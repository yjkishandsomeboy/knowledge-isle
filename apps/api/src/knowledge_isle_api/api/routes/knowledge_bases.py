from fastapi import APIRouter, HTTPException, status

from knowledge_isle_api.api.dependencies import CurrentUser, DatabaseSession
from knowledge_isle_api.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from knowledge_isle_api.services.knowledge_bases import (
    create_knowledge_base,
    delete_knowledge_base,
    get_knowledge_base,
    list_knowledge_bases,
    update_knowledge_base,
)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge bases"])


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases_route(
    session: DatabaseSession,
    user: CurrentUser,
) -> list[KnowledgeBaseResponse]:
    knowledge_bases = await list_knowledge_bases(session, user.id)
    return [KnowledgeBaseResponse.model_validate(item) for item in knowledge_bases]


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base_route(
    payload: KnowledgeBaseCreate,
    session: DatabaseSession,
    user: CurrentUser,
) -> KnowledgeBaseResponse:
    knowledge_base = await create_knowledge_base(
        session,
        owner_id=user.id,
        name=payload.name,
        description=payload.description,
        default_locale=payload.default_locale,
    )
    return KnowledgeBaseResponse.model_validate(knowledge_base)


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base_route(
    knowledge_base_id: str,
    payload: KnowledgeBaseUpdate,
    session: DatabaseSession,
    user: CurrentUser,
) -> KnowledgeBaseResponse:
    knowledge_base = await get_knowledge_base(
        session,
        knowledge_base_id=knowledge_base_id,
        owner_id=user.id,
    )
    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )
    knowledge_base = await update_knowledge_base(
        session,
        knowledge_base,
        name=payload.name,
        description=payload.description,
        default_locale=payload.default_locale,
    )
    return KnowledgeBaseResponse.model_validate(knowledge_base)


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base_route(
    knowledge_base_id: str,
    session: DatabaseSession,
    user: CurrentUser,
) -> None:
    knowledge_base = await get_knowledge_base(
        session,
        knowledge_base_id=knowledge_base_id,
        owner_id=user.id,
    )
    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )
    await delete_knowledge_base(session, knowledge_base)
