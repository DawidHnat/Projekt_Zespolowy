"""Existing role policy shared by provisioning, login and request authorization."""

ROLES = ("admin", "editor", "viewer")
EDIT_ROLES = frozenset(("admin", "editor"))


def can_authenticate(role: str) -> bool:
    return role in ROLES


def can_edit(role: str) -> bool:
    return role in EDIT_ROLES
