"""Upload data access."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion import ParsedRow, Upload


class UploadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_organization(self, organization_id: UUID) -> list[Upload]:
        result = await self._session.execute(
            select(Upload)
            .where(
                Upload.organization_id == organization_id,
                Upload.deleted_at.is_(None),
            )
            .order_by(Upload.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, upload_id: UUID, organization_id: UUID) -> Upload | None:
        result = await self._session.execute(
            select(Upload).where(
                Upload.id == upload_id,
                Upload.organization_id == organization_id,
                Upload.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, upload: Upload) -> Upload:
        self._session.add(upload)
        await self._session.flush()
        return upload

    async def soft_delete(self, upload: Upload) -> None:
        upload.deleted_at = datetime.now(UTC)
        upload.status = "deleted"
        await self._session.flush()

    async def list_parsed_rows(self, upload_id: UUID) -> list[ParsedRow]:
        result = await self._session.execute(
            select(ParsedRow)
            .where(ParsedRow.upload_id == upload_id)
            .order_by(ParsedRow.row_number.asc())
        )
        return list(result.scalars().all())

    async def add_parsed_rows(self, rows: list[ParsedRow]) -> None:
        self._session.add_all(rows)
        await self._session.flush()

    async def delete_parsed_rows(self, upload_id: UUID) -> None:
        result = await self._session.execute(
            select(ParsedRow).where(ParsedRow.upload_id == upload_id)
        )
        for row in result.scalars().all():
            await self._session.delete(row)
        await self._session.flush()

    async def keep_parsed_rows(self, upload_id: UUID, row_numbers: set[int]) -> int:
        result = await self._session.execute(
            select(ParsedRow).where(ParsedRow.upload_id == upload_id)
        )
        kept = 0
        for row in result.scalars().all():
            if row.row_number in row_numbers:
                kept += 1
            else:
                await self._session.delete(row)
        await self._session.flush()
        return kept
