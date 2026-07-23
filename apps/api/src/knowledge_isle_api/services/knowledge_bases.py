from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_isle_api.models.knowledge_base import KnowledgeBase


async def list_knowledge_bases(session: AsyncSession, owner_id: str) -> list[KnowledgeBase]:
    result = await session.scalars(
        select(KnowledgeBase)
        .where(KnowledgeBase.owner_id == owner_id)
        .order_by(KnowledgeBase.created_at.desc())
    )
    return list(result)


async def get_knowledge_base(
    session: AsyncSession,
    *,
    knowledge_base_id: str,
    owner_id: str,
) -> KnowledgeBase | None:
    return await session.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.owner_id == owner_id,
        )
    )


async def create_knowledge_base(
    session: AsyncSession,
    *,
    owner_id: str,
    name: str,
    description: str | None,
    default_locale: str,
) -> KnowledgeBase:
    knowledge_base = KnowledgeBase(
        owner_id=owner_id,
        name=name.strip(),
        description=description.strip() if description else None,
        default_locale=default_locale,
    )
    session.add(knowledge_base)
    await session.commit()
    await session.refresh(knowledge_base)
    return knowledge_base


async def update_knowledge_base(
    session: AsyncSession,
    knowledge_base: KnowledgeBase,
    *,
    name: str | None,
    description: str | None,
    default_locale: str | None,
) -> KnowledgeBase:
    if name is not None:
        knowledge_base.name = name.strip()
    if description is not None:
        knowledge_base.description = description.strip() or None
    if default_locale is not None:
        knowledge_base.default_locale = default_locale
    await session.commit()
    await session.refresh(knowledge_base)
    return knowledge_base


async def delete_knowledge_base(session: AsyncSession, knowledge_base: KnowledgeBase) -> None:
    await session.delete(knowledge_base)
    await session.commit()
