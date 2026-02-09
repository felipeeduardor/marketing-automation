from fastapi import Header, HTTPException


async def get_tenant_id(x_tenant_id: str = Header(default="default")) -> str:
    """Extract tenant ID from request header. Used to isolate data per client."""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    return x_tenant_id
