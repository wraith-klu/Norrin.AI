from fastapi import APIRouter

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/status")
def status() -> dict[str, str]:
    return {"status": "ready"}
