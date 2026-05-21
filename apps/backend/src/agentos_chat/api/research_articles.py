import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.dependencies import CurrentIdentity, get_current_identity
from agentos_chat.db.identity_session_repository import IdentitySessionRepository
from agentos_chat.db.models import ArticleStatusEnum
from agentos_chat.db.research_repository import ResearchRepository
from agentos_chat.db.session import get_db_session
from agentos_chat.models.research_schemas import (
    UpdateArticleStatusRequest,
    UpdateArticleStatusResponse,
)

router = APIRouter(prefix="/api/research", tags=["research-articles"])


@router.patch(
    "/articles/{article_id}/status",
    response_model=UpdateArticleStatusResponse,
)
async def update_article_status(
    article_id: uuid.UUID,
    body: UpdateArticleStatusRequest,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> UpdateArticleStatusResponse:
    id_repo = IdentitySessionRepository(db)
    user_identity_id = await id_repo.ensure_identity(identity.auth_subject)

    repo = ResearchRepository(db)
    article = await repo.get_article_for_owner(article_id, user_identity_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )

    latest = await repo.get_latest_version(article_id)
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No article version found.",
        )

    new_status = ArticleStatusEnum(body.status.value)
    await repo.update_version_status(latest.id, new_status)
    await db.commit()

    return UpdateArticleStatusResponse(
        article_id=article_id,
        version_number=latest.version_number,
        status=body.status,
    )
