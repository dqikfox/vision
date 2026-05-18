"""Admin authentication and authorization system for Vision.

Provides JWT-based authentication, role-based access control,
and audit logging for administrative operations.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Configuration
ADMIN_SECRET = os.environ.get("VISION_ADMIN_SECRET", secrets.token_hex(32))
TOKEN_EXPIRY = int(os.environ.get("VISION_ADMIN_TOKEN_EXPIRY", "3600"))
RATE_LIMIT = int(os.environ.get("VISION_ADMIN_RATE_LIMIT", "5"))


class Role(Enum):
    """User roles for access control."""
    USER = "user"
    TEACHER = "teacher"
    ADMIN = "admin"


@dataclass
class User:
    """Admin user model."""
    id: str
    username: str
    password_hash: str
    role: Role = Role.USER
    created_at: float = field(default_factory=time.time)
    last_login: float | None = None
    is_active: bool = True


@dataclass
class Token:
    """JWT token model."""
    token: str
    user_id: str
    role: Role
    expires_at: float
    created_at: float = field(default_factory=time.time)


class AuditLog:
    """Audit logging for admin actions."""

    def __init__(self, log_dir: str = ".logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "admin_audit.log")

    def log(
        self,
        action: str,
        user_id: str,
        details: dict[str, Any] | None = None,
        ip: str | None = None,
    ) -> None:
        """Log an admin action."""
        entry = {
            "timestamp": time.time(),
            "action": action,
            "user_id": user_id,
            "ip": ip,
            "details": details or {},
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


class AuthManager:
    """Main authentication manager."""

    def __init__(self):
        self.users: dict[str, User] = {}
        self.tokens: dict[str, Token] = {}
        self.failed_attempts: dict[str, list[float]] = {}
        self.audit = AuditLog()
        self._load_default_admin()

    def _load_default_admin(self) -> None:
        """Create default admin if no users exist."""
        if not self.users:
            self.create_user(
                username="admin",
                password=os.environ.get("VISION_ADMIN_DEFAULT_PASSWORD", "changeme"),
                role=Role.ADMIN,
            )

    def _hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2."""
        salt = secrets.token_hex(16)
        hash_value = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100000,
        ).hex()
        return f"{salt}${hash_value}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, stored_hash = password_hash.split("$")
            computed = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt.encode(),
                100000,
            ).hex()
            return hmac.compare_digest(computed, stored_hash)
        except ValueError:
            return False

    def _generate_token(self, user: User) -> Token:
        """Generate a JWT token for a user."""
        header = json.dumps({"alg": "HS256", "typ": "JWT"})
        now = time.time()
        payload = json.dumps({
            "sub": user.id,
            "role": user.role.value,
            "iat": now,
            "exp": now + TOKEN_EXPIRY,
        })

        header_b64 = self._base64url_encode(header)
        payload_b64 = self._base64url_encode(payload)

        signature = hmac.new(
            ADMIN_SECRET.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256,
        ).digest()
        signature_b64 = self._base64url_encode_bytes(signature)

        token_str = f"{header_b64}.{payload_b64}.{signature_b64}"

        token = Token(
            token=token_str,
            user_id=user.id,
            role=user.role,
            expires_at=now + TOKEN_EXPIRY,
        )
        self.tokens[token_str] = token
        return token

    def _base64url_encode(self, data: str) -> str:
        """Base64URL encode a string."""
        import base64
        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

    def _base64url_encode_bytes(self, data: bytes) -> str:
        """Base64URL encode bytes."""
        import base64
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def _base64url_decode(self, data: str) -> str:
        """Base64URL decode to string."""
        import base64
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data).decode()

    def _check_rate_limit(self, identifier: str) -> bool:
        """Check if rate limit exceeded."""
        now = time.time()
        window = 60  # 1 minute window

        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []

        # Remove old attempts
        self.failed_attempts[identifier] = [
            t for t in self.failed_attempts[identifier]
            if now - t < window
        ]

        return len(self.failed_attempts[identifier]) < RATE_LIMIT

    def create_user(
        self,
        username: str,
        password: str,
        role: Role = Role.USER,
    ) -> User:
        """Create a new user."""
        user_id = secrets.token_hex(16)
        user = User(
            id=user_id,
            username=username,
            password_hash=self._hash_password(password),
            role=role,
        )
        self.users[user_id] = user
        self.audit.log("user_created", user_id, {"username": username, "role": role.value})
        return user

    def authenticate(self, username: str, password: str, ip: str | None = None) -> Token | None:
        """Authenticate a user and return a token."""
        if not self._check_rate_limit(username):
            self.audit.log("rate_limit_exceeded", "unknown", {"username": username}, ip)
            return None

        user = next(
            (u for u in self.users.values() if u.username == username and u.is_active),
            None,
        )

        if not user:
            self.failed_attempts.setdefault(username, []).append(time.time())
            return None

        if not self._verify_password(password, user.password_hash):
            self.failed_attempts.setdefault(username, []).append(time.time())
            self.audit.log("login_failed", user.id, {"username": username}, ip)
            return None

        user.last_login = time.time()
        self.audit.log("login_success", user.id, {"username": username}, ip)
        return self._generate_token(user)

    def validate_token(self, token_str: str) -> Token | None:
        """Validate a token and return it if valid."""
        token = self.tokens.get(token_str)
        if not token:
            return None
        if token.expires_at < time.time():
            del self.tokens[token_str]
            return None
        return token

    def logout(self, token_str: str) -> bool:
        """Invalidate a token."""
        if token_str in self.tokens:
            token = self.tokens[token_str]
            del self.tokens[token_str]
            self.audit.log("logout", token.user_id)
            return True
        return False

    def require_role(self, token_str: str, min_role: Role) -> User | None:
        """Check if token has at least the required role."""
        token = self.validate_token(token_str)
        if not token:
            return None

        user = self.users.get(token.user_id)
        if not user or not user.is_active:
            return None

        # Role hierarchy: ADMIN > TEACHER > USER
        role_values = {Role.USER: 1, Role.TEACHER: 2, Role.ADMIN: 3}
        if role_values[token.role] < role_values[min_role]:
            return None

        return user

    def list_users(self, requester_token: str) -> list[dict] | None:
        """List all users (admin only)."""
        if not self.require_role(requester_token, Role.ADMIN):
            return None

        return [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role.value,
                "created_at": u.created_at,
                "last_login": u.last_login,
                "is_active": u.is_active,
            }
            for u in self.users.values()
        ]

    def delete_user(self, requester_token: str, user_id: str) -> bool:
        """Delete a user (admin only)."""
        requester = self.require_role(requester_token, Role.ADMIN)
        if not requester:
            return False

        if user_id == requester.id:
            return False  # Can't delete self

        if user_id in self.users:
            user = self.users[user_id]
            del self.users[user_id]
            # Invalidate all tokens for this user
            self.tokens = {
                k: v for k, v in self.tokens.items()
                if v.user_id != user_id
            }
            self.audit.log("user_deleted", requester.id, {"deleted_user": user_id})
            return True
        return False


# Singleton instance
auth_manager = AuthManager()


if __name__ == "__main__":
    # Quick test
    print("Admin module loaded")
    print("Default admin: username='admin', password from env")
    print(f"Token expiry: {TOKEN_EXPIRY}s")
