from datetime import UTC, datetime

from sqlalchemy import delete, false, func, or_, select
from sqlalchemy.exc import IntegrityError

from app.core.errors import ApiError
from app.core.models import Driver, Vehicle
from app.modules.auth.service import aware
from app.modules.drivers.models import DriverAssignment, DriverCategory
from app.modules.drivers.schemas import CATEGORIES, CATEGORIES_VERSION


def profile_query(source):
    counts = (
        select(DriverAssignment.driver_id, func.count().label("vehicle_count"))
        .join(Vehicle, Vehicle.id == DriverAssignment.vehicle_id)
        .where(DriverAssignment.active.is_(True), Vehicle.source_account == source)
        .group_by(DriverAssignment.driver_id)
        .subquery()
    )
    return (
        select(Driver, func.coalesce(counts.c.vehicle_count, 0).label("vehicle_count"))
        .outerjoin(counts, counts.c.driver_id == Driver.id)
        .where(Driver.source_account == source)
    )


def current_relations(source):
    return (
        select(DriverAssignment.driver_id)
        .join(Vehicle, Vehicle.id == DriverAssignment.vehicle_id)
        .where(DriverAssignment.active.is_(True), Vehicle.source_account == source)
    )


def profile_filters(
    query, source, q, active, assigned, category, vehicle_id=None, missing_categories=None
):
    if active is not None:
        query = query.where(Driver.active.is_(active))
    relation = current_relations(source).where(DriverAssignment.driver_id == Driver.id).exists()
    if assigned is not None:
        query = query.where(relation if assigned else ~relation)
    if vehicle_id is not None:
        query = query.where(
            current_relations(source)
            .where(
                DriverAssignment.driver_id == Driver.id, DriverAssignment.vehicle_id == vehicle_id
            )
            .exists()
        )
    if category:
        if category not in CATEGORIES:
            raise ApiError(422, "VALIDATION_ERROR", "Nieznana kategoria")
        query = query.where(
            select(DriverCategory.driver_id)
            .where(DriverCategory.driver_id == Driver.id, DriverCategory.category == category)
            .exists()
        )
    if missing_categories is not None:
        known = (
            select(DriverCategory.driver_id).where(DriverCategory.driver_id == Driver.id).exists()
        )
        query = query.where(~known if missing_categories else known)
    needle = q.strip().casefold()
    if "\x00" in needle:
        return query.where(false())
    if needle:
        vehicle_match = (
            current_relations(source)
            .where(
                DriverAssignment.driver_id == Driver.id,
                or_(
                    *(
                        column.contains(needle, autoescape=True)
                        for column in (
                            Vehicle.search_name,
                            Vehicle.search_number,
                            Vehicle.search_license_plate,
                        )
                    )
                ),
            )
            .exists()
        )
        query = query.where(
            or_(Driver.search_text.contains(needle, autoescape=True), vehicle_match)
        )
    return query


def profiles(session, rows, source):
    identities = [driver.id for driver, _ in rows]
    categories = {identity: [] for identity in identities}
    first = {}
    if identities:
        for driver_id, category in session.execute(
            select(DriverCategory.driver_id, DriverCategory.category).where(
                DriverCategory.driver_id.in_(identities)
            )
        ):
            categories[driver_id].append(category)
        ranked = (
            select(
                DriverAssignment.driver_id,
                Vehicle.id.label("vehicle_id"),
                Vehicle.name,
                Vehicle.active,
                func.row_number()
                .over(partition_by=DriverAssignment.driver_id, order_by=(Vehicle.name, Vehicle.id))
                .label("rank"),
            )
            .join(Vehicle, Vehicle.id == DriverAssignment.vehicle_id)
            .where(
                DriverAssignment.driver_id.in_(identities),
                DriverAssignment.active.is_(True),
                Vehicle.source_account == source,
            )
            .subquery()
        )
        for row in session.execute(select(ranked).where(ranked.c.rank == 1)).mappings():
            first[row["driver_id"]] = {
                "id": str(row["vehicle_id"]),
                "name": row["name"],
                "active": row["active"],
            }
    return [
        {
            "id": str(driver.id),
            "display_name": driver.display_name,
            "first_name": driver.first_name,
            "last_name": driver.last_name,
            "identifier": driver.identifier,
            "phone": driver.phone,
            "email": driver.email,
            "active": driver.active,
            "version": driver.version,
            "needs_completion": not all((driver.first_name, driver.last_name, driver.identifier)),
            "categories": [item for item in CATEGORIES if item in categories[driver.id]],
            "categories_version": CATEGORIES_VERSION,
            "vehicles_total": count,
            "first_vehicle": first.get(driver.id),
            "compatibility": {"status": "not_evaluated", "reason": "SCRUM-70"},
        }
        for driver, count in rows
    ]


def find_driver(session, source, identity, *, version=None):
    statement = select(Driver).where(Driver.id == identity, Driver.source_account == source)
    if version is not None:
        statement = statement.with_for_update()
    driver = session.scalar(statement)
    if not driver:
        raise ApiError(404, "NOT_FOUND", "Kierowca nie istnieje")
    if version is not None and driver.version != version:
        raise ApiError(409, "CONFLICT", "Dane kierowcy zmieniły się. Pobierz bieżącą wersję")
    return driver


def replace_categories(session, driver, categories):
    session.execute(delete(DriverCategory).where(DriverCategory.driver_id == driver.id))
    session.add_all(
        DriverCategory(driver_id=driver.id, category=category) for category in categories
    )


def commit_profile(session):
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ApiError(409, "CONFLICT", "Identyfikator kierowcy jest już używany") from None


def project_vehicle_drivers(session, vehicle_ids, source):
    # Sorted vehicle locks serialize concurrent changes from different drivers.
    vehicles = session.scalars(
        select(Vehicle)
        .where(Vehicle.id.in_(vehicle_ids), Vehicle.source_account == source)
        .order_by(Vehicle.id)
        .with_for_update()
    ).all()
    for vehicle in vehicles:
        identities = session.scalars(
            select(Driver.id)
            .join(DriverAssignment, DriverAssignment.driver_id == Driver.id)
            .where(
                DriverAssignment.vehicle_id == vehicle.id,
                DriverAssignment.active.is_(True),
                Driver.active.is_(True),
                or_(Driver.source_account == source, Driver.source_account.is_(None)),
            )
            .order_by(Driver.id)
        ).all()
        vehicle.driver_id = identities[0] if len(identities) == 1 else None


def close_driver_assignments(session, driver, source):
    rows = session.scalars(
        select(DriverAssignment).where(
            DriverAssignment.driver_id == driver.id, DriverAssignment.active.is_(True)
        )
    ).all()
    now = datetime.now(UTC)
    for assignment in rows:
        assignment.active = False
        assignment.ended_at = now
    session.flush()
    project_vehicle_drivers(session, [row.vehicle_id for row in rows], source)


def assignment_payload(assignment, vehicle):
    return {
        "id": str(assignment.id),
        "driver_id": str(assignment.driver_id),
        "vehicle": {
            "id": str(vehicle.id),
            "name": vehicle.name,
            "license_plate": vehicle.license_plate,
            "active": vehicle.active,
        },
        "active": assignment.active,
        "started_at": aware(assignment.started_at).isoformat() if assignment.started_at else None,
        "ended_at": aware(assignment.ended_at).isoformat() if assignment.ended_at else None,
        "recorded_at": aware(assignment.recorded_at).isoformat(),
        "start_known": assignment.started_at is not None,
    }
