from fastapi import APIRouter, HTTPException, status

from knowledge_isle_api.api.dependencies import CurrentUser, DatabaseSession
from knowledge_isle_api.schemas.chat import AskRequest, AskResponse, CitationResponse
from knowledge_isle_api.services.chat import ask_question
from knowledge_isle_api.services.knowledge_bases import get_knowledge_base

router = APIRouter(prefix="/knowledge-bases/{knowledge_base_id}/chat", tags=["chat"])


@router.post("", response_model=AskResponse)
async def ask_question_route(
    knowledge_base_id: str,
    payload: AskRequest,
    session: DatabaseSession,
    user: CurrentUser,
) -> AskResponse:
    knowledge_base = await get_knowledge_base(
        session, knowledge_base_id=knowledge_base_id, owner_id=user.id
    )
    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )
    conversation, message, evidence = await ask_question(
        session,
        knowledge_base_id=knowledge_base_id,
        owner_id=user.id,
        question=payload.question,
        conversation_id=payload.conversation_id,
    )
    return AskResponse(
        conversation_id=conversation.id,
        message_id=message.id,
        answer=message.content,
        citations=[
            CitationResponse(
                document_id=item.document_id,
                filename=item.filename,
                snippet=item.snippet,
                rank=index,
                chunk_id=item.chunk_id,
                start_offset=item.start_offset,
                end_offset=item.end_offset,
            )
            for index, item in enumerate(evidence, 1)
        ],
        created_at=message.created_at,
    )
