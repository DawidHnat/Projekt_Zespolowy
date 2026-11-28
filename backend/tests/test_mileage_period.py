from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.models import Driver, Vehicle
from app.modules.auth.models import User
from app.modules.fleet.sync import account_key
from app.modules.trips.models import Trip, TripAnnotation, TripHistoryDay
from app.modules.trips.service import polish_day


def test_period_uses_polish_start_day_and_sums_all_rows_before_pagination(logged_in):
    app, client = logged_in
    day = date(2026, 10, 24)
    start, midnight = polish_day(day)
    following_day = day + timedelta(days=1)
    source = account_key(app.state.settings.webfleet_account)
    with app.state.sessions() as session:
        author = session.scalar(select(User))
        car = Vehicle(source_account=source, external_uid="period-test", name="Synthetic vehicle")
        other = Vehicle(source_account="other-source", external_uid="other", name="Other vehicle")
        driver = Driver(source_account=source, display_name="Synthetic driver")
        session.add_all([car, other, driver])
        session.flush()
        crossing = Trip(
            vehicle_id=car.id,
            external_uid="crossing",
            start_at=midnight - timedelta(minutes=10),
            end_at=midnight + timedelta(minutes=10),
            distance_km=Decimal("12.345"),
            driver_id=driver.id,
        )
        session.add_all(
            [
                crossing,
                Trip(
                    vehicle_id=car.id,
                    external_uid="low",
                    start_at=start,
                    distance_km=Decimal("0.006"),
                ),
                Trip(
                    vehicle_id=car.id, external_uid="unknown", start_at=start + timedelta(hours=3)
                ),
                TripHistoryDay(vehicle_id=car.id, report_day=day, imported_at=midnight),
            ]
        )
        session.flush()
        session.add(
            TripAnnotation(
                trip_id=crossing.id,
                purpose="Serwis",
                description="Próba",
                version=2,
                updated_by=author.id,
                updated_at=midnight,
            )
        )
        car_id, other_id, crossing_id = str(car.id), str(other.id), str(crossing.id)
        session.commit()

    path = "/api/v1/trips/mileage"
    params = {"vehicle_id": car_id, "from_day": day.isoformat(), "through": day.isoformat()}
    result = client.get(path, params={**params, "page_size": 1})
    assert result.status_code == 200
    data = result.json()
    assert data["total"] == 3 and len(data["items"]) == 1
    assert data["items"][0]["id"] == crossing_id
    # PO decision 27.11 (SCRUM-62): known-km sum; documented km is a separate extension.
    assert data["summary"] == {"known_km": 12.351, "missing_purpose": 2, "missing_distance": 1}
    assert data["coverage"]["covered_days"] == [day.isoformat()]
    assert (
        client.get(path, params={**params, "page_size": 1, "page": 2}).json()["summary"]
        == data["summary"]
    )

    second = client.get(
        path,
        params={
            **params,
            "from_day": following_day.isoformat(),
            "through": following_day.isoformat(),
        },
    ).json()
    assert second["items"] == [] and second["summary"]["known_km"] is None
    assert second["coverage"]["state"] == "unavailable"
    assert client.get(path, params={**params, "vehicle_id": other_id}).status_code == 404
    assert (
        client.get(path, params={**params, "from_day": following_day.isoformat()}).status_code
        == 422
    )
