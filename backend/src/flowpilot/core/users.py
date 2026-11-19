"""Panel kullanıcıları: şifre özeti (argon2) ve demo hesapları."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flowpilot.core import audit
from flowpilot.core.models import User, UserRole

_hasher = PasswordHasher()

# Kurgusal Atlas Endüstri çalışanları (.example alan adı, RFC 2606).
DEMO_DOMAIN = "atlas-endustri.example"
DEMO_USERS: tuple[tuple[str, str, UserRole, tuple[str, ...]], ...] = (
    ("yonetici", "Demo Yönetici", UserRole.ADMIN, ()),
    ("satinalma", "Satın Alma Uzmanı", UserRole.DEPARTMENT_USER, ("procurement",)),
    ("finans", "Finans Uzmanı", UserRole.DEPARTMENT_USER, ("finance",)),
    ("satis", "Satış Temsilcisi", UserRole.DEPARTMENT_USER, ("sales_orders",)),
    ("lojistik", "Lojistik Planlamacı", UserRole.DEPARTMENT_USER, ("logistics",)),
)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def authenticate(session: Session, email: str, password: str) -> User | None:
    user = session.scalars(
        select(User).where(func.lower(User.email) == email.strip().lower())
    ).first()
    if user is None:
        # Zamanlama farkıyla kullanıcı varlığı sızmasın diye yine de bir doğrulama yapılır.
        _hasher.hash(password)
        return None
    try:
        _hasher.verify(user.password_hash, password)
    except (VerificationError, InvalidHashError):
        return None
    return user


def ensure_demo_users(session: Session, password: str) -> list[str]:
    """Demo hesaplarını oluşturur; var olanların şifresini ve yetkisini günceller."""
    emails = []
    for local, name, role, departments in DEMO_USERS:
        email = f"{local}@{DEMO_DOMAIN}"
        user = session.scalars(select(User).where(User.email == email)).first()
        if user is None:
            user = User(email=email, name=name, role=role, departments=list(departments))
            session.add(user)
        user.name, user.role, user.departments = name, role, list(departments)
        user.password_hash = hash_password(password)
        emails.append(email)
    session.flush()
    audit.record(
        session,
        actor=audit.SYSTEM,
        action="users.demo_ensured",
        entity_type="user",
        entity_id="demo",
        data={"emails": emails},
    )
    return emails
