from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentos_chat.auth.dependencies import CurrentIdentity, get_current_identity
from agentos_chat.db.models import WhatsAppSettings
from agentos_chat.db.session import get_db_session
from agentos_chat.db.whatsapp_settings_repository import (
    DuplicatePhoneNumberError,
    InvalidPhoneNumberError,
    PhoneNotFoundError,
    add_allowlist_phone,
    get_or_create_settings,
    remove_allowlist_phone,
    update_enabled,
)
from agentos_chat.models.schemas import (
    AllowedPhoneNumberSchema,
    WhatsAppAllowlistAddRequest,
    WhatsAppSettingsSchema,
    WhatsAppSettingsUpdateRequest,
)

router = APIRouter(prefix="/api/whatsapp/settings", tags=["whatsapp-settings"])


def _to_schema(settings: WhatsAppSettings) -> WhatsAppSettingsSchema:
    return WhatsAppSettingsSchema(
        enabled=settings.enabled,
        allowed_phone_numbers=[
            AllowedPhoneNumberSchema(
                phone_number=entry.phone_number,
                created_at=entry.created_at,
            )
            for entry in sorted(settings.allowed_phone_numbers, key=lambda e: e.created_at)
        ],
    )


@router.get("", response_model=WhatsAppSettingsSchema)
async def get_whatsapp_settings(
    _identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> WhatsAppSettingsSchema:
    settings = await get_or_create_settings(db)
    return _to_schema(settings)


@router.patch("", response_model=WhatsAppSettingsSchema)
async def patch_whatsapp_settings(
    body: WhatsAppSettingsUpdateRequest,
    _identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> WhatsAppSettingsSchema:
    settings = await update_enabled(db, enabled=body.enabled)
    return _to_schema(settings)


@router.post(
    "/allowlist",
    response_model=WhatsAppSettingsSchema,
    status_code=status.HTTP_201_CREATED,
)
async def post_allowlist_phone(
    body: WhatsAppAllowlistAddRequest,
    _identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> WhatsAppSettingsSchema:
    try:
        settings = await add_allowlist_phone(db, phone_number=body.phone_number)
    except InvalidPhoneNumberError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_phone_number", "message": str(exc)},
        ) from exc
    except DuplicatePhoneNumberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "duplicate_phone", "message": str(exc)},
        ) from exc
    return _to_schema(settings)


@router.delete("/allowlist/{phone_number}", response_model=WhatsAppSettingsSchema)
async def delete_allowlist_phone(
    phone_number: str,
    _identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db_session),
) -> WhatsAppSettingsSchema:
    try:
        settings = await remove_allowlist_phone(db, phone_number=phone_number)
    except PhoneNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": str(exc)},
        ) from exc
    return _to_schema(settings)
