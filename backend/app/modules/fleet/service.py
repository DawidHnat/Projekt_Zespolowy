import re
from datetime import UTC, datetime, timedelta
from math import isfinite

from sqlalchemy import case, false, func, or_, select

from app.core.errors import ApiError
from app.core.models import Driver, Measurement, SyncState, Vehicle
from app.modules.auth.models import User
from app.modules.auth.service import aware
from app.modules.drivers.compatibility import vehicle_license_requirement
from app.modules.drivers.models import DriverAssignment


def vehicle_archive_authors(session, vehicles):
    author_ids = {vehicle.archived_by for vehicle in vehicles if vehicle.archived_by is not None}
    if not author_ids:
        return {}
    return {
        user.id: user for user in session.scalars(select(User).where(User.id.in_(author_ids))).all()
    }


def fleet_driver_summaries(session, vehicle_ids, source):
    if not vehicle_ids:
        return {}
    ranked = (
        select(
            DriverAssignment.vehicle_id,
            Driver.id,
            Driver.display_name,
            func.count().over(partition_by=DriverAssignment.vehicle_id).label("total"),
            func.row_number()
            .over(
                partition_by=DriverAssignment.vehicle_id, order_by=(Driver.display_name, Driver.id)
            )
            .label("rank"),
        )
        .join(Driver, Driver.id == DriverAssignment.driver_id)
        .where(
            DriverAssignment.vehicle_id.in_(vehicle_ids),
            DriverAssignment.active.is_(True),
            Driver.active.is_(True),
            or_(Driver.source_account == source, Driver.source_account.is_(None)),
        )
        .subquery()
    )
    result = {}
    for row in session.execute(
        select(ranked).where(ranked.c.rank <= 3).order_by(ranked.c.vehicle_id, ranked.c.rank)
    ).mappings():
        summary = result.setdefault(row["vehicle_id"], {"total": row["total"], "preview": []})
        summary["preview"].append({"id": str(row["id"]), "display_name": row["display_name"]})
    return result


def with_driver_summary(payload, summary):
    if summary is None:
        summary = {
            "total": int(payload["driver"] is not None),
            "preview": [payload["driver"]] if payload["driver"] else [],
        }
    return {
        **payload,
        "driver_count": summary["total"],
        "driver_preview": summary["preview"],
        "driver": summary["preview"][0] if summary["total"] == 1 else None,
    }


def timestamp(value):
    return aware(value).isoformat() if value else None


