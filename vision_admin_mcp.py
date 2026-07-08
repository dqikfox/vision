"""MCP tools for admin operations.

Exposes admin functionality via Model Context Protocol.
"""

from __future__ import annotations

import json
from typing import Any

from vision_admin import Role, auth_manager


class AdminMCPTools:
    """MCP tools for admin mode."""

    def __init__(self):
        self.auth_manager = auth_manager

    def require_admin(self, token: str) -> bool:
        """Check if token has admin role."""
        user = self.auth_manager.require_role(token, Role.ADMIN)
        return user is not None

    def require_teacher(self, token: str) -> bool:
        """Check if token has teacher or admin role."""
        user = self.auth_manager.require_role(token, Role.TEACHER)
        return user is not None

    def vision_admin_login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate and get JWT token.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            Token response or error
        """
        token = self.auth_manager.authenticate(username, password)
        if not token:
            return {
                "success": False,
                "error": "Invalid credentials",
            }
        return {
            "success": True,
            "token": token.token,
            "expires_at": token.expires_at,
            "role": token.role.value,
        }

    def vision_admin_logout(self, token: str) -> dict[str, Any]:
        """Invalidate token.
        
        Args:
            token: JWT token to invalidate
            
        Returns:
            Logout status
        """
        self.auth_manager.logout(token)
        return {"success": True, "status": "logged_out"}

    def vision_admin_validate(self, token: str) -> dict[str, Any]:
        """Validate token and get user info.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token validity and user info
        """
        validated = self.auth_manager.validate_token(token)
        if not validated:
            return {
                "valid": False,
                "error": "Token invalid or expired",
            }
        return {
            "valid": True,
            "user_id": validated.user_id,
            "role": validated.role.value,
            "expires_at": validated.expires_at,
        }

    def vision_admin_users(self, token: str) -> dict[str, Any]:
        """List all users (admin only).
        
        Args:
            token: Admin JWT token
            
        Returns:
            List of users or error
        """
        if not self.require_admin(token):
            return {
                "success": False,
                "error": "Admin access required",
            }
        users = self.auth_manager.list_users(token)
        return {
            "success": True,
            "users": users or [],
        }

    def vision_admin_create_user(
        self,
        token: str,
        username: str,
        password: str,
        role: str = "user",
    ) -> dict[str, Any]:
        """Create new user (admin only).
        
        Args:
            token: Admin JWT token
            username: New username
            password: New password
            role: Role (user/teacher/admin)
            
        Returns:
            Created user or error
        """
        if not self.require_admin(token):
            return {
                "success": False,
                "error": "Admin access required",
            }

        try:
            role_enum = Role(role)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid role: {role}",
            }

        user = self.auth_manager.create_user(username, password, role_enum)
        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role.value,
                "created_at": user.created_at,
            },
        }

    def vision_admin_delete_user(self, token: str, user_id: str) -> dict[str, Any]:
        """Delete user (admin only).
        
        Args:
            token: Admin JWT token
            user_id: User ID to delete
            
        Returns:
            Deletion status
        """
        if not self.auth_manager.delete_user(token, user_id):
            return {
                "success": False,
                "error": "Admin access required or cannot delete self",
            }
        return {
            "success": True,
            "deleted": user_id,
        }

    def vision_admin_logs(self, token: str, limit: int = 50) -> dict[str, Any]:
        """View audit logs (admin/teacher).
        
        Args:
            token: JWT token with teacher+ role
            limit: Maximum entries to return
            
        Returns:
            Audit logs or error
        """
        if not self.require_teacher(token):
            return {
                "success": False,
                "error": "Teacher or admin access required",
            }

        log_file = self.auth_manager.audit.log_file
        try:
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()
                entries = [json.loads(line) for line in lines[-limit:]]
                return {
                    "success": True,
                    "logs": entries,
                }
        except FileNotFoundError:
            return {
                "success": True,
                "logs": [],
            }

    def vision_admin_stats(self, token: str) -> dict[str, Any]:
        """Get system statistics (admin/teacher).
        
        Args:
            token: JWT token with teacher+ role
            
        Returns:
            System stats or error
        """
        if not self.require_teacher(token):
            return {
                "success": False,
                "error": "Teacher or admin access required",
            }

        try:
            with open(self.auth_manager.audit.log_file, encoding="utf-8") as f:
                audit_count = sum(1 for _ in f)
        except FileNotFoundError:
            audit_count = 0

        return {
            "success": True,
            "stats": {
                "total_users": len(self.auth_manager.users),
                "active_tokens": len(self.auth_manager.tokens),
                "audit_entries": audit_count,
            },
        }


# Singleton instance
admin_mcp_tools = AdminMCPTools()

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Vision Admin")

@mcp.tool()
def vision_admin_login(username: str, password: str) -> dict[str, Any]:
    """Authenticate and get JWT token.
    
    Args:
        username: Admin username
        password: Admin password
    """
    return admin_mcp_tools.vision_admin_login(username, password)

@mcp.tool()
def vision_admin_logout(token: str) -> dict[str, Any]:
    """Invalidate token.
    
    Args:
        token: JWT token to invalidate
    """
    return admin_mcp_tools.vision_admin_logout(token)

@mcp.tool()
def vision_admin_validate(token: str) -> dict[str, Any]:
    """Validate token and get user info.
    
    Args:
        token: JWT token to validate
    """
    return admin_mcp_tools.vision_admin_validate(token)

@mcp.tool()
def vision_admin_users(token: str) -> dict[str, Any]:
    """List all users (admin only).
    
    Args:
        token: Admin JWT token
    """
    return admin_mcp_tools.vision_admin_users(token)

@mcp.tool()
def vision_admin_create_user(token: str, username: str, password: str, role: str = "user") -> dict[str, Any]:
    """Create new user (admin only).
    
    Args:
        token: Admin JWT token
        username: New username
        password: New password
        role: Role (user/teacher/admin)
    """
    return admin_mcp_tools.vision_admin_create_user(token, username, password, role)

@mcp.tool()
def vision_admin_delete_user(token: str, user_id: str) -> dict[str, Any]:
    """Delete user (admin only).
    
    Args:
        token: Admin JWT token
        user_id: User ID to delete
    """
    return admin_mcp_tools.vision_admin_delete_user(token, user_id)

@mcp.tool()
def vision_admin_logs(token: str, limit: int = 50) -> dict[str, Any]:
    """View audit logs (admin/teacher).
    
    Args:
        token: JWT token with teacher+ role
        limit: Maximum entries to return
    """
    return admin_mcp_tools.vision_admin_logs(token, limit)

@mcp.tool()
def vision_admin_stats(token: str) -> dict[str, Any]:
    """Get system statistics (admin/teacher).
    
    Args:
        token: JWT token with teacher+ role
    """
    return admin_mcp_tools.vision_admin_stats(token)

if __name__ == "__main__":
    mcp.run()
