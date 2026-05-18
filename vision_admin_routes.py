"""FastAPI routes for admin mode.

Provides REST API endpoints for admin authentication and management.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from vision_admin import Role, auth_manager

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_at: float
    role: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: float
    last_login: float | None
    is_active: bool


class ConfigUpdate(BaseModel):
    key: str
    value: Any


def get_auth_header(request: Request) -> str | None:
    """Extract bearer token from Authorization header."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: Request, credentials: LoginRequest):
    """Authenticate and get JWT token."""
    client_ip = request.client.host if request.client else None
    token = auth_manager.authenticate(
        credentials.username,
        credentials.password,
        ip=client_ip,
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return LoginResponse(
        token=token.token,
        expires_at=token.expires_at,
        role=token.role.value,
    )


@router.post("/logout")
async def admin_logout(request: Request):
    """Invalidate current token."""
    token = get_auth_header(request)
    if token:
        auth_manager.logout(token)
    return {"status": "logged_out"}


@router.get("/users", response_model=list[UserResponse])
async def list_users(request: Request):
    """List all users (admin only)."""
    token = get_auth_header(request)
    users = auth_manager.list_users(token)
    if users is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return [UserResponse(**u) for u in users]


@router.post("/users", response_model=UserResponse)
async def create_user(request: Request, user_data: UserCreate):
    """Create new user (admin only)."""
    token = get_auth_header(request)
    if not auth_manager.require_role(token, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    try:
        role = Role(user_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {user_data.role}",
        )

    user = auth_manager.create_user(
        username=user_data.username,
        password=user_data.password,
        role=role,
    )
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role.value,
        created_at=user.created_at,
        last_login=user.last_login,
        is_active=user.is_active,
    )


@router.delete("/users/{user_id}")
async def delete_user(request: Request, user_id: str):
    """Delete user (admin only)."""
    token = get_auth_header(request)
    if not auth_manager.delete_user(token, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required or cannot delete self",
        )
    return {"status": "deleted", "user_id": user_id}


@router.get("/logs")
async def get_logs(request: Request, limit: int = 100):
    """View system logs (admin/teacher)."""
    token = get_auth_header(request)
    user = auth_manager.require_role(token, Role.TEACHER)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin access required",
        )

    # Read last N lines from audit log
    log_file = auth_manager.audit.log_file
    try:
        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
            entries = [json.loads(line) for line in lines[-limit:]]
            return {"logs": entries}
    except FileNotFoundError:
        return {"logs": []}


@router.get("/stats")
async def get_stats(request: Request):
    """System statistics (admin/teacher)."""
    token = get_auth_header(request)
    user = auth_manager.require_role(token, Role.TEACHER)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin access required",
        )

    return {
        "total_users": len(auth_manager.users),
        "active_tokens": len(auth_manager.tokens),
        "audit_entries": _count_audit_entries(),
    }


def _count_audit_entries() -> int:
    """Count total audit log entries."""
    try:
        with open(auth_manager.audit.log_file, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


@router.post("/config")
async def update_config(request: Request, config: ConfigUpdate):
    """Update system config (admin only)."""
    token = get_auth_header(request)
    user = auth_manager.require_role(token, Role.ADMIN)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Log config change
    auth_manager.audit.log(
        "config_updated",
        user.id,
        {"key": config.key, "value": str(config.value)[:100]},
    )

    return {"status": "updated", "key": config.key}


# Import json for logs endpoint
import json
