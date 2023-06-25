from jose import jwt
from datetime import datetime, timedelta
import os
from openpvz.models import User, UserRole
from openpvz.consts import TELEGRAM_BOT_NAME
from typing import Dict, Any, Tuple


SECRET_KEY = os.getenv('AUTH_SECRET_KEY')
if SECRET_KEY is None:
    raise Exception("Please specify 'AUTH_SECRET_KEY'")


ALGORITHM = "HS256"


def create_link(owner: User, role: UserRole):
    token = _create_role_jwt(str(owner.id), role, timedelta(days=1))
    return f"https://t.me/{TELEGRAM_BOT_NAME}?start={token}"


def parse_token(token: str) -> Tuple[UserRole, int, bool]:
    payload = _decode_jwt(token)
    return payload["role"], int(payload["iss"]), datetime.utcnow() > payload["exp"]


def _create_role_jwt(issuer: str, role: str, expires_delta: timedelta) -> str:
    now = datetime.utcnow()
    expire = now + expires_delta
    to_encode = {
        "iss": issuer,
        "role": role,
        "exp": expire,
        "iat": now,
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def _decode_jwt(token: str) -> Dict[str, Any]:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
