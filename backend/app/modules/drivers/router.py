from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import ApiError
from app.core.models import Driver, Vehicle
from app.modules.auth.models import User
from app.modules.auth.service import check_origin, current_user, editor
from app.modules.drivers.compatibility import (
    MATRIX_VERSION,
    PO_CONFIRMED,
    REASON_CODES,
    evaluate_driver_vehicle,
    summarize_driver_compatibility,
)
from app.modules.drivers.models import DriverAssignment, DriverCategory
from app.modules.drivers.schemas import (
    CATEGORIES,
    CATEGORIES_VERSION,
    AssignmentBody,
    CloseAssignmentBody,
    DriverFields,
    DriverPatch,
    DriverSearch,
)
from app.modules.drivers.service import (
    assignment_payload,
    close_driver_assignments,
    commit_profile,
    find_driver,
    profile_filters,
    profile_query,
    profiles,
    project_vehicle_drivers,
    replace_categories,
)
from app.modules.fleet.sync import account_key

router = APIRouter(prefix="/api/v1/drivers", tags=["drivers"])
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(current_user)]
EditorDep = Annotated[User, Depends(editor)]
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
Sort = Literal["name_asc", "name_desc", "vehicles_asc", "vehicles_desc", "custom"]


def source_for(request):
    return account_key(request.app.state.settings.webfleet_account)


@router.get("/categories")
def categories(_: UserDep):
    return {
        "version": CATEGORIES_VERSION,
        "items": [{"id": item, "label": item} for item in CATEGORIES],
        "compatibility": "evaluated",
        "matrix_version": MATRIX_VERSION,
        "po_confirmed": PO_CONFIRMED,
    }


def _matching_compatibility_driver_ids(session: Session, query, source: str, mode: str):
    scope = query.subquery()
    driver_ids = list(session.scalars(select(scope.c.id)).all())
    if not driver_ids:
        return []
    cats_by_driver: dict[UUID, list[str]] = {did: [] for did in driver_ids}
    for did, cat in session.execute(
        select(DriverCategory.driver_id, DriverCategory.category).where(
            DriverCategory.driver_id.in_(driver_ids)
        )
    ):
        cats_by_driver[did].append(cat)
    vehicles_by_driver: dict[UUID, list[Vehicle]] = {did: [] for did in driver_ids}
    for did, veh in session.execute(
        select(DriverAssignment.driver_id, Vehicle)
        .join(Vehicle, Vehicle.id == DriverAssignment.vehicle_id)
        .where(
            DriverAssignment.driver_id.in_(driver_ids),
            DriverAssignment.active.is_(True),
            Vehicle.source_account == source,
        )
    ):
        vehicles_by_driver[did].append(veh)
    matched: list[UUID] = []
    for did in driver_ids:
        active_vehs = vehicles_by_driver[did]
        if mode == "attention":
            if active_vehs and summarize_driver_compatibility(cats_by_driver[did], active_vehs)[
                "status"
            ] in ("incompatible", "unverified"):
                matched.append(did)
        else:
            if summarize_driver_compatibility(cats_by_driver[did], active_vehs)["status"] == mode:
                matched.append(did)
    return matched


@router.get("/summary")
def summary(
    request: Request,
    session: SessionDep,
    _: UserDep,
    active: bool | None = None,
    assigned: bool | None = None,
    category: str | None = None,
    vehicle_id: UUID | None = None,
    missing_categories: bool | None = None,
    compatibility_status: Literal["compatible", "incompatible", "unverified", "attention"]
    | None = None,
):
    require_post_for_search(request)
    source = source_for(request)
    query = profile_filters(
        profile_query(source),
        source,
        "",
        active,
        assigned,
        category,
        vehicle_id,
        missing_categories,
    )
    if compatibility_status is not None:
        allowed_ids = _matching_compatibility_driver_ids(
            session, query, source, compatibility_status
        )
        query = (
            query.where(Driver.id.in_(allowed_ids))
            if allowed_ids
            else query.where(Driver.id.is_(None))
        )
    return driver_summary(session, query, source)


