from __future__ import annotations

from . import store
from .schemas import UserRole
from .settings import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_NAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_NAME,
    DEFAULT_USER_PASSWORD,
)

LEGACY_ADMIN_EMAIL = "admin@gaia.com"
LEGACY_USER_EMAIL = "usuario@gaia.com"


def _migrate_legacy_email(old_email: str, new_email: str) -> None:
    legacy_user = store.get_user_by_email(old_email)
    if legacy_user is None or store.get_user_by_email(new_email) is not None:
        return

    store.update_user_email(legacy_user["id"], new_email)


def seed_default_users() -> None:
    _migrate_legacy_email(LEGACY_ADMIN_EMAIL, DEFAULT_ADMIN_EMAIL)
    _migrate_legacy_email(LEGACY_USER_EMAIL, DEFAULT_USER_EMAIL)

    if store.get_user_by_email(DEFAULT_ADMIN_EMAIL) is None:
        store.create_user(
            full_name=DEFAULT_ADMIN_NAME,
            email=DEFAULT_ADMIN_EMAIL,
            password=DEFAULT_ADMIN_PASSWORD,
            role=UserRole.admin,
        )

    if store.get_user_by_email(DEFAULT_USER_EMAIL) is None:
        store.create_user(
            full_name=DEFAULT_USER_NAME,
            email=DEFAULT_USER_EMAIL,
            password=DEFAULT_USER_PASSWORD,
            role=UserRole.user,
        )
