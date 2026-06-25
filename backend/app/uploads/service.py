"""Upload file ingestion — parse CSV/JSON, store raw + mapped rows separately."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.copilot.billing_import import (
    COPILOT_MAPPING_FIELD_LABELS,
    parse_copilot_billing_csv,
    suggest_copilot_column_mapping,
    summarize_aggregates,
)
from app.copilot.billing_import_service import CopilotBillingImportService
from app.figma.billing_import import (
    FIGMA_MAPPING_FIELD_LABELS,
    aggregate_figma_billing_rows,
    parse_figma_billing_csv,
    suggest_figma_column_mapping,
    summarize_figma_aggregates,
)
from app.figma.billing_import_service import FigmaBillingImportService
from app.figma.pricing import calculate_figma_row_costs, figma_pricing_from_assignment
from app.models.admin import Tool
from app.models.auth import User
from app.models.collector import UsageEvent
from app.models.ingestion import ParsedRow, Upload
from app.teams.membership_repository import TeamMembershipRepository
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
        self._memberships = TeamMembershipRepository(session)

    async def list_uploads(
        self,
        organization_id: UUID,
        team_ids: list[UUID] | None = None,
        *,
        team_id: UUID | None = None,
        tool_id: UUID | None = None,
        period_from: date | None = None,
        period_to: date | None = None,
    ) -> UploadListResponse:
        rows = await self._uploads.list_by_organization(
            organization_id,
            team_id=team_id,
            tool_id=tool_id,
            period_from=period_from,
            period_to=period_to,
        )
        if team_ids is not None:
            rows = [r for r in rows if r.team_id is None or r.team_id in set(team_ids)]
        uploader_names = await self._uploader_names(rows)
        team_names = await self._team_names(organization_id, rows)
        tool_names = await self._tool_names(organization_id, rows)
        data = [
            self._to_upload_response(
                row,
                team_name=team_names.get(row.team_id) if row.team_id else None,
                uploaded_by_name=uploader_names.get(row.uploaded_by),
                tool_name=tool_names.get(row.tool_id) if row.tool_id else None,
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
        tool_id: UUID | None = None,
    ) -> UploadCreateResponse:
        if user.role not in ADMIN_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

        if team_id is not None:
            team = await self._teams.get_by_id(team_id, user.organization_id)
            if team is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

        resolved_tool = await self._resolve_catalogue_tool(user.organization_id, tool_id)
        if tool_id is not None and resolved_tool is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found.")
        if resolved_tool is not None and resolved_tool.vendor == "copilot" and team_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Copilot billing CSV uploads require a team.",
            )
        if resolved_tool is not None and resolved_tool.vendor == "figma" and team_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Figma billing CSV uploads require a team.",
            )

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
            tool_id=resolved_tool.id if resolved_tool else None,
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

        tools = await self._tool_lookups(user.organization_id, team_id)
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
                mapped_payload=self._with_team_context(row.mapped_payload, team_id),
            )
            for row in parsed.rows
        ]
        await self._uploads.add_parsed_rows(parsed_rows)

        upload.status = "preview_ready"
        upload.total_rows = len(parsed.rows)
        upload.matched_rows = len(parsed.rows)
        upload.unmatched_rows = 0

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

        is_copilot = await self._is_copilot_upload(upload)
        is_figma = await self._is_figma_upload(upload)
        suggested = (
            suggest_copilot_column_mapping(headers)
            if is_copilot
            else suggest_figma_column_mapping(headers)
            if is_figma
            else suggest_column_mapping(headers)
        )
        field_labels = (
            COPILOT_MAPPING_FIELD_LABELS
            if is_copilot
            else FIGMA_MAPPING_FIELD_LABELS
            if is_figma
            else MAPPING_FIELD_LABELS
        )

        fields = [
            UploadMappingField(
                key=key,
                label=label,
                required=is_copilot and key in {"sku", "unit_type"},
            )
            for key, label in field_labels.items()
        ]
        saved = upload.column_mapping if isinstance(upload.column_mapping, dict) else None

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
        if not any(column for column in mapping.values() if column):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Map at least one CSV column before continuing.",
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

        upload.status = "parsing"
        await self._session.flush()

        if await self._is_copilot_upload(upload):
            users_by_login: dict[str, UUID] = {}
            if upload.team_id is not None:
                from app.copilot.user_matching import build_team_copilot_user_lookup

                users_by_login = await build_team_copilot_user_lookup(
                    self._session,
                    organization_id=organization_id,
                    team_id=upload.team_id,
                )
            parsed_rows, _aggregates, error_message = self._parse_copilot_rows(
                text,
                mapping,
                organization_id=organization_id,
                upload_id=upload.id,
                team_id=upload.team_id,
                users_by_login=users_by_login,
            )
            if error_message:
                upload.status = "failed"
                upload.error_message = error_message
                await self._session.commit()
                await self._session.refresh(upload)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message,
                )
            await self._uploads.delete_parsed_rows(upload.id)
            await self._uploads.add_parsed_rows(parsed_rows)
            upload.status = "preview_ready"
            upload.column_mapping = mapping
            upload.total_rows = len(parsed_rows)
            upload.matched_rows = len(parsed_rows)
            upload.unmatched_rows = 0
            upload.error_message = None
            await self._session.commit()
            await self._session.refresh(upload)
            return self._to_upload_response(
                upload,
                team_name=await self._resolve_team_name(organization_id, upload.team_id),
                uploaded_by_name=await self._resolve_uploader_name(upload.uploaded_by),
            )

        if await self._is_figma_upload(upload):
            users_by_email = await self._users_by_email(organization_id)
            parsed_rows, error_message = self._parse_figma_rows(
                text,
                mapping,
                organization_id=organization_id,
                upload_id=upload.id,
                team_id=upload.team_id,
                users_by_email=users_by_email,
            )
            if error_message:
                upload.status = "failed"
                upload.error_message = error_message
                await self._session.commit()
                await self._session.refresh(upload)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message,
                )
            await self._uploads.delete_parsed_rows(upload.id)
            await self._uploads.add_parsed_rows(parsed_rows)
            upload.status = "preview_ready"
            upload.column_mapping = mapping
            upload.total_rows = len(parsed_rows)
            upload.matched_rows = len(parsed_rows)
            upload.unmatched_rows = 0
            upload.error_message = None
            await self._session.commit()
            await self._session.refresh(upload)
            return self._to_upload_response(
                upload,
                team_name=await self._resolve_team_name(organization_id, upload.team_id),
                uploaded_by_name=await self._resolve_uploader_name(upload.uploaded_by),
            )

        tools = await self._tool_lookups(organization_id, upload.team_id)
        users = await self._users.list_by_organization(organization_id)
        users_by_email = {row.email.lower(): row.id for row in users}

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
                mapped_payload=self._with_team_context(row.mapped_payload, upload.team_id),
            )
            for row in parsed.rows
        ]
        await self._uploads.add_parsed_rows(parsed_rows)

        upload.status = "preview_ready"
        upload.column_mapping = mapping
        upload.total_rows = len(parsed.rows)
        upload.matched_rows = len(parsed.rows)
        upload.unmatched_rows = 0
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
        copilot_summary: dict | None = None
        figma_summary: dict | None = None
        if await self._is_copilot_upload(upload):
            from app.copilot.billing_import import aggregate_copilot_billing, summarize_aggregates
            from app.copilot.billing_import_service import copilot_rows_from_parsed
            from app.copilot.service import CopilotAnalyticsService
            from app.teams.team_tool_repository import TeamToolRepository

            billing_rows = copilot_rows_from_parsed(rows)
            aggregates = aggregate_copilot_billing(billing_rows)
            assignment = None
            if upload.team_id is not None and upload.tool_id is not None:
                team_tools = TeamToolRepository(self._session)
                assignment = await team_tools.get_by_team_and_tool(upload.team_id, upload.tool_id)
            _, _, configured_subscription, _ = CopilotAnalyticsService._configured_copilot_pricing(
                assignment
            )
            copilot_summary = summarize_aggregates(
                aggregates,
                configured_subscription=configured_subscription,
            )
            billing_service = CopilotBillingImportService(self._session)
            conflicts = await billing_service.find_period_conflicts(
                upload,
                organization_id=organization_id,
                aggregates=aggregates,
            )
            if conflicts:
                copilot_summary["period_conflicts"] = conflicts
            for row in rows:
                mapped = row.mapped_payload if isinstance(row.mapped_payload, dict) else {}
                raw = row.raw_payload if isinstance(row.raw_payload, dict) else {}
                preview_rows.append(
                    ParsedUsageRowResponse(
                        row_number=row.row_number,
                        user_email=mapped.get("user_login"),
                        matched_user_id=row.matched_user_id,
                        user_name=str(mapped.get("user_login") or "—"),
                        input_tokens=0,
                        output_tokens=0,
                        occurred_at=row.occurred_at,
                        model=str(mapped.get("sku") or ""),
                        cost=float(mapped.get("net_amount") or mapped.get("monthly_amount") or 0),
                        status="valid" if not row.error_reason else "error",
                        error_reason=row.error_reason,
                        raw_data=raw,
                        mapped_data=mapped,
                    )
                )
        elif await self._is_figma_upload(upload):
            from app.figma.billing_import_service import figma_rows_from_parsed
            from app.teams.team_tool_repository import TeamToolRepository

            billing_rows = figma_rows_from_parsed(rows)
            assignment = None
            if upload.team_id is not None and upload.tool_id is not None:
                team_tools = TeamToolRepository(self._session)
                assignment = await team_tools.get_by_team_and_tool(upload.team_id, upload.tool_id)
            pricing = figma_pricing_from_assignment(assignment)
            row_costs = [
                calculate_figma_row_costs(
                    seat_type=row.seat_type,
                    seat_credits_used=row.seat_credits_used,
                    paid_credits_used=row.paid_credits_used,
                    pricing=pricing,
                )
                for row in billing_rows
            ]
            aggregates = aggregate_figma_billing_rows(billing_rows, row_costs=row_costs)
            figma_summary = summarize_figma_aggregates(aggregates)
            figma_summary["credits_per_usd"] = (
                float(pricing.credits_per_usd) if pricing.credits_per_usd is not None else None
            )
            billing_service = FigmaBillingImportService(self._session)
            conflicts = await billing_service.find_period_conflicts(
                upload,
                organization_id=organization_id,
                aggregates=aggregates,
            )
            if conflicts:
                figma_summary["period_conflicts"] = conflicts
            billing_by_number = {row.row_number: row for row in billing_rows}
            cost_by_number = {
                billing_rows[index].row_number: row_costs[index]
                for index in range(len(billing_rows))
            }
            for row in rows:
                billing_row = billing_by_number.get(row.row_number)
                if billing_row is None:
                    continue
                mapped = row.mapped_payload if isinstance(row.mapped_payload, dict) else {}
                raw = row.raw_payload if isinstance(row.raw_payload, dict) else {}
                _, _, total = cost_by_number.get(billing_row.row_number, (Decimal("0"), Decimal("0"), Decimal("0")))
                preview_rows.append(
                    ParsedUsageRowResponse(
                        row_number=billing_row.row_number,
                        user_email=billing_row.user_email,
                        matched_user_id=row.matched_user_id,
                        user_name=billing_row.user_name or billing_row.user_email or "—",
                        input_tokens=0,
                        output_tokens=0,
                        occurred_at=billing_row.last_activity,
                        model=billing_row.seat_type,
                        cost=float(total),
                        status="valid" if not billing_row.error_reason else "error",
                        error_reason=billing_row.error_reason,
                        raw_data=raw,
                        mapped_data=mapped,
                    )
                )
        else:
            for row in rows:
                mapped = row.mapped_payload if isinstance(row.mapped_payload, dict) else {}
                raw = row.raw_payload if isinstance(row.raw_payload, dict) else {}
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
                        status="valid",
                        error_reason=row.error_reason,
                        raw_data=raw,
                        mapped_data=mapped,
                    )
                )

        return UploadPreviewResponse(
            upload_id=upload.id,
            filename=upload.filename,
            team_id=upload.team_id,
            team_name=await self._resolve_team_name(organization_id, upload.team_id),
            tool_id=upload.tool_id,
            total_rows=len(preview_rows),
            matched_rows=len(preview_rows),
            unmatched_rows=0,
            rows=preview_rows,
            copilot_summary=copilot_summary,
            figma_summary=figma_summary,
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

        parsed_rows = await self._uploads.list_parsed_rows(upload_id)
        if not parsed_rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload has no parsed rows to import.",
            )

        if body.row_numbers is not None:
            if not body.row_numbers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Select at least one row to import.",
                )
            available = {row.row_number for row in parsed_rows}
            invalid = [number for number in body.row_numbers if number not in available]
            if invalid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown row numbers: {', '.join(str(n) for n in invalid)}",
                )
            imported_count = await self._uploads.keep_parsed_rows(
                upload_id,
                set(body.row_numbers),
            )
        else:
            imported_count = len(parsed_rows)

        upload.total_rows = imported_count
        upload.matched_rows = imported_count
        upload.unmatched_rows = 0
        upload.status = "committing"
        await self._session.flush()

        remaining_rows = await self._uploads.list_parsed_rows(upload_id)
        if await self._is_copilot_upload(upload):
            from app.copilot.billing_import import aggregate_copilot_billing
            from app.copilot.billing_import_service import (
                CopilotBillingImportService,
                copilot_rows_from_parsed,
            )

            billing_rows = copilot_rows_from_parsed(remaining_rows)
            aggregates = aggregate_copilot_billing(billing_rows)
            billing_service = CopilotBillingImportService(self._session)
            await billing_service.assert_no_period_conflicts(
                upload,
                organization_id=organization_id,
                aggregates=aggregates,
            )
            await billing_service.commit_from_upload(
                upload,
                organization_id=organization_id,
                aggregates=aggregates,
            )
            from app.copilot.billing_period import period_from_aggregates

            period_start, period_end = period_from_aggregates(
                aggregates,
                fallback_anchor=datetime.now(UTC).date(),
            )
            if period_start and period_end:
                upload.billing_period_start = period_start
                upload.billing_period_end = period_end
                await billing_service.backfill_null_periods(
                    upload.id,
                    period_start,
                    period_end,
                )
            display_name = (
                f"{period_start.isoformat()}_{period_end.isoformat()}.csv"
                if period_start and period_end
                else None
            )
            if display_name:
                upload.filename = display_name
        elif await self._is_figma_upload(upload):
            from app.figma.billing_import_service import figma_rows_from_parsed

            billing_rows = figma_rows_from_parsed(remaining_rows)
            row_indexes = list(range(len(billing_rows)))
            from app.teams.team_tool_repository import TeamToolRepository

            assignment = None
            if upload.team_id is not None and upload.tool_id is not None:
                team_tools = TeamToolRepository(self._session)
                assignment = await team_tools.get_by_team_and_tool(upload.team_id, upload.tool_id)
            pricing = figma_pricing_from_assignment(assignment)
            aggregates = aggregate_figma_billing_rows(
                billing_rows,
                row_costs=[
                    calculate_figma_row_costs(
                        seat_type=row.seat_type,
                        seat_credits_used=row.seat_credits_used,
                        paid_credits_used=row.paid_credits_used,
                        pricing=pricing,
                    )
                    for row in billing_rows
                ],
            )
            billing_service = FigmaBillingImportService(self._session)
            await billing_service.assert_no_period_conflicts(
                upload,
                organization_id=organization_id,
                aggregates=aggregates,
            )
            matched_user_ids = {
                index: remaining_rows[index].matched_user_id
                for index in range(len(remaining_rows))
            }
            await billing_service.commit_from_upload(
                upload,
                organization_id=organization_id,
                billing_rows=billing_rows,
                row_indexes=row_indexes,
                matched_user_ids=matched_user_ids,
            )
            period_starts = [
                row.usage_period_start for row in billing_rows if row.usage_period_start
            ]
            period_ends = [row.usage_period_end for row in billing_rows if row.usage_period_end]
            if period_starts and period_ends:
                period_start = min(period_starts)
                period_end = max(period_ends)
                upload.billing_period_start = period_start
                upload.billing_period_end = period_end
                upload.filename = f"{period_start.isoformat()}_{period_end.isoformat()}.csv"
        else:
            await self._import_usage_rows(
                upload,
                remaining_rows,
                organization_id,
            )

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
        if await self._is_copilot_upload(upload):
            from app.copilot.billing_import_service import CopilotBillingImportService

            await CopilotBillingImportService(self._session).delete_by_upload_id(upload_id)
        elif await self._is_figma_upload(upload):
            await FigmaBillingImportService(self._session).delete_by_upload_id(upload_id)
        await self._uploads.soft_delete(upload)
        await self._session.commit()

    async def assert_upload_scope(
        self,
        organization_id: UUID,
        upload_id: UUID,
        managed_team_ids: list[UUID],
    ) -> None:
        """Raise 404 if the upload does not belong to any of team_admin's managed teams."""
        upload = await self._require_upload(organization_id, upload_id)
        if upload.team_id not in managed_team_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found.")

    async def _require_upload(self, organization_id: UUID, upload_id: UUID) -> Upload:
        upload = await self._uploads.get_by_id(upload_id, organization_id)
        if upload is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found.")
        return upload

    async def _tool_lookups(
        self,
        organization_id: UUID,
        team_id: UUID | None = None,
    ) -> list[ToolLookup]:
        tools = await self._tools.list_by_organization(organization_id, active=None)
        if team_id is None:
            return [
                ToolLookup(id=tool.id, name=tool.name, vendor=tool.vendor)
                for tool in tools
            ]

        team = await self._teams.get_by_id(team_id, organization_id)
        if team is None:
            return []

        allowed_ids: set[UUID] = set()
        tool_ids_raw = team.tool_ids if isinstance(team.tool_ids, list) else []
        for raw_tool_id in tool_ids_raw:
            try:
                allowed_ids.add(UUID(str(raw_tool_id)))
            except ValueError:
                continue

        filtered = [tool for tool in tools if tool.id in allowed_ids] if allowed_ids else tools
        return [
            ToolLookup(id=tool.id, name=tool.name, vendor=tool.vendor)
            for tool in filtered
        ]

    async def _import_usage_rows(
        self,
        upload: Upload,
        rows: list[ParsedRow],
        organization_id: UUID,
    ) -> None:
        team_id = upload.team_id
        linked_users: set[UUID] = set()

        for row in rows:
            mapped = row.mapped_payload if isinstance(row.mapped_payload, dict) else {}
            if team_id is not None:
                mapped = {**mapped, "team_id": str(team_id)}
                row.mapped_payload = mapped

            tool_id: UUID | None = None
            raw_tool_id = mapped.get("tool_id")
            if raw_tool_id:
                try:
                    tool_id = UUID(str(raw_tool_id))
                except ValueError:
                    tool_id = None

            provider = str(mapped.get("vendor") or "upload")
            occurred_at = row.occurred_at or datetime.now(UTC)
            total_tokens = int(row.input_tokens) + int(row.output_tokens)

            self._session.add(
                UsageEvent(
                    organization_id=organization_id,
                    team_id=team_id,
                    user_id=row.matched_user_id,
                    user_email=row.user_email,
                    upload_id=upload.id,
                    tool_id=tool_id,
                    collector_id=None,
                    provider=provider,
                    model=mapped.get("model"),
                    occurred_at=occurred_at,
                    input_tokens=int(row.input_tokens),
                    output_tokens=int(row.output_tokens),
                    cache_write_tokens=0,
                    cache_read_tokens=0,
                    total_tokens=total_tokens,
                    estimated_cost=Decimal(str(mapped.get("estimated_cost") or 0)),
                    vendor_event_id=f"upload-{upload.id}-{row.row_number}",
                )
            )

            if team_id is not None and row.matched_user_id is not None:
                linked_users.add(row.matched_user_id)

        for user_id in linked_users:
            await self._memberships.add(
                organization_id=organization_id,
                team_id=team_id,  # type: ignore[arg-type]
                user_id=user_id,
            )

        await self._session.flush()

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

    async def _tool_names(
        self,
        organization_id: UUID,
        uploads: list[Upload],
    ) -> dict[UUID, str]:
        ids = {row.tool_id for row in uploads if row.tool_id}
        if not ids:
            return {}
        tools = await self._tools.list_by_organization(organization_id, active=None)
        return {tool.id: tool.name for tool in tools if tool.id in ids}

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
    def _with_team_context(mapped_payload: dict, team_id: UUID | None) -> dict:
        payload = dict(mapped_payload) if isinstance(mapped_payload, dict) else {}
        if team_id is not None:
            payload["team_id"] = str(team_id)
        return payload

    async def _resolve_catalogue_tool(
        self,
        organization_id: UUID,
        tool_id: UUID | None,
    ) -> Tool | None:
        if tool_id is None:
            return None
        tool = await self._tools.get_by_id(tool_id, organization_id)
        if tool is None or not tool.catalogue_only:
            return None
        return tool

    async def _is_copilot_upload(self, upload: Upload) -> bool:
        if upload.tool_id is None:
            return False
        tool = await self._session.get(Tool, upload.tool_id)
        return tool is not None and tool.vendor == "copilot"

    async def _is_figma_upload(self, upload: Upload) -> bool:
        if upload.tool_id is None:
            return False
        tool = await self._session.get(Tool, upload.tool_id)
        return tool is not None and tool.vendor == "figma"

    async def _users_by_email(self, organization_id: UUID) -> dict[str, UUID]:
        users = await self._users.list_by_organization(organization_id)
        return {user.email.lower(): user.id for user in users}

    def _parse_figma_rows(
        self,
        text: str,
        mapping: dict[str, str | None],
        *,
        organization_id: UUID,
        upload_id: UUID,
        team_id: UUID | None,
        users_by_email: dict[str, UUID],
    ) -> tuple[list[ParsedRow], str | None]:
        result = parse_figma_billing_csv(text, column_mapping=mapping)
        if result.error_message:
            return [], result.error_message

        parsed_rows: list[ParsedRow] = []
        for row in result.rows:
            email_key = (row.user_email or "").strip().lower()
            matched_user_id = users_by_email.get(email_key) if email_key else None
            mapped_payload = {
                "figma_user_id": row.figma_user_id,
                "user_id": row.figma_user_id,
                "user_email": row.user_email,
                "user_name": row.user_name,
                "seat_type": row.seat_type,
                "seat_credits_used": str(row.seat_credits_used),
                "paid_credits_used": str(row.paid_credits_used),
                "last_activity": row.last_activity.isoformat() if row.last_activity else None,
                "usage_period_start": row.usage_period_start.isoformat()
                if row.usage_period_start
                else None,
                "usage_period_end": row.usage_period_end.isoformat()
                if row.usage_period_end
                else None,
                "vendor": "figma",
                "user_linked": matched_user_id is not None,
            }
            parsed_rows.append(
                ParsedRow(
                    organization_id=organization_id,
                    upload_id=upload_id,
                    row_number=row.row_number,
                    user_email=row.user_email,
                    matched_user_id=matched_user_id,
                    occurred_at=row.last_activity,
                    match_status="matched" if row.error_reason is None else "error",
                    error_reason=row.error_reason,
                    raw_payload=row.raw_payload,
                    mapped_payload=self._with_team_context(mapped_payload, team_id),
                )
            )
        return parsed_rows, None

    def _parse_copilot_rows(
        self,
        text: str,
        mapping: dict[str, str | None],
        *,
        organization_id: UUID,
        upload_id: UUID,
        team_id: UUID | None,
        users_by_login: dict[str, UUID] | None = None,
    ) -> tuple[list[ParsedRow], list, str | None]:
        from app.copilot.user_matching import match_copilot_user_login

        result = parse_copilot_billing_csv(text, column_mapping=mapping)
        if result.error_message:
            return [], [], result.error_message

        parsed_rows: list[ParsedRow] = []
        for row in result.rows:
            matched_user_id = match_copilot_user_login(row.user_login, users_by_login or {})
            mapped_payload = {
                "sku": row.sku,
                "unit_type": row.unit_type,
                "monthly_amount": str(row.monthly_amount),
                "net_amount": str(row.net_amount),
                "gross_amount": str(row.gross_amount),
                "quantity": row.quantity,
                "billing_period_start": row.billing_period_start.isoformat()
                if row.billing_period_start
                else None,
                "billing_period_end": row.billing_period_end.isoformat()
                if row.billing_period_end
                else None,
                "usage_date": row.usage_date.isoformat() if row.usage_date else None,
                "user_login": row.user_login,
                "vendor": "copilot",
                "user_linked": matched_user_id is not None,
            }
            parsed_rows.append(
                ParsedRow(
                    organization_id=organization_id,
                    upload_id=upload_id,
                    row_number=row.row_number,
                    user_email=row.user_login,
                    matched_user_id=matched_user_id,
                    occurred_at=None,
                    match_status="matched" if row.error_reason is None else "error",
                    error_reason=row.error_reason,
                    raw_payload=row.raw_payload,
                    mapped_payload=self._with_team_context(mapped_payload, team_id),
                )
            )
        return parsed_rows, result.aggregates, None

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
        tool_name: str | None = None,
    ) -> UploadResponse:
        row_count = None
        if upload.total_rows is not None:
            row_count = upload.total_rows
        return UploadResponse(
            id=upload.id,
            team_id=upload.team_id,
            tool_id=upload.tool_id,
            team_name=team_name,
            tool_name=tool_name,
            filename=upload.filename,
            detected_format=upload.detected_format,
            size_bytes=int(upload.size_bytes),
            status=upload.status,  # type: ignore[arg-type]
            total_rows=upload.total_rows,
            matched_rows=upload.matched_rows,
            unmatched_rows=upload.unmatched_rows,
            error_message=upload.error_message,
            uploaded_by_name=uploaded_by_name,
            billing_period_start=upload.billing_period_start,
            billing_period_end=upload.billing_period_end,
            created_at=upload.created_at,
            completed_at=upload.committed_at,
        )


def _copilot_period_metadata(
    aggregates: list,
) -> tuple[date | None, date | None, str | None]:
    from app.copilot.billing_import import CopilotBillingAggregate
    from app.copilot.billing_period import normalize_billing_period

    typed = [row for row in aggregates if isinstance(row, CopilotBillingAggregate)]
    normalized = [
        normalize_billing_period(row.billing_period_start, row.billing_period_end)
        for row in typed
    ]
    starts = [start for start, _end in normalized if start is not None]
    ends = [end for _start, end in normalized if end is not None]
    if not starts or not ends:
        return None, None, None
    period_start = min(starts)
    period_end = max(ends)
    return period_start, period_end, f"{period_start.isoformat()}_{period_end.isoformat()}.csv"