def driver_summary(session, query, source: str):
    scope = query.subquery()
    active_count = func.count().filter(scope.c.active.is_(True))
    without = func.count().filter(scope.c.active.is_(True), scope.c.vehicle_count == 0)
    no_categories = func.count().filter(
        scope.c.active.is_(True),
        ~select(DriverCategory.driver_id).where(DriverCategory.driver_id == scope.c.id).exists(),
    )
    total, active_total, unassigned, missing = session.execute(
        select(func.count(), active_count, without, no_categories).select_from(scope)
    ).one()

    assignment_rows = session.execute(
        select(DriverAssignment.driver_id, Vehicle)
        .join(Vehicle, Vehicle.id == DriverAssignment.vehicle_id)
        .where(
            DriverAssignment.driver_id.in_(select(scope.c.id)),
            DriverAssignment.active.is_(True),
            Vehicle.source_account == source,
        )
    ).all()
    assigned_driver_ids = list({did for did, _ in assignment_rows})
    cats_map: dict[UUID, list[str]] = {did: [] for did in assigned_driver_ids}
    if assigned_driver_ids:
        for did, cat in session.execute(
            select(DriverCategory.driver_id, DriverCategory.category).where(
                DriverCategory.driver_id.in_(assigned_driver_ids)
            )
        ):
            cats_map[did].append(cat)

    incompatible_rel = 0
    unverified_rel = 0
    by_reason = {code: 0 for code in REASON_CODES}
    for did, veh in assignment_rows:
        ev = evaluate_driver_vehicle(cats_map.get(did, ()), veh)
        if ev["status"] == "incompatible":
            incompatible_rel += 1
        elif ev["status"] == "unverified":
            unverified_rel += 1
        for r in ev["reasons"]:
            if r in by_reason:
                by_reason[r] += 1

    return {
        "total": total,
        "active": active_total,
        "active_unassigned": unassigned,
        "active_missing_categories": missing,
        "assignments_to_check": {
            "status": "evaluated",
            "total": incompatible_rel + unverified_rel,
            "incompatible": incompatible_rel,
            "unverified": unverified_rel,
            "by_reason": by_reason,
            "matrix_version": MATRIX_VERSION,
            "po_confirmed": PO_CONFIRMED,
        },
        "scope": "current_source_and_filters",
    }


@router.get("")
def drivers(
    request: Request,
    session: SessionDep,
    _: UserDep,
    active: bool | None = None,
    assigned: bool | None = None,
    category: str | None = None,
    sort: Sort = "name_asc",
    page: Page = 1,
    page_size: PageSize = 25,
    vehicle_id: UUID | None = None,
    missing_categories: bool | None = None,
    compatibility_status: Literal["compatible", "incompatible", "unverified", "attention"]
    | None = None,
    custom_order: Annotated[list[UUID] | None, Query(max_length=2000)] = None,
):
    require_post_for_search(request)
    source = source_for(request)
    query = profile_filters(
        profile_query(source),
        source,
        "",
        active,
        assigned,
        category,
        vehicle_id,
        missing_categories,
    )
    if compatibility_status is not None:
        allowed_ids = _matching_compatibility_driver_ids(
            session, query, source, compatibility_status
        )
        query = (
            query.where(Driver.id.in_(allowed_ids))
            if allowed_ids
            else query.where(Driver.id.is_(None))
        )
    return driver_page(session, source, query, sort, page, page_size, custom_order)


