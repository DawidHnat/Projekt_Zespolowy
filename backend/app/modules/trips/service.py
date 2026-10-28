from app.modules.auth.service import aware


def annotation_payload(annotation, author):
    if annotation is None:
        return {
            "purpose": None,
            "description": None,
            "version": 1,
            "updated_at": None,
            "updated_by": None,
        }
    return {
        "purpose": annotation.purpose,
        "description": annotation.description,
        "version": annotation.version,
        "updated_at": aware(annotation.updated_at).isoformat(),
        "updated_by": {"id": str(author.id), "display_name": author.display_name},
    }


def trip_payload(trip, annotation, author):
    start = aware(trip.start_at)
    end = aware(trip.end_at) if trip.end_at else None
    return {
        "id": str(trip.id),
        "vehicle_id": str(trip.vehicle_id),
        "start_at": start.isoformat(),
        "end_at": end.isoformat() if end else None,
        "distance_km": float(trip.distance_km) if trip.distance_km is not None else None,
        "duration_seconds": int((end - start).total_seconds()) if end else None,
        "annotation": annotation_payload(annotation, author),
        "geometry": None,
    }
