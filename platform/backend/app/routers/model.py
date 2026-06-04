"""Model inference router — passthrough to hosted custom model (stubs)."""
import logging
import time
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from app.dependencies import get_current_user
from app.schemas.common import ok

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/model")


@router.post("/infer")
async def model_infer(body: dict, request: Request, current_user=Depends(get_current_user)):
    """Direct prompt→completion via the configured custom model endpoint."""
    from app.config import settings
    custom_url = getattr(settings, "custom_model_url", "")
    if not custom_url:
        return ok({"status": "not_configured", "completion": "", "model": None, "latency_ms": 0})

    llm = getattr(request.app.state, "llm_provider", None)
    if llm is None:
        return ok({"status": "not_configured", "completion": "", "model": None, "latency_ms": 0})

    start = time.time()
    try:
        completion = await llm.complete(body.get("system", ""), body.get("user", ""))
        latency_ms = int((time.time() - start) * 1000)
        return ok({
            "status": "ok",
            "completion": completion,
            "model": getattr(settings, "custom_model_name", "careergraph-v1"),
            "latency_ms": latency_ms,
        })
    except Exception as exc:
        logger.error(f"model_infer error: {exc}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Custom model unavailable")


@router.get("/status")
async def model_status(current_user=Depends(get_current_user)):
    """Health status of the custom model endpoint."""
    from app.config import settings
    custom_url = getattr(settings, "custom_model_url", "")
    if not custom_url:
        return ok({"status": "not_configured", "model": None, "url": None})

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{custom_url.rstrip('/')}/health")
        if resp.status_code < 400:
            return ok({
                "status": "available",
                "model": getattr(settings, "custom_model_name", "careergraph-v1"),
                "url": custom_url,
            })
    except Exception:
        pass

    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "data": {"status": "unavailable", "url": custom_url},
            "message": "Custom model unreachable",
        },
    )
