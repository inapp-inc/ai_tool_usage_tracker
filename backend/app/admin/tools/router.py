"""AI tools API routes (FR-ADM-001)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.tools.schemas import (
    ToolCreateRequest,
    ToolCsvColumnMapping,
    ToolCsvImportPreview,
    ToolCsvImportResponse,
    ToolCsvInspectResponse,
    ToolListResponse,
    ToolResponse,
    ToolSyncResponse,
    ToolUpdateRequest,
)
from app.admin.tools.service import (
    ToolConflictError,
    ToolCsvImportError,
    ToolNotFoundError,
    ToolService,
    ToolSyncError,
)
from app.core.pagination import CursorError
from app.auth.dependencies import get_current_user
from app.auth.service import AuthenticatedUser
from app.core.rbac import require_super_admin
from app.db.session import get_session

router = APIRouter(prefix="/tools", tags=["Tools"])

MAX_CSV_BYTES = 10 * 1024 * 1024


async def _read_csv_upload(file: UploadFile) -> tuple[str, bytes]:
    file_name = file.filename or "upload.csv"
    if not file_name.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported for tool usage import.",
        )
    content = await file.read()
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV file exceeds the 10 MB limit.",
        )
    return file_name, content


def _mapping_from_form(
    token_column: str | None = Form(default=None),
    cost_column: str | None = Form(default=None),
    date_column: str | None = Form(default=None),
    date_from_column: str | None = Form(default=None),
    date_to_column: str | None = Form(default=None),
) -> ToolCsvColumnMapping | None:
    if not token_column:
        return None
    return ToolCsvColumnMapping(
        token_column=token_column or None,
        cost_column=cost_column or None,
        date_column=date_column or None,
        date_from_column=date_from_column or None,
        date_to_column=date_to_column or None,
    )


@router.post(
    "/import-csv/inspect",
    response_model=ToolCsvInspectResponse,
    summary="List CSV headers and suggested column mapping",
    operation_id="inspectToolCsvImport",
)
async def inspect_tool_csv_import(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ToolCsvInspectResponse:
    _file_name, content = await _read_csv_upload(file)
    service = ToolService(session)
    try:
        return await service.inspect_csv_import(current_user, content=content)
    except ToolCsvImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/import-csv/preview",
    response_model=ToolCsvImportPreview,
    summary="Preview usage metrics extracted from a CSV file",
    operation_id="previewToolCsvImport",
)
async def preview_tool_csv_import(
    file: UploadFile = File(...),
    token_column: str | None = Form(default=None),
    cost_column: str | None = Form(default=None),
    date_column: str | None = Form(default=None),
    date_from_column: str | None = Form(default=None),
    date_to_column: str | None = Form(default=None),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ToolCsvImportPreview:
    file_name, content = await _read_csv_upload(file)
    mapping = _mapping_from_form(
        token_column=token_column,
        cost_column=cost_column,
        date_column=date_column,
        date_from_column=date_from_column,
        date_to_column=date_to_column,
    )
    service = ToolService(session)
    try:
        return await service.preview_csv_import(
            current_user,
            file_name=file_name,
            content=content,
            mapping=mapping,
        )
    except ToolCsvImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/import-csv",
    response_model=ToolCsvImportResponse,
    summary="Create or update a tool from CSV usage data",
    operation_id="importToolCsv",
)
async def import_tool_csv(
    file: UploadFile = File(...),
    name: str = Form(...),
    provider: str = Form(...),
    mode: str = Form(default="create"),
    tool_id: uuid.UUID | None = Form(default=None),
    replace_existing: bool = Form(default=True),
    token_column: str | None = Form(default=None),
    cost_column: str | None = Form(default=None),
    date_column: str | None = Form(default=None),
    date_from_column: str | None = Form(default=None),
    date_to_column: str | None = Form(default=None),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ToolCsvImportResponse:
    if mode not in {"create", "update"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="mode must be create or update.",
        )

    file_name, content = await _read_csv_upload(file)
    mapping = _mapping_from_form(
        token_column=token_column,
        cost_column=cost_column,
        date_column=date_column,
        date_from_column=date_from_column,
        date_to_column=date_to_column,
    )
    service = ToolService(session)
    try:
        return await service.import_csv(
            current_user,
            file_name=file_name,
            content=content,
            name=name,
            provider=provider,
            mode=mode,
            tool_id=tool_id,
            replace_existing=replace_existing,
            mapping=mapping,
        )
    except ToolNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        ) from exc
    except ToolConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tool with this name already exists in your organization.",
        ) from exc
    except ToolCsvImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=ToolListResponse,
    summary="List AI tools",
    operation_id="listTools",
)
async def list_tools(
    active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ToolListResponse:
    service = ToolService(session)
    try:
        return await service.list_tools(
            current_user, active=active, limit=limit, cursor=cursor
        )
    except CursorError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=ToolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI tool",
    operation_id="createTool",
)
async def create_tool(
    body: ToolCreateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ToolResponse:
    service = ToolService(session)
    try:
        return await service.create_tool(current_user, body)
    except ToolConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tool with this name already exists in your organization.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{tool_id}",
    response_model=ToolResponse,
    summary="Get AI tool by ID",
    operation_id="getTool",
)
async def get_tool(
    tool_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ToolResponse:
    service = ToolService(session)
    try:
        return await service.get_tool(current_user, tool_id)
    except ToolNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        ) from exc


@router.patch(
    "/{tool_id}",
    response_model=ToolResponse,
    summary="Update AI tool",
    operation_id="updateTool",
)
async def update_tool(
    tool_id: uuid.UUID,
    body: ToolUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ToolResponse:
    service = ToolService(session)
    try:
        return await service.update_tool(current_user, tool_id, body)
    except ToolNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        ) from exc
    except ToolConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tool with this name already exists in your organization.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{tool_id}/sync",
    response_model=ToolSyncResponse,
    summary="Validate credential and sync tool connection",
    operation_id="syncTool",
)
async def sync_tool(
    tool_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ToolSyncResponse:
    service = ToolService(session)
    try:
        return await service.sync_tool(current_user, tool_id)
    except ToolNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found.",
        ) from exc
    except ToolSyncError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
