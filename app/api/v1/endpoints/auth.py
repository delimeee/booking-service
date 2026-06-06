from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import Token, UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)) -> User:
    svc = UserService(db)
    if svc.get_by_username(data.username):
        raise ConflictException(f"Username '{data.username}' is already taken")
    return svc.create(data)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = UserService(db).authenticate(form_data.username, form_data.password)
    if not user:
        raise UnauthorizedException("Incorrect username or password")
    token = create_access_token(subject=user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
