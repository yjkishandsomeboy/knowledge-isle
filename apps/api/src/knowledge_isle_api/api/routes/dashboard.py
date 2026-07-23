from fastapi import APIRouter

from knowledge_isle_api.api.dependencies import CurrentUser

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def dashboard(user: CurrentUser) -> dict[str, str]:
    return {"message": "Knowledge Isle is ready", "userId": user.id}
