"""NEVER MERGE: intentionally invalid synthetic consumer responses for SCRUM-108 proof."""

import copy

import pytest

from test_contracts import OPERATIONS, validator


@pytest.mark.parametrize(
    "change", ["renamed_required_field", "changed_field_type", "removed_required_field"]
)
def test_unmerged_breaking_response_is_rejected_by_required_ci(change):
    response = copy.deepcopy(OPERATIONS["GET", "/fleet/vehicles"]["response_example"])
    if change == "renamed_required_field":
        response["count"] = response.pop("total")
    elif change == "changed_field_type":
        response["total"] = "1"
    else:
        del response["total"]
    # Deliberately no assertRaises: these invalid responses MUST make this isolated PR red.
    validator({"$ref": "#/$defs/VehicleList"}).validate(response)
