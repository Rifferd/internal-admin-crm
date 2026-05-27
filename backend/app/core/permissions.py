from collections.abc import Iterable

from fastapi import HTTPException, status

from app.common.enums import UserRole
from app.models.user import User


def ensure_user_has_role(user: User, allowed_roles: Iterable[UserRole]) -> None:
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )