from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, sessionmaker

from flowpilot.bootstrap import get_registry
from flowpilot.config import get_settings
from flowpilot.core.db import get_engine
from flowpilot.core.models import User, UserRole
from flowpilot.core.registry import DepartmentRegistry
from flowpilot.core.storage import AttachmentStorage, LocalStorage

SESSION_USER_KEY = "user_id"


def get_db() -> Iterator[Session]:
    """İstek başına bir veritabanı işlemi: hata yoksa commit, varsa rollback."""
    factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    with factory() as session, session.begin():
        yield session


def get_storage() -> AttachmentStorage:
    return LocalStorage(get_settings().storage_dir)


def registry() -> DepartmentRegistry:
    return get_registry()


Db = Annotated[Session, Depends(get_db)]
Storage = Annotated[AttachmentStorage, Depends(get_storage)]
Registry = Annotated[DepartmentRegistry, Depends(registry)]


def current_user(request: Request, db: Db) -> User:
    raw = request.session.get(SESSION_USER_KEY)
    user = None
    if raw:
        try:
            user = db.get(User, UUID(raw))
        except ValueError:
            user = None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Giriş yapmanız gerekiyor.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def admin_user(user: CurrentUser) -> User:
    if user.role is not UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bu işlem için yönetici yetkisi gerekiyor.")
    return user


AdminUser = Annotated[User, Depends(admin_user)]