def driver_page(session, source, query, sort, page, page_size, custom_order):
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    name = func.lower(func.coalesce(Driver.last_name, Driver.display_name))
    first = func.lower(func.coalesce(Driver.first_name, ""))
    order = (
        (name, first, Driver.id)
        if sort == "name_asc"
        else (name.desc(), first.desc(), Driver.id)
        if sort == "name_desc"
        else (
            query.selected_columns.vehicle_count.asc()
            if sort == "vehicles_asc"
            else query.selected_columns.vehicle_count.desc(),
            name,
            first,
            Driver.id,
        )
    )
    if sort == "custom":
        order = (name, first, Driver.id)
        if custom_order:
            order = (
                case(
                    {identity: index for index, identity in enumerate(custom_order)},
                    value=Driver.id,
                    else_=len(custom_order),
                ),
                *order,
            )
    rows = session.execute(
        query.order_by(*order).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": profiles(session, rows, source),
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def require_post_for_search(request):
    if "q" in request.query_params:
        raise ApiError(422, "QUERY_BODY_REQUIRED", "Użyj formularza wyszukiwania kierowców")


@router.post("/search", dependencies=[Depends(check_origin)])
def search_drivers(body: DriverSearch, request: Request, session: SessionDep, _: UserDep):
    source = source_for(request)
    query = profile_filters(
        profile_query(source),
        source,
        body.q,
        body.active,
        body.assigned,
        body.category,
        body.vehicle_id,
        body.missing_categories,
    )
    if body.compatibility_status is not None:
        allowed_ids = _matching_compatibility_driver_ids(
            session, query, source, body.compatibility_status
        )
        query = (
            query.where(Driver.id.in_(allowed_ids))
            if allowed_ids
            else query.where(Driver.id.is_(None))
        )
    result = driver_page(
        session, source, query, body.sort, body.page, body.page_size, body.custom_order
    )
    result["summary"] = driver_summary(session, query, source)
    return result


def response_profile(session, source, identity):
    rows = session.execute(profile_query(source).where(Driver.id == identity)).all()
    return profiles(session, rows, source)[0]


@router.get("/{driver_id}")
def driver(driver_id: UUID, request: Request, session: SessionDep, _: UserDep):
    source = source_for(request)
    find_driver(session, source, driver_id)
    return response_profile(session, source, driver_id)


@router.post("", status_code=201)
def create_driver(body: DriverFields, request: Request, session: SessionDep, _: EditorDep):
    source = source_for(request)
    fields = body.model_dump(exclude={"categories"})
    driver = Driver(
        **fields, source_account=source, display_name=f"{body.first_name} {body.last_name}"
    )
    session.add(driver)
    try:
        session.flush()
        replace_categories(session, driver, body.categories)
        commit_profile(session)
    except IntegrityError:
        session.rollback()
        raise ApiError(409, "CONFLICT", "Identyfikator kierowcy jest już używany") from None
    return response_profile(session, source, driver.id)


@router.patch("/{driver_id}")
def patch_driver(
    driver_id: UUID, body: DriverPatch, request: Request, session: SessionDep, _: EditorDep
):
    source = source_for(request)
    if body.active is False:
        # Canonical lock order: Vehicle (by id) -> Driver -> DriverAssignment.
        candidate_vehicle_ids = sorted(
            set(
                session.scalars(
                    select(DriverAssignment.vehicle_id)
                    .join(Vehicle, Vehicle.id == DriverAssignment.vehicle_id)
                    .where(
                        DriverAssignment.driver_id == driver_id,
                        DriverAssignment.active.is_(True),
                        Vehicle.source_account == source,
                    )
                ).all()
            )
        )
        if candidate_vehicle_ids:
            session.scalars(
                select(Vehicle)
                .where(Vehicle.id.in_(candidate_vehicle_ids), Vehicle.source_account == source)
                .order_by(Vehicle.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            ).all()
    driver = find_driver(session, source, driver_id, version=body.version)
    changes = body.model_dump(exclude_unset=True, exclude={"categories", "version"})
    for field, value in changes.items():
        setattr(driver, field, value)
    if driver.first_name and driver.last_name:
        driver.display_name = f"{driver.first_name} {driver.last_name}"
    driver.version += 1
    try:
        if "categories" in body.model_fields_set:
            replace_categories(session, driver, body.categories)
        if body.active is False:
            close_driver_assignments(session, driver, source)
        commit_profile(session)
    except IntegrityError:
        session.rollback()
        raise ApiError(409, "CONFLICT", "Identyfikator kierowcy jest już używany") from None
    return response_profile(session, source, driver.id)


@router.get("/{driver_id}/assignments")
def assignments(
    driver_id: UUID,
    request: Request,
    session: SessionDep,
    _: UserDep,
    active: bool | None = None,
    page: Page = 1,
    page_size: PageSize = 25,
):
    source = source_for(request)
    find_driver(session, source, driver_id)
    query = (
        select(DriverAssignment, Vehicle)
        .join(Vehicle, Vehicle.id == DriverAssignment.vehicle_id)
        .where(DriverAssignment.driver_id == driver_id, Vehicle.source_account == source)
    )
    if active is not None:
        query = query.where(DriverAssignment.active.is_(active))
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.execute(
        query.order_by(DriverAssignment.recorded_at.desc(), DriverAssignment.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    driver_cats = list(
        session.scalars(
            select(DriverCategory.category).where(DriverCategory.driver_id == driver_id)
        ).all()
    )
    return {
        "items": [assignment_payload(*row, driver_categories=driver_cats) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{driver_id}/assignments", status_code=201)
def assign(
    driver_id: UUID, body: AssignmentBody, request: Request, session: SessionDep, _: EditorDep
):
    source = source_for(request)
    # Canonical lock order: Vehicle -> Driver -> DriverAssignment.
    vehicle = session.scalar(
        select(Vehicle)
        .where(Vehicle.id == body.vehicle_id, Vehicle.source_account == source)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    driver = find_driver(session, source, driver_id, version=body.version)
    if not driver.active or not vehicle or not vehicle.active:
        raise ApiError(404, "NOT_FOUND", "Kierowca lub pojazd są niedostępne")
    if vehicle.archived:
        raise ApiError(
            409,
            "VEHICLE_ARCHIVED",
            "Nie można przypisać kierowcy do zarchiwizowanego pojazdu",
        )
    driver_cats = list(
        session.scalars(
            select(DriverCategory.category).where(DriverCategory.driver_id == driver_id)
        ).all()
    )
    comp = evaluate_driver_vehicle(driver_cats, vehicle)
    if comp["status"] == "incompatible":
        raise ApiError(409, "LICENSE_INCOMPATIBLE", comp["message"])
    if session.scalar(
        select(DriverAssignment.id)
        .where(
            DriverAssignment.driver_id == driver_id,
            DriverAssignment.vehicle_id == vehicle.id,
            DriverAssignment.active.is_(True),
        )
        .order_by(DriverAssignment.id)
        .with_for_update()
    ):
        raise ApiError(409, "CONFLICT", "To przypisanie jest już aktywne")
    assignment = DriverAssignment(
        driver_id=driver_id, vehicle_id=vehicle.id, started_at=datetime.now(UTC)
    )
    session.add(assignment)
    driver.version += 1
    try:
        session.flush()
        project_vehicle_drivers(session, [vehicle.id], source)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ApiError(
            409, "CONFLICT", "Przypisanie zmieniło się. Pobierz bieżącą wersję"
        ) from None
    return {
        "assignment": assignment_payload(assignment, vehicle, driver_categories=driver_cats),
        "driver_version": driver.version,
    }


@router.patch("/{driver_id}/assignments/{assignment_id}/close")
def close(
    driver_id: UUID,
    assignment_id: UUID,
    body: CloseAssignmentBody,
    request: Request,
    session: SessionDep,
    _: EditorDep,
):
    source = source_for(request)
    # Canonical lock order: Vehicle -> Driver -> DriverAssignment.
    vehicle_id = session.scalar(
        select(DriverAssignment.vehicle_id)
        .join(Vehicle, Vehicle.id == DriverAssignment.vehicle_id)
        .where(
            DriverAssignment.id == assignment_id,
            DriverAssignment.driver_id == driver_id,
            Vehicle.source_account == source,
        )
    )
    vehicle = (
        session.scalar(
            select(Vehicle)
            .where(Vehicle.id == vehicle_id, Vehicle.source_account == source)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if vehicle_id is not None
        else None
    )
    driver = find_driver(session, source, driver_id, version=body.version)
    if vehicle is None:
        raise ApiError(404, "NOT_FOUND", "Przypisanie nie istnieje")
    assignment = session.scalar(
        select(DriverAssignment)
        .where(
            DriverAssignment.id == assignment_id,
            DriverAssignment.driver_id == driver.id,
            DriverAssignment.vehicle_id == vehicle.id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not assignment:
        raise ApiError(404, "NOT_FOUND", "Przypisanie nie istnieje")
    if not assignment.active:
        raise ApiError(409, "CONFLICT", "Przypisanie jest już zakończone")
    assignment.active = False
    assignment.ended_at = datetime.now(UTC)
    driver.version += 1
    session.flush()
    project_vehicle_drivers(session, [vehicle.id], source)
    session.commit()
    driver_cats = list(
        session.scalars(
            select(DriverCategory.category).where(DriverCategory.driver_id == driver_id)
        ).all()
    )
    return {
        "assignment": assignment_payload(assignment, vehicle, driver_categories=driver_cats),
        "driver_version": driver.version,
    }