def normalize_identity_token(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[\s\-]+", "", value).casefold()


def find_identity_conflicts(
    session,
    source: str,
    *,
    license_plate: str | None,
    vin: str | None,
    exclude_id=None,
):
    plate_token = normalize_identity_token(license_plate)
    vin_token = normalize_identity_token(vin)
    if not plate_token and not vin_token:
        return []
    query = select(Vehicle).where(Vehicle.source_account == source)
    if exclude_id is not None:
        query = query.where(Vehicle.id != exclude_id)
    conflicts = []
    for candidate in session.scalars(query).all():
        same_plate = bool(
            plate_token and normalize_identity_token(candidate.license_plate) == plate_token
        )
        same_vin = bool(vin_token and normalize_identity_token(candidate.vin) == vin_token)
        if same_plate or same_vin:
            conflicts.append((candidate, same_plate, same_vin))
    return conflicts


def source_link_candidates(session, vehicle: Vehicle):
    if not vehicle.is_manual:
        return []
    manual_vin = normalize_identity_token(vehicle.vin)
    matches = []
    for candidate, same_plate, same_vin in find_identity_conflicts(
        session,
        vehicle.source_account,
        license_plate=vehicle.license_plate,
        vin=vehicle.vin,
        exclude_id=vehicle.id,
    ):
        if not candidate.is_manual and candidate.active and not candidate.archived:
            candidate_vin = normalize_identity_token(candidate.vin)
            if manual_vin and candidate_vin and manual_vin != candidate_vin:
                continue
            matches.append(
                {
                    "id": str(candidate.id),
                    "name": candidate.name,
                    "number": candidate.number,
                    "license_plate": candidate.license_plate,
                    "vin": candidate.vin,
                    "matched_by": [
                        field
                        for field, matched in (("license_plate", same_plate), ("vin", same_vin))
                        if matched
                    ],
                }
            )
    return matches


def source_payload(session, source):
    state = session.get(SyncState, source)
    if state and state.last_success_at:
        return {
            "status": "degraded" if state.error_code else "ok",
            "last_success_at": timestamp(state.last_success_at),
            "error_code": state.error_code,
        }
    has_manual = session.scalar(
        select(Vehicle.id)
        .where(Vehicle.source_account == source, Vehicle.is_manual.is_(True))
        .limit(1)
    )
    if has_manual is not None:
        return {
            "status": "degraded",
            "last_success_at": None,
            "error_code": "MANUAL_ONLY",
        }
    raise ApiError(503, "SOURCE_UNAVAILABLE", "Oczekiwanie na dane WEBFLEET")


def serialize_vehicle(
    vehicle,
    measurement,
    driver,
    now,
    stale_seconds,
    source_degraded=False,
    *,
    archive_author=None,
    link_candidates=None,
):
    time = aware(measurement.position_at) if measurement and measurement.position_at else None
    age = (now - time).total_seconds() if time else None
    stale = source_degraded or age is None or age > stale_seconds or age < -300
    status = "unknown"
    if measurement and not vehicle.is_manual:
        if stale:
            status = "offline"
        elif measurement.standing_still is not None:
            status = "stopped" if measurement.standing_still else "moving"
    located = bool(
        not vehicle.is_manual
        and measurement
        and measurement.gps_quality == "A"
        and time
        and age >= -300
        and measurement.latitude is not None
        and measurement.longitude is not None
    )
    archive_info = None
    if vehicle.archived:
        archive_info = {
            "archived_at": timestamp(vehicle.archived_at),
            "archived_by": (
                {"id": str(archive_author.id), "display_name": archive_author.display_name}
                if archive_author
                else None
            ),
            "reason": vehicle.archived_reason,
        }
    telemetry_odometer = (
        float(measurement.odometer_km)
        if not vehicle.is_manual and measurement and measurement.odometer_km is not None
        else None
    )
    manual_odometer = (
        float(vehicle.manual_odometer_km) if vehicle.manual_odometer_km is not None else None
    )
    payload = {
        "id": str(vehicle.id),
        "origin": "manual" if vehicle.is_manual else "webfleet",
        "name": vehicle.name,
        "card_version": vehicle.card_version,
        "photo_version": vehicle.photo_version,
        "number": None if vehicle.is_manual else vehicle.number,
        "license_plate": vehicle.license_plate,
        "vehicle_type": vehicle.vehicle_type,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "vin": vehicle.vin,
        "fuel_type": vehicle.fuel_type,
        "leasing_company": vehicle.leasing_company,
        "leasing_contract_no": vehicle.leasing_contract_no,
        "leasing_end_on": vehicle.leasing_end_on.isoformat() if vehicle.leasing_end_on else None,
        "inspection_due_on": (
            vehicle.inspection_due_on.isoformat() if vehicle.inspection_due_on else None
        ),
        "insurance_due_on": (
            vehicle.insurance_due_on.isoformat() if vehicle.insurance_due_on else None
        ),
        "manual_odometer_km": manual_odometer,
        "manual_odometer_date": (
            vehicle.manual_odometer_date.isoformat() if vehicle.manual_odometer_date else None
        ),
        "gross_weight_kg": vehicle.gross_weight_kg,
        "passenger_seats": vehicle.passenger_seats,
        "tows_heavy_trailer": vehicle.tows_heavy_trailer,
        "required_category_override": vehicle.required_category_override,
        "ownership_category": vehicle.ownership_category,
        "leasing_buyout_on": vehicle.leasing_buyout_on.isoformat()
        if vehicle.leasing_buyout_on
        else None,
        "first_registration_on": vehicle.first_registration_on.isoformat()
        if vehicle.first_registration_on
        else None,
        "first_registration_pl_on": vehicle.first_registration_pl_on.isoformat()
        if vehicle.first_registration_pl_on
        else None,
        "engine_capacity_cc": vehicle.engine_capacity_cc,
        "power_kw": vehicle.power_kw,
        "curb_weight_kg": vehicle.curb_weight_kg,
        "payload_kg": vehicle.payload_kg,
        "axles": vehicle.axles,
        "license_requirement": vehicle_license_requirement(vehicle),
        "archived": vehicle.archived,
        "archive": archive_info,
        "status": status,
        "driver": {"id": str(driver.id), "display_name": driver.display_name} if driver else None,
        "latitude": measurement.latitude if located else None,
        "longitude": measurement.longitude if located else None,
        "position_at": None if vehicle.is_manual else timestamp(time),
        "received_at": (
            timestamp(measurement.received_at) if not vehicle.is_manual and measurement else None
        ),
        "is_stale": stale,
        "position_address": (
            measurement.position_address if not vehicle.is_manual and measurement else None
        ),
        "odometer_km": telemetry_odometer if telemetry_odometer is not None else manual_odometer,
        "speed_kmh": float(measurement.speed_kmh)
        if located
        and not stale
        and age >= 0
        and measurement.speed_kmh is not None
        and isfinite(measurement.speed_kmh)
        and 0 <= measurement.speed_kmh <= 300
        else None,
        "ignition_on": measurement.ignition_on if not vehicle.is_manual and measurement else None,
        "standing_still": (
            measurement.standing_still if not vehicle.is_manual and measurement else None
        ),
    }
    if link_candidates is not None:
        payload["link_candidates"] = link_candidates
    return payload


def fleet_order(session, sort, status_expression):
    # Python casefold + bytewise collation preserves the ordering used by main.
    collation = "C" if session.bind.dialect.name == "postgresql" else "BINARY"
    name = Vehicle.search_name.collate(collation)
    if sort == "name-desc":
        return [name.desc(), Vehicle.id]
    if sort == "status":
        rank = case(
            (status_expression == "moving", 0),
            (status_expression == "stopped", 1),
            (status_expression == "offline", 2),
            else_=3,
        )
        return [rank, name, Vehicle.id]
    if sort in ("odometer-asc", "odometer-desc"):
        effective_mileage = func.coalesce(Measurement.odometer_km, Vehicle.manual_odometer_km)
        mileage = effective_mileage.desc() if sort == "odometer-desc" else effective_mileage.asc()
        return [mileage.nulls_last(), name, Vehicle.id]
    return [name, Vehicle.id]


def fleet_status(now, stale_seconds, source_degraded=False):
    """Use the same time boundaries as the detail serializer, including future GPS."""
    stale = or_(
        source_degraded,
        Measurement.position_at.is_(None),
        Measurement.position_at < now - timedelta(seconds=stale_seconds),
        Measurement.position_at > now + timedelta(seconds=300),
    )
    return case(
        (Measurement.vehicle_id.is_(None), "unknown"),
        (stale, "offline"),
        (Measurement.standing_still.is_(True), "stopped"),
        (Measurement.standing_still.is_(False), "moving"),
        else_="unknown",
    )


def fleet_filters(source, q, status, status_expression, archive="active"):
    conditions = [Vehicle.source_account == source]
    if archive == "archived":
        conditions.append(Vehicle.archived.is_(True))
    elif archive == "all":
        conditions.append(or_(Vehicle.active.is_(True), Vehicle.archived.is_(True)))
    else:
        conditions.extend((Vehicle.active.is_(True), Vehicle.archived.is_(False)))
    needle = q.strip().casefold()
    if "\x00" in needle:
        # PostgreSQL text cannot contain NUL; avoid sending an invalid SQL parameter.
        conditions.append(false())
    elif needle:
        # Escape LIKE metacharacters: user input is a literal substring, not a pattern.
        conditions.append(
            or_(
                *(
                    field.contains(needle, autoescape=True)
                    for field in (
                        Vehicle.search_name,
                        Vehicle.search_number,
                        Vehicle.search_license_plate,
                        Vehicle.search_make,
                        Vehicle.search_model,
                        Vehicle.search_vin,
                    )
                )
            )
        )
    if status:
        conditions.append(status_expression == status)
    return conditions


def fleet_count(session, conditions):
    return session.scalar(
        select(func.count())
        .select_from(Vehicle)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .where(*conditions)
    )


def fleet_page(
    session,
    source,
    stale_seconds,
    q,
    status,
    page,
    page_size,
    sort="name-asc",
    *,
    archive="active",
    source_degraded=False,
):
    now = datetime.now(UTC)
    conditions = fleet_filters(
        source,
        q,
        status,
        fleet_status(now, stale_seconds, source_degraded),
        archive=archive,
    )
    total = fleet_count(session, conditions)
    rows = session.execute(
        select(Vehicle, Measurement, Driver)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .outerjoin(Driver, Driver.id == Vehicle.driver_id)
        .where(*conditions)
        .order_by(*fleet_order(session, sort, fleet_status(now, stale_seconds, source_degraded)))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    drivers = fleet_driver_summaries(session, [row[0].id for row in rows], source)
    authors = vehicle_archive_authors(session, [row[0] for row in rows])
    return [
        with_driver_summary(
            serialize_vehicle(
                *row,
                now,
                stale_seconds,
                source_degraded,
                archive_author=authors.get(row[0].archived_by),
            ),
            drivers.get(row[0].id),
        )
        for row in rows
    ], total


def fleet_markers(
    session, source, stale_seconds, q, status, *, archive="active", source_degraded=False
):
    now = datetime.now(UTC)
    status_expression = fleet_status(now, stale_seconds, source_degraded)
    conditions = fleet_filters(source, q, status, status_expression, archive=archive)
    total = fleet_count(session, conditions)
    # Coordinates of stale positions remain useful; only invalid/missing/future GPS is hidden.
    rows = session.execute(
        select(
            Vehicle.id,
            Vehicle.name,
            Measurement.longitude,
            Measurement.latitude,
            Measurement.position_at,
            status_expression.label("status"),
        )
        .join(Measurement, Measurement.vehicle_id == Vehicle.id)
        .where(
            *conditions,
            Vehicle.is_manual.is_(False),
            Measurement.gps_quality == "A",
            Measurement.position_at <= now + timedelta(seconds=300),
            Measurement.latitude.is_not(None),
            Measurement.longitude.is_not(None),
        )
        .order_by(Vehicle.name, Vehicle.id)
    ).all()
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row.longitude, row.latitude]},
            "properties": {
                "id": str(row.id),
                "name": row.name,
                "status": row.status,
                "is_stale": source_degraded
                or (now - aware(row.position_at)).total_seconds() > stale_seconds,
                "position_at": timestamp(row.position_at),
            },
        }
        for row in rows
    ]
    return features, total


def fleet_summary(session, source, stale_seconds, *, source_degraded=False):
    now = datetime.now(UTC)
    status_expression = fleet_status(now, stale_seconds, source_degraded)
    rows = session.execute(
        select(status_expression, func.count())
        .select_from(Vehicle)
        .outerjoin(Measurement, Measurement.vehicle_id == Vehicle.id)
        .where(
            Vehicle.source_account == source,
            Vehicle.active.is_(True),
            Vehicle.archived.is_(False),
        )
        .group_by(status_expression)
    ).all()
    counts = dict.fromkeys(("moving", "stopped", "offline", "unknown"), 0)
    counts.update(rows)
    return {"total": sum(counts.values()), **counts}
