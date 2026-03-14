"""Encryption utilities for sensitive configuration data."""

import os
import json
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from typing import Any, Dict
from loguru import logger


class ConfigEncryption:
    """Handle encryption/decryption of metadata JSON with master password."""

    def __init__(self):
        self.salt_file = os.path.expanduser("~/.llm_agent/salt")
        self._ensure_salt_file()

    def _ensure_salt_file(self) -> None:
        """Create salt file if it doesn't exist."""
        os.makedirs(os.path.dirname(self.salt_file), exist_ok=True)
        if not os.path.exists(self.salt_file):
            salt = os.urandom(16)
            with open(self.salt_file, "wb") as f:
                f.write(salt)
            os.chmod(self.salt_file, 0o600)
            logger.info(f"Created salt file at {self.salt_file}")

    def _get_key_from_password(self, password: str) -> bytes:
        """Derive encryption key from master password using PBKDF2."""
        with open(self.salt_file, "rb") as f:
            salt = f.read()

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        return b64encode(key)

    def encrypt_metadata(self, metadata: Dict[str, Any], password: str) -> str:
        """Encrypt metadata JSON with master password."""
        key = self._get_key_from_password(password)
        cipher = Fernet(key)
        json_str = json.dumps(metadata)
        encrypted = cipher.encrypt(json_str.encode())
        return b64encode(encrypted).decode()

    def decrypt_metadata(self, encrypted_data: str, password: str) -> Dict[str, Any]:
        """Decrypt metadata JSON with master password."""
        key = self._get_key_from_password(password)
        cipher = Fernet(key)
        try:
            encrypted_bytes = b64decode(encrypted_data.encode())
            decrypted = cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Invalid password or corrupted data")

    @staticmethod
    def prompt_master_password() -> str:
        """Prompt user for master password via CLI."""
        import getpass
        return getpass.getpass("Enter master password: ")
