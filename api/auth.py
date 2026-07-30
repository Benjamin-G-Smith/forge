import os

from fastapi import HTTPException, Request

VIEW_TOKEN = os.environ.get("VIEW_TOKEN", "")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")


async def auth_middleware(request: Request, call_next):
    token = request.query_params.get("v")
    auth_header = request.headers.get("Authorization", "")
    bearer = auth_header.removeprefix("Bearer ").strip()

    request.state.is_admin = bool(ADMIN_TOKEN) and bearer == ADMIN_TOKEN
    request.state.is_viewer = request.state.is_admin or (
        bool(VIEW_TOKEN) and token == VIEW_TOKEN
    )

    is_frontend_asset = not request.url.path.startswith("/api/")
    if not request.state.is_viewer and not is_frontend_asset:
        from fastapi.responses import JSONResponse

        return JSONResponse({"error": "unauthorized"}, status_code=401)

    return await call_next(request)


def require_admin(request: Request) -> None:
    if not getattr(request.state, "is_admin", False):
        raise HTTPException(status_code=403, detail="admin token required")
