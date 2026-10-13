from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/children")
def create_child() -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet (Stage 2)")
