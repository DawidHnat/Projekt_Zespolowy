from app.modules.auth.service import aware
from app.modules.drivers.compatibility import HISTORICAL_ASSIGNMENT_WARNING


def annotation_payload(annotation, author, trip_driver=None):
    if annotation is None:
        return {
            "purpose": None,
            "description": None,
            "driver_id": None,
            "driver": None,
            "version": 1,
            "updated_at": None,
            "updated_by": None,
        }
    driver_info = None
    if trip_driver is not None:
        driver_info = {
            "id": str(trip_driver.id),
            "display_name": trip_driver.display_name,
            "historical_warning": HISTORICAL_ASSIGNMENT_WARNING,
        }
    return {
        "purpose": annotation.purpose,
        "description": annotation.description,
        "driver_id": str(annotation.driver_id) if annotation.driver_id else None,
        "driver": driver_info,
        "version": annotation.version,
        "updated_at": aware(annotation.updated_at).isoformat(),
        "updated_by": {"id": str(author.id), "display_name": author.display_name},
    }


def trip_payload(trip, annotation, author, trip_driver=None):
    start = aware(trip.start_at)
    end = aware(trip.end_at) if trip.end_at else None
    return {
        "id": str(trip.id),
        "vehicle_id": str(trip.vehicle_id),
        "start_at": start.isoformat(),
        "end_at": end.isoformat() if end else None,
        "distance_km": float(trip.distance_km) if trip.distance_km is not None else None,
        "duration_seconds": int((end - start).total_seconds()) if end else None,
        "annotation": annotation_payload(annotation, author, trip_driver),
        "geometry": None,
    }
