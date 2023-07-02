import time
import os
import base64
from datetime import timedelta
from openpvz.models import User, UserRole
from openpvz.consts import TELEGRAM_BOT_NAME
from typing import Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


SECRET_KEY = os.getenv('AUTH_SECRET_KEY')
if SECRET_KEY is None:
    raise Exception("Please specify 'AUTH_SECRET_KEY'")


_short_roles = {
    UserRole.SUPEROWNER: "SO",
    UserRole.OWNER: "OW",
    UserRole.MANAGER: "MA",
    UserRole.OPERATOR: "OP",
}


def create_link(owner: User, role: UserRole):
    short_role = _short_roles.get(role)
    token = encrypt_user_info(short_role, owner.id, int(time.time() + timedelta(days=1).total_seconds()))
    return f"https://t.me/{TELEGRAM_BOT_NAME}?start={token}"


def parse_token(token: str) -> Tuple[UserRole, int, bool]:
    short_role, owner_id, expired = decrypt_user_info(token)
    short_roles_values = list(_short_roles.values())
    if not short_role in short_roles_values:
        return None, None, None
    role = list(_short_roles.keys())[short_roles_values.index(short_role)]
    return role, owner_id, expired


# Almost all credits for these two functions go to ChatGPT
def encrypt_user_info(role: str, owner_id: int, expire_time: int) -> str:
    salt = os.urandom(2)
    key = _get_key(salt)
    plaintext = f"{role}:{owner_id}:{expire_time}"
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
    encrypted_string = base64.urlsafe_b64encode(iv + salt + ciphertext).decode()
    return encrypted_string


def decrypt_user_info(encrypted_string: str) -> Tuple[str, int, bool]:
    encrypted_data = base64.urlsafe_b64decode(encrypted_string.encode())
    iv = encrypted_data[:16]
    salt = encrypted_data[16:18]
    ciphertext = encrypted_data[18:]
    key = _get_key(salt)
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    role, owner_id, expire_time = plaintext.decode().split(':')
    current_time = int(time.time())
    return role, int(owner_id), int(expire_time) < current_time


def _get_key(salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(bytes(SECRET_KEY, 'utf-8'))[:16]
    return key
