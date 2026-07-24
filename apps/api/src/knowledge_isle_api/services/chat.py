from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_isle_api.models.citation import Citation
from knowledge_isle_api.models.conversation import Conversation
from knowledge_isle_api.models.message import Message
from knowledge_isle_api.services.ai_provider import generate_answer, stream_answer
from knowledge_isle_api.services.retrieval import RetrievedEvidence, retrieve_evidence


async def ask_question(
    session: AsyncSession,
    *,
    knowledge_base_id: str,
    owner_id: str,
    question: str,
    conversation_id: str | None,
) -> tuple[Conversation, Message, list[RetrievedEvidence]]:
    conversation = None
    if conversation_id is not None:
        conversation = await session.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.knowledge_base_id == knowledge_base_id,
                Conversation.owner_id == owner_id,
            )
        )
    if conversation is None:
        conversation = Conversation(
            knowledge_base_id=knowledge_base_id,
            owner_id=owner_id,
            title=question.strip()[:200],
        )
        session.add(conversation)
        await session.flush()

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=question.strip(),
    )
    session.add(user_message)
    evidence = await retrieve_evidence(
        session, knowledge_base_id=knowledge_base_id, question=question
    )
    answer = await generate_answer(question, evidence)
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
    )
    session.add(assistant_message)
    await session.flush()
    session.add_all(
        Citation(
            message_id=assistant_message.id,
            document_id=item.document_id,
            chunk_id=item.chunk_id,
            snippet=item.snippet,
            rank=index,
            start_offset=item.start_offset,
            end_offset=item.end_offset,
        )
        for index, item in enumerate(evidence, 1)
    )
    await session.commit()
    await session.refresh(assistant_message)
    return conversation, assistant_message, evidence


async def prepare_question(
    session: AsyncSession,
    *,
    knowledge_base_id: str,
    owner_id: str,
    question: str,
    conversation_id: str | None,
) -> tuple[Conversation, Message, list[RetrievedEvidence]]:
    conversation = None
    if conversation_id is not None:
        conversation = await session.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.knowledge_base_id == knowledge_base_id,
                Conversation.owner_id == owner_id,
            )
        )
    if conversation is None:
        conversation = Conversation(
            knowledge_base_id=knowledge_base_id, owner_id=owner_id, title=question.strip()[:200]
        )
        session.add(conversation)
        await session.flush()
    user_message = Message(conversation_id=conversation.id, role="user", content=question.strip())
    session.add(user_message)
    evidence = await retrieve_evidence(
        session, knowledge_base_id=knowledge_base_id, question=question
    )
    await session.flush()
    return conversation, user_message, evidence


async def stream_question(
    session: AsyncSession,
    *,
    knowledge_base_id: str,
    owner_id: str,
    question: str,
    conversation_id: str | None,
) -> AsyncIterator[tuple[str, object]]:
    conversation, _, evidence = await prepare_question(
        session,
        knowledge_base_id=knowledge_base_id,
        owner_id=owner_id,
        question=question,
        conversation_id=conversation_id,
    )
    parts: list[str] = []
    async for delta in stream_answer(question, evidence):
        parts.append(delta)
        yield "delta", delta
    answer = "".join(parts)
    assistant_message = Message(conversation_id=conversation.id, role="assistant", content=answer)
    session.add(assistant_message)
    await session.flush()
    session.add_all(
        Citation(
            message_id=assistant_message.id,
            document_id=item.document_id,
            chunk_id=item.chunk_id,
            snippet=item.snippet,
            rank=index,
            start_offset=item.start_offset,
            end_offset=item.end_offset,
        )
        for index, item in enumerate(evidence, 1)
    )
    await session.commit()
    await session.refresh(assistant_message)
    yield "done", (conversation, assistant_message, evidence)
