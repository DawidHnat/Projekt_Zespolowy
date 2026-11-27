"""Polish driving license compatibility evaluation (SCRUM-70).

Evaluates driver entitlement against vehicle DMC (`gross_weight_kg`), passenger capacity,
heavy-trailer flag, and explicit category overrides. Never uses alphabetical ordering
of category strings and never infers heavy-truck (`C`) requirement from the label
`"ciężarowy"` alone without DMC. Missing data always produces `"unverified"`, never
`"compatible"`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.core.models import Vehicle
from app.modules.drivers.schemas import CATEGORIES

MATRIX_VERSION = "pl-ustawa-o-kierujacych-v1-pending-po"
PO_CONFIRMED = False

HISTORICAL_ASSIGNMENT_WARNING = (
    "Aktualne prawo jazdy i kartoteka pojazdu nie potwierdzają uprawnień "
    "w dacie historycznego przypisania."
)

# Statutory entitlement expansion based on Art. 6 of the Polish Act on Vehicle Drivers
# (Ustawa z dnia 5 stycznia 2011 r. o kierujących pojazdami — pending PO confirmation).
IMPLIED_CATEGORIES: dict[str, frozenset[str]] = {
    "AM": frozenset({"AM"}),
    "A1": frozenset({"A1", "AM"}),
    "A2": frozenset({"A2", "A1", "AM"}),
    "A": frozenset({"A", "A2", "A1", "AM"}),
    "B1": frozenset({"B1", "AM"}),
    "B": frozenset({"B", "B1", "AM"}),
    "B+E": frozenset({"B+E", "B", "B1", "AM", "T"}),
    "C1": frozenset({"C1"}),
    "C1+E": frozenset({"C1+E", "C1", "B+E", "T"}),
    "C": frozenset({"C", "C1"}),
    "C+E": frozenset({"C+E", "C", "C1+E", "C1", "B+E", "T"}),
    "D1": frozenset({"D1"}),
    "D1+E": frozenset({"D1+E", "D1", "B+E", "T"}),
    "D": frozenset({"D", "D1"}),
    "D+E": frozenset({"D+E", "D", "D1+E", "D1", "B+E", "T"}),
    "T": frozenset({"T", "AM"}),
}

TRAILER_UPGRADE: dict[str, str] = {
    "B": "B+E",
    "C1": "C1+E",
    "C": "C+E",
    "D1": "D1+E",
    "D": "D+E",
}

REASON_CODES = (
    "category_mismatch",
    "missing_driver_categories",
    "missing_vehicle_dmc",
    "missing_passenger_seats",
    "missing_vehicle_requirements",
)

REASON_MESSAGES_PL: dict[str, str] = {
    "category_mismatch": "Wpisane kategorie kierowcy nie obejmują wymaganej kategorii pojazdu.",
    "missing_driver_categories": "Kierowca nie ma wpisanych kategorii prawa jazdy.",
    "missing_vehicle_dmc": "Brak DMC (kg) w kartotece pojazdu — nie zgadujemy z samej nazwy typu.",
    "missing_passenger_seats": "Brak liczby miejsc pasażerskich autobusu w kartotece pojazdu.",
    "missing_vehicle_requirements": (
        "Pojazd wymaga jawnego wskazania wymaganej kategorii uprawnień."
    ),
    "no_active_assignments": "Kierowca nie ma obecnie przypisanego pojazdu.",
    "matched": "Wpisane kategorie kierowcy są zgodne z wymaganiami przypisanych pojazdów.",
}

_TRACTOR_TYPES = frozenset(
    {"ciagnik", "ciagnik rolniczy", "ciągnik", "ciągnik rolniczy", "tractor"}
)
_MOTORCYCLE_TYPES = frozenset({"motocykl", "motorcycle", "motorower", "skuter", "moped"})
_BUS_TYPES = frozenset({"autobus", "bus pasazerski", "bus pasażerski", "coach", "minibus"})
_QUAD_TYPES = frozenset({"czterokolowiec", "czterokołowiec", "quad"})


def expand_driver_categories(held: Iterable[str]) -> set[str]:
    expanded: set[str] = set()
    held_set = {item for item in held if item in IMPLIED_CATEGORIES}
    for cat in held_set:
        expanded.update(IMPLIED_CATEGORIES[cat])
    # Art. 6 ust. 2 pkt 3: C+E implies D+E when the driver also holds D (and similarly D1).
    if "C+E" in held_set and "D" in held_set:
        expanded.update({"D+E", "D1+E"})
    elif "C+E" in held_set and "D1" in held_set:
        expanded.add("D1+E")
    return expanded


def accepted_categories_for(required_category: str) -> list[str]:
    return [
        candidate
        for candidate in CATEGORIES
        if required_category in IMPLIED_CATEGORIES.get(candidate, frozenset())
    ]


def _with_trailer(base_category: str, tows_heavy_trailer: bool) -> str:
    if tows_heavy_trailer and base_category in TRAILER_UPGRADE:
        return TRAILER_UPGRADE[base_category]
    return base_category


def vehicle_license_requirement(vehicle: Vehicle) -> dict[str, Any]:
    override = getattr(vehicle, "required_category_override", None)
    tows = bool(getattr(vehicle, "tows_heavy_trailer", False))
    dmc = getattr(vehicle, "gross_weight_kg", None)
    seats = getattr(vehicle, "passenger_seats", None)
    raw_type = (getattr(vehicle, "vehicle_type", None) or "").strip().casefold()

    if override in IMPLIED_CATEGORIES:
        req = _with_trailer(override, tows)
        return {
            "status": "determined",
            "required_category": req,
            "accepted_categories": accepted_categories_for(req),
            "reason": None,
            "source": "override",
        }

    if raw_type in _TRACTOR_TYPES:
        return {
            "status": "determined",
            "required_category": "T",
            "accepted_categories": accepted_categories_for("T"),
            "reason": None,
            "source": "vehicle_type",
        }

    if raw_type in _MOTORCYCLE_TYPES or raw_type in _QUAD_TYPES:
        # Power/weight ratio is not in basic card fields -> require explicit override.
        return {
            "status": "unverified",
            "required_category": None,
            "accepted_categories": [],
            "reason": "missing_vehicle_requirements",
            "source": "missing",
        }

    if raw_type in _BUS_TYPES or (seats is not None and seats > 8):
        if seats is None or seats <= 8:
            return {
                "status": "unverified",
                "required_category": None,
                "accepted_categories": [],
                "reason": "missing_passenger_seats",
                "source": "missing",
            }
        base = "D1" if seats <= 16 else "D"
        req = _with_trailer(base, tows)
        return {
            "status": "determined",
            "required_category": req,
            "accepted_categories": accepted_categories_for(req),
            "reason": None,
            "source": "passenger_seats",
        }

    # Standard road vehicles (cars, vans, N1/N2/N3 "ciężarowy"): DMC is strictly required!
    if dmc is None:
        return {
            "status": "unverified",
            "required_category": None,
            "accepted_categories": [],
            "reason": "missing_vehicle_dmc",
            "source": "missing",
        }

    if dmc <= 3500:
        base = "B"
    elif dmc <= 7500:
        base = "C1"
    else:
        base = "C"
    req = _with_trailer(base, tows)
    return {
        "status": "determined",
        "required_category": req,
        "accepted_categories": accepted_categories_for(req),
        "reason": None,
        "source": "dmc",
    }


def evaluate_driver_vehicle(
    driver_categories: Iterable[str],
    vehicle: Vehicle,
    *,
    historical: bool = False,
) -> dict[str, Any]:
    held_ordered = [cat for cat in CATEGORIES if cat in set(driver_categories)]
    req = vehicle_license_requirement(vehicle)
    reasons: list[str] = []

    if not held_ordered:
        reasons.append("missing_driver_categories")
    if req["status"] != "determined" and req["reason"]:
        reasons.append(req["reason"])

    if reasons:
        primary = reasons[0]
        return {
            "status": "unverified",
            "reason": primary,
            "reasons": reasons,
            "required_category": req["required_category"],
            "accepted_categories": req["accepted_categories"],
            "message": REASON_MESSAGES_PL[primary],
            "historical_warning": HISTORICAL_ASSIGNMENT_WARNING if historical else None,
        }

    required_cat = req["required_category"]
    entitled = expand_driver_categories(held_ordered)
    if required_cat in entitled:
        return {
            "status": "compatible",
            "reason": "matched",
            "reasons": [],
            "required_category": required_cat,
            "accepted_categories": req["accepted_categories"],
            "message": f"Zgodne uprawnienia (wymagana kat. {required_cat}).",
            "historical_warning": HISTORICAL_ASSIGNMENT_WARNING if historical else None,
        }

    return {
        "status": "incompatible",
        "reason": "category_mismatch",
        "reasons": ["category_mismatch"],
        "required_category": required_cat,
        "accepted_categories": req["accepted_categories"],
        "message": (
            f"Niezgodne uprawnienia: pojazd wymaga kat. {required_cat}, "
            f"kierowca posiada {', '.join(held_ordered)}."
        ),
        "historical_warning": HISTORICAL_ASSIGNMENT_WARNING if historical else None,
    }


def summarize_driver_compatibility(
    driver_categories: list[str], active_vehicles: list[Vehicle]
) -> dict[str, Any]:
    if not active_vehicles:
        reason = "missing_driver_categories" if not driver_categories else "no_active_assignments"
        return {
            "status": "unverified",
            "reason": reason,
            "reasons": [reason],
            "incompatible_count": 0,
            "unverified_count": 0,
            "message": REASON_MESSAGES_PL[reason],
        }

    incompatible_count = 0
    unverified_count = 0
    collected_reasons: list[str] = []
    for vehicle in active_vehicles:
        ev = evaluate_driver_vehicle(driver_categories, vehicle)
        if ev["status"] == "incompatible":
            incompatible_count += 1
        elif ev["status"] == "unverified":
            unverified_count += 1
        for r in ev["reasons"]:
            if r not in collected_reasons:
                collected_reasons.append(r)

    if incompatible_count > 0:
        return {
            "status": "incompatible",
            "reason": "category_mismatch",
            "reasons": collected_reasons or ["category_mismatch"],
            "incompatible_count": incompatible_count,
            "unverified_count": unverified_count,
            "message": REASON_MESSAGES_PL["category_mismatch"],
        }
    if unverified_count > 0:
        primary = collected_reasons[0] if collected_reasons else "missing_vehicle_dmc"
        return {
            "status": "unverified",
            "reason": primary,
            "reasons": collected_reasons,
            "incompatible_count": 0,
            "unverified_count": unverified_count,
            "message": REASON_MESSAGES_PL.get(primary, "Wymaga weryfikacji danych."),
        }
    return {
        "status": "compatible",
        "reason": "matched",
        "reasons": [],
        "incompatible_count": 0,
        "unverified_count": 0,
        "message": REASON_MESSAGES_PL["matched"],
    }
