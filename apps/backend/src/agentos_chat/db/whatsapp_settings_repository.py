from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agentos_chat.db.models import AllowedPhoneNumber, WhatsAppSettings
from agentos_chat.db.whatsapp_validation import is_valid_e164, normalize_whatsapp_phone


class InvalidPhoneNumberError(ValueError):
    pass


class DuplicatePhoneNumberError(ValueError):
    pass


class PhoneNotFoundError(ValueError):
    pass


async def _load_settings(db: AsyncSession, settings_id: UUID) -> WhatsAppSettings:
    result = await db.execute(
        select(WhatsAppSettings)
        .options(selectinload(WhatsAppSettings.allowed_phone_numbers))
        .where(WhatsAppSettings.id == settings_id)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


async def get_or_create_settings(db: AsyncSession) -> WhatsAppSettings:
    result = await db.execute(
        select(WhatsAppSettings)
        .options(selectinload(WhatsAppSettings.allowed_phone_numbers))
        .limit(1)
    )
    settings = result.scalar_one_or_none()
    if settings is not None:
        return settings

    settings = WhatsAppSettings(enabled=False)
    db.add(settings)
    await db.flush()
    await db.commit()
    return await _load_settings(db, settings.id)


async def update_enabled(db: AsyncSession, *, enabled: bool) -> WhatsAppSettings:
    settings = await get_or_create_settings(db)
    settings_id = settings.id
    settings.enabled = enabled
    await db.commit()
    db.expire_all()
    return await _load_settings(db, settings_id)


async def add_allowlist_phone(db: AsyncSession, *, phone_number: str) -> WhatsAppSettings:
    normalized = normalize_whatsapp_phone(phone_number)
    if not is_valid_e164(normalized):
        raise InvalidPhoneNumberError(f"Invalid E.164 phone number: {phone_number}")

    settings = await get_or_create_settings(db)
    settings_id = settings.id
    existing = {entry.phone_number for entry in settings.allowed_phone_numbers}
    if normalized in existing:
        raise DuplicatePhoneNumberError(f"Phone number already in allowlist: {normalized}")

    db.add(AllowedPhoneNumber(settings_id=settings_id, phone_number=normalized))
    await db.commit()
    db.expire_all()
    return await _load_settings(db, settings_id)


async def remove_allowlist_phone(db: AsyncSession, *, phone_number: str) -> WhatsAppSettings:
    normalized = normalize_whatsapp_phone(phone_number)
    settings = await get_or_create_settings(db)
    settings_id = settings.id
    target = next(
        (entry for entry in settings.allowed_phone_numbers if entry.phone_number == normalized),
        None,
    )
    if target is None:
        raise PhoneNotFoundError(f"Phone number not in allowlist: {normalized}")

    await db.delete(target)
    await db.commit()
    db.expire_all()
    return await _load_settings(db, settings_id)


async def get_settings_by_id(db: AsyncSession, settings_id: UUID) -> WhatsAppSettings | None:
    result = await db.execute(
        select(WhatsAppSettings)
        .options(selectinload(WhatsAppSettings.allowed_phone_numbers))
        .where(WhatsAppSettings.id == settings_id)
    )
    return result.scalar_one_or_none()
