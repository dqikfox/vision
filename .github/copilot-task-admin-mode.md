# TASK: Build Admin Mode Feature for Vision

## Background
Issue #6: "Add Admin Mode"  
Issue #12: "Add teacher admin mode: auth-..."

The Vision project needs an administrative interface with authentication and privileged operations.

## Current State
- [x] MCP server exists with health/models/metrics/memory/tools APIs
- [x] `vision_admin.py` - Core authentication module created
- [x] `vision_admin_routes.py` - FastAPI routes created
- [x] `vision_admin_mcp.py` - MCP tools created
- [ ] Routes need to be registered in `vision_hotkey.py`
- [ ] MCP tools need to be integrated into `vision_mcp_server.py`

## Files Created

### 1. `vision_admin.py` ✅
JWT-based authentication with:
- Token generation/validation
- Role-based access (admin, teacher, user)
- PBKDF2 password hashing
- Rate limiting
- Audit logging

### 2. `vision_admin_routes.py` ✅
FastAPI routes:
- POST `/api/admin/login` - Authenticate and get token
- POST `/api/admin/logout` - Invalidate token
- GET `/api/admin/users` - List users (admin only)
- POST `/api/admin/users` - Create user (admin only)
- DELETE `/api/admin/users/{id}` - Delete user (admin only)
- GET `/api/admin/logs` - View system logs (admin/teacher)
- POST `/api/admin/config` - Update system config (admin only)
- GET `/api/admin/stats` - System statistics (admin/teacher)

### 3. `vision_admin_mcp.py` ✅
MCP tools:
- `vision_admin_login` - Authenticate
- `vision_admin_logout` - Invalidate token
- `vision_admin_validate` - Check token validity
- `vision_admin_users` - List users
- `vision_admin_create_user` - Create user
- `vision_admin_delete_user` - Delete user
- `vision_admin_logs` - View audit logs
- `vision_admin_stats` - System statistics

## Next Steps (for Copilot or manual)

### Step 4: Register Routes in `vision_hotkey.py`
Add to the FastAPI app initialization:
```python
from vision_admin_routes import router as admin_router
app.include_router(admin_router)
```

### Step 5: Integrate MCP Tools
Update `vision_mcp_server.py` to include admin tools:
```python
from vision_admin_mcp import admin_mcp_tools

# Add admin tools to the tools dictionary
```

### Step 6: Update Environment Variables
Add to `.env.example`:
```
VISION_ADMIN_SECRET=your-jwt-secret
VISION_ADMIN_TOKEN_EXPIRY=3600
VISION_ADMIN_RATE_LIMIT=5
```

### Step 7: Create Tests
Create `tests/test_admin_mode.py` with tests for:
- Token generation/validation
- Role-based access control
- API endpoint access
- Audit logging

## Usage

### Login via API
```bash
curl -X POST http://localhost:8765/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme"}'
```

### Login via MCP
```
@vision-local admin_login {"username": "admin", "password": "changeme"}
```

## Security
- Default credentials: admin/changeme (change immediately)
- Tokens expire after 1 hour
- Rate limited to 5 login attempts per minute
- All admin actions logged to `.logs/admin_audit.log`

## Definition of Done
- [x] `vision_admin.py` - Authentication module
- [x] `vision_admin_routes.py` - API endpoints
- [x] `vision_admin_mcp.py` - MCP tools
- [ ] Routes registered in `vision_hotkey.py`
- [ ] MCP tools integrated
- [ ] `.env.example` updated
- [ ] Tests created
- [ ] Issue #6 can be closed

**Created by ULTRON for Copilot integration**  
**Date: 2026-05-14**
