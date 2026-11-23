"""Existing role policy shared by provisioning, login and request authorization."""

from typing import Literal

type Role = Literal["admin", "editor", "viewer"]

ROLES = ("admin", "editor", "viewer")
EDIT_ROLES = frozenset(("admin", "editor"))


def can_authenticate(role: str) -> bool:
    return role in ROLES


def can_edit(role: str) -> bool:
    return role in EDIT_ROLES


def can_manage_accounts(role: str) -> bool:
    return role == "admin"
