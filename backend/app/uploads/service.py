"""Upload file ingestion — parse CSV/JSON, store raw + mapped rows separately."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.auth import User
from app.models.ingestion import ParsedRow, Upload
from app.teams.repository import TeamRepository
from app.tools.repository import ToolRepository
from app.uploads.parser import (
    MAPPING_FIELD_LABELS,
    ToolLookup,
    extract_csv_headers,
    extract_csv_sample_row,
    parse_upload_content,
    suggest_column_mapping,
)
from app.uploads.repository import UploadRepository
from app.uploads.schemas import (
    PaginationMeta,
    ParsedUsageRowResponse,
    UploadColumnMappingRequest,
    UploadCommitRequest,
    UploadCreateResponse,
    UploadListResponse,
    UploadMappingField,
    UploadMappingResponse,
    UploadPreviewResponse,
    UploadResponse,
)
from app.users.repository import UserAdminRepository

MAX_UPLOAD_BYTES = 52_428_800
ADMIN_ROLES = frozenset({"super_admin", "team_admin"})


class UploadService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._uploads = UploadRepository(session)
        self._teams = TeamRepository(session)
        self._tools = ToolRepository(session)
        self._users = UserAdminRepository(session)

    async def list_uploads(self, organization_id: UUID) -> UploadListResponse:
        rows = await self._uploads.list_by_organization(organization_id)
        uploader_names = await self._uploader_names(rows)
        team_names = await self._team_names(organization_id, rows)
        data = [
            self._to_upload_response(
                row,
                team_name=team_names.get(row.team_id) if row.team_id else None,
                uploaded_by_name=uploader_names.get(row.uploaded_by),
            )
            for row in rows
        ]
        return UploadListResponse(data=data, meta=PaginationMeta(has_more=False))

    async def create_upload(
        self,
        user: User,
        *,
        file: UploadFile,
        team_id: UUID | None,
    ) -> UploadCreateResponse:
        if user.role not in ADMIN_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

        if team_id is not None:
            team = await self._teams.get_by_id(team_id, user.organization_id)
            if team is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

        filename = file.filename or "upload.csv"
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds 50 MB limit.",
            )
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty.")

        detected_format = "json" if filename.lower().endswith(".json") else "csv"
        upload = Upload(
            organization_id=user.organization_id,
            team_id=team_id,
            uploaded_by=user.id,
            filename=filename,
            content_type=file.content_type,
            size_bytes=len(content),
            storage_key="",
            status="parsing",
            detected_format=detected_format,
        )
        await self._uploads.create(upload)

        storage_key = await self._persist_file(
            user.organization_id,
            upload.id,
            filename,
            content,
        )
        upload.storage_key = storage_key

        text = content.decode("utf-8-sig", errors="replace")

        if detected_format == "csv":
            headers, header_error = extract_csv_headers(text)
            if header_error:
                upload.status = "failed"
                upload.error_message = header_error
                await self._session.commit()
                await self._session.refresh(upload)
                response = self._to_upload_response(
                    upload,
                    team_name=await self._resolve_team_name(user.organization_id, team_id),
                    uploaded_by_name=self._display_name(user),
                )
                return UploadCreateResponse(
                    upload_id=upload.id,
                    status=upload.status,  # type: ignore[arg-type]
                    filename=upload.filename,
                    size_bytes=upload.size_bytes,
                    upload=response,
                )

            upload.status = "pending_mapping"
            upload.detected_headers = headers
            await self._session.commit()
            await self._session.refresh(upload)
            response = self._to_upload_response(
                upload,
                team_name=await self._resolve_team_name(user.organization_id, team_id),
                uploaded_by_name=self._display_name(user),
            )
            return UploadCreateResponse(
                upload_id=upload.id,
                status=upload.status,  # type: ignore[arg-type]
                filename=upload.filename,
                size_bytes=upload.size_bytes,
                upload=response,
            )

        tools = await self._tool_lookups(user.organization_id)
        users = await self._users.list_by_organization(user.organization_id)
        users_by_email = {row.email.lower(): row.id for row in users}

        parsed = parse_upload_content(
            text,
            filename=filename,
            tools=tools,
            users_by_email=users_by_email,
        )

        if parsed.error_message:
            upload.status = "failed"
            upload.error_message = parsed.error_message
            await self._session.commit()
            await self._session.refresh(upload)
            response = self._to_upload_response(
                upload,
                team_name=await self._resolve_team_name(user.organization_id, team_id),
                uploaded_by_name=self._display_name(user),
            )
            return UploadCreateResponse(
                upload_id=upload.id,
                status=upload.status,  # type: ignore[arg-type]
                filename=upload.filename,
                size_bytes=upload.size_bytes,
                upload=response,
            )

        parsed_rows = [
            ParsedRow(
                organization_id=user.organization_id,
                upload_id=upload.id,
                row_number=row.row_number,
                user_email=row.user_email,
                matched_user_id=row.matched_user_id,
                occurred_at=row.occurred_at,
                input_tokens=row.input_tokens,
                output_tokens=row.output_tokens,
                match_status=row.match_status,
                error_reason=row.error_reason,
                raw_payload=row.raw_payload,
                mapped_payload=row.mapped_payload,
            )
            for row in parsed.rows
        ]
        await self._uploads.add_parsed_rows(parsed_rows)

        matched = sum(1 for row in parsed.rows if row.match_status == "matched")
        unmatched = len(parsed.rows) - matched
        upload.status = "preview_ready"
        upload.total_rows = len(parsed.rows)
        upload.matched_rows = matched
        upload.unmatched_rows = unmatched

        await self._session.commit()
        await self._session.refresh(upload)

        response = self._to_upload_response(
            upload,
            team_name=await self._resolve_team_name(user.organization_id, team_id),
            uploaded_by_name=self._display_name(user),
        )
        return UploadCreateResponse(
            upload_id=upload.id,
            status=upload.status,  # type: ignore[arg-type]
            filename=upload.filename,
            size_bytes=upload.size_bytes,
            upload=response,
        )

    async def get_mapping(
        self,
        organization_id: UUID,
        upload_id: UUID,
    ) -> UploadMappingResponse:
        upload = await self._require_upload(organization_id, upload_id)
        if upload.status != "pending_mapping":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload is not awaiting column mapping.",
            )

        headers = upload.detected_headers if isinstance(upload.detected_headers, list) else []
        if not headers:
            content = self._read_upload_file(upload)
            text = content.decode("utf-8-sig", errors="replace")
            extracted, header_error = extract_csv_headers(text)
            if header_error:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=header_error)
            headers = extracted
            upload.detected_headers = headers
            await self._session.commit()

        sample_row: dict = {}
        content = self._read_upload_file(upload)
        text = content.decode("utf-8-sig", errors="replace")
        sample = extract_csv_sample_row(text)
        if sample:
            sample_row = sample

        suggested = suggest_column_mapping(headers)
        saved = upload.column_mapping if isinstance(upload.column_mapping, dict) else None

        fields = [
            UploadMappingField(
                key=key,
                label=MAPPING_FIELD_LABELS[key],
                required=key == "email",
            )
            for key in MAPPING_FIELD_LABELS
        ]

        return UploadMappingResponse(
            upload_id=upload.id,
            filename=upload.filename,
            headers=headers,
            fields=fields,
            suggested_mapping=suggested,
            column_mapping=saved,
            sample_row=sample_row,
        )

    async def apply_mapping(
        self,
        organization_id: UUID,
        upload_id: UUID,
        body: UploadColumnMappingRequest,
    ) -> UploadResponse:
        upload = await self._require_upload(organization_id, upload_id)
        if upload.status != "pending_mapping":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload is not awaiting column mapping.",
            )

        headers = upload.detected_headers if isinstance(upload.detected_headers, list) else []
        if not headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No CSV headers detected for this upload.",
            )

        mapping = body.model_dump(exclude_none=False)
        if not mapping.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email column mapping is required.",
            )

        header_set = set(headers)
        for field, column in mapping.items():
            if column and column not in header_set:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Column '{column}' for '{field}' was not found in the CSV headers.",
                )

        content = self._read_upload_file(upload)
        text = content.decode("utf-8-sig", errors="replace")

        tools = await self._tool_lookups(organization_id)
        users = await self._users.list_by_organization(organization_id)
        users_by_email = {row.email.lower(): row.id for row in users}

        upload.status = "parsing"
        await self._session.flush()

        parsed = parse_upload_content(
            text,
            filename=upload.filename,
            tools=tools,
            users_by_email=users_by_email,
            column_mapping=mapping,
        )

        if parsed.error_message:
            upload.status = "failed"
            upload.error_message = parsed.error_message
            await self._session.commit()
            await self._session.refresh(upload)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=parsed.error_message,
            )

        await self._uploads.delete_parsed_rows(upload.id)
        parsed_rows = [
            ParsedRow(
                organization_id=organization_id,
                upload_id=upload.id,
                row_number=row.row_number,
                user_email=row.user_email,
                matched_user_id=row.matched_user_id,
                occurred_at=row.occurred_at,
                input_tokens=row.input_tokens,
                output_tokens=row.output_tokens,
                match_status=row.match_status,
                error_reason=row.error_reason,
                raw_payload=row.raw_payload,
                mapped_payload=row.mapped_payload,
            )
            for row in parsed.rows
        ]
        await self._uploads.add_parsed_rows(parsed_rows)

        matched = sum(1 for row in parsed.rows if row.match_status == "matched")
        unmatched = len(parsed.rows) - matched
        upload.status = "preview_ready"
        upload.column_mapping = mapping
        upload.total_rows = len(parsed.rows)
        upload.matched_rows = matched
        upload.unmatched_rows = unmatched
        upload.error_message = None

        await self._session.commit()
        await self._session.refresh(upload)

        return self._to_upload_response(
            upload,
            team_name=await self._resolve_team_name(organization_id, upload.team_id),
            uploaded_by_name=await self._resolve_uploader_name(upload.uploaded_by),
        )

    async def get_preview(
        self,
        organization_id: UUID,
        upload_id: UUID,
    ) -> UploadPreviewResponse:
        upload = await self._require_upload(organization_id, upload_id)
        if upload.status == "pending_mapping":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload requires column mapping before preview.",
            )
        rows = await self._uploads.list_parsed_rows(upload_id)
        user_names = await self._matched_user_names(rows)

        preview_rows: list[ParsedUsageRowResponse] = []
        for row in rows:
            mapped = row.mapped_payload if isinstance(row.mapped_payload, dict) else {}
            raw = row.raw_payload if isinstance(row.raw_payload, dict) else {}
            is_valid = row.match_status == "matched"
            preview_rows.append(
                ParsedUsageRowResponse(
                    row_number=row.row_number,
                    user_email=row.user_email,
                    matched_user_id=row.matched_user_id,
                    user_name=user_names.get(row.matched_user_id)
                    or row.user_email
                    or "Unknown",
                    input_tokens=int(row.input_tokens),
                    output_tokens=int(row.output_tokens),
                    occurred_at=row.occurred_at,
                    model=mapped.get("model"),
                    cost=float(mapped.get("estimated_cost") or 0),
                    status="valid" if is_valid else "error",
                    error_reason=row.error_reason,
                    raw_data=raw,
                    mapped_data=mapped,
                )
            )

        matched = sum(1 for row in preview_rows if row.status == "valid")
        return UploadPreviewResponse(
            upload_id=upload.id,
            filename=upload.filename,
            total_rows=len(preview_rows),
            matched_rows=matched,
            unmatched_rows=len(preview_rows) - matched,
            rows=preview_rows,
        )

    async def commit_upload(
        self,
        organization_id: UUID,
        upload_id: UUID,
        body: UploadCommitRequest,
    ) -> UploadResponse:
        upload = await self._require_upload(organization_id, upload_id)
        if upload.status not in ("preview_ready", "completed"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload is not ready to commit.",
            )

        if body.team_id is not None:
            team = await self._teams.get_by_id(body.team_id, organization_id)
            if team is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
            upload.team_id = body.team_id

        upload.status = "committing"
        await self._session.flush()

        upload.status = "completed"
        upload.committed_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(upload)

        return self._to_upload_response(
            upload,
            team_name=await self._resolve_team_name(organization_id, upload.team_id),
            uploaded_by_name=await self._resolve_uploader_name(upload.uploaded_by),
        )

    async def delete_upload(self, organization_id: UUID, upload_id: UUID) -> None:
        upload = await self._require_upload(organization_id, upload_id)
        await self._uploads.soft_delete(upload)
        await self._session.commit()

    async def _require_upload(self, organization_id: UUID, upload_id: UUID) -> Upload:
        upload = await self._uploads.get_by_id(upload_id, organization_id)
        if upload is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found.")
        return upload

    async def _tool_lookups(self, organization_id: UUID) -> list[ToolLookup]:
        tools = await self._tools.list_by_organization(organization_id, active=None)
        return [
            ToolLookup(id=tool.id, name=tool.name, vendor=tool.vendor)
            for tool in tools
        ]

    async def _persist_file(
        self,
        organization_id: UUID,
        upload_id: UUID,
        filename: str,
        content: bytes,
    ) -> str:
        settings = get_settings()
        root = Path(settings.local_storage_root)
        relative = Path("uploads") / str(organization_id) / str(upload_id) / filename
        absolute = root / relative
        absolute.parent.mkdir(parents=True, exist_ok=True)
        absolute.write_bytes(content)
        return relative.as_posix()

    def _read_upload_file(self, upload: Upload) -> bytes:
        settings = get_settings()
        root = Path(settings.local_storage_root)
        absolute = root / upload.storage_key
        if not absolute.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload file not found on disk.",
            )
        return absolute.read_bytes()

    async def _uploader_names(self, uploads: list[Upload]) -> dict[UUID, str]:
        ids = {row.uploaded_by for row in uploads}
        if not ids:
            return {}
        users = await self._users.list_by_organization(uploads[0].organization_id)
        return {
            user.id: self._display_name(user)
            for user in users
            if user.id in ids
        }

    async def _team_names(
        self,
        organization_id: UUID,
        uploads: list[Upload],
    ) -> dict[UUID, str]:
        ids = {row.team_id for row in uploads if row.team_id}
        if not ids:
            return {}
        teams = await self._teams.list_by_organization(organization_id, active=None)
        return {team.id: team.name for team in teams if team.id in ids}

    async def _matched_user_names(self, rows: list[ParsedRow]) -> dict[UUID | None, str]:
        user_ids = {row.matched_user_id for row in rows if row.matched_user_id}
        if not user_ids:
            return {}
        from sqlalchemy import select

        from app.models.auth import User as AuthUser

        result = await self._session.execute(
            select(AuthUser).where(AuthUser.id.in_(user_ids))
        )
        return {
            user.id: self._display_name(user)
            for user in result.scalars().all()
        }

    async def _resolve_team_name(
        self,
        organization_id: UUID,
        team_id: UUID | None,
    ) -> str | None:
        if team_id is None:
            return None
        team = await self._teams.get_by_id(team_id, organization_id)
        return team.name if team else None

    async def _resolve_uploader_name(self, user_id: UUID) -> str | None:
        from sqlalchemy import select

        from app.models.auth import User as AuthUser

        result = await self._session.execute(select(AuthUser).where(AuthUser.id == user_id))
        user = result.scalar_one_or_none()
        return self._display_name(user) if user else None

    @staticmethod
    def _display_name(user: User) -> str:
        if user.display_name and user.display_name.strip():
            return user.display_name.strip()
        return user.email

    @staticmethod
    def _to_upload_response(
        upload: Upload,
        *,
        team_name: str | None,
        uploaded_by_name: str | None,
    ) -> UploadResponse:
        row_count = None
        if upload.total_rows is not None:
            row_count = upload.total_rows
        return UploadResponse(
            id=upload.id,
            team_id=upload.team_id,
            tool_id=upload.tool_id,
            team_name=team_name,
            filename=upload.filename,
            detected_format=upload.detected_format,
            size_bytes=int(upload.size_bytes),
            status=upload.status,  # type: ignore[arg-type]
            total_rows=upload.total_rows,
            matched_rows=upload.matched_rows,
            unmatched_rows=upload.unmatched_rows,
            error_message=upload.error_message,
            uploaded_by_name=uploaded_by_name,
            created_at=upload.created_at,
            completed_at=upload.committed_at,
        )
