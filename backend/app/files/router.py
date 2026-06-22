"""Download stored verification artifacts."""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.auth.dependencies import get_current_user
from app.config import Settings, get_settings
from app.files.schemas import CursorPullRunListResponse
from app.files.service import StoredFilesService
from app.models.auth import User

router = APIRouter(prefix="/files", tags=["Files"])


def get_stored_files_service(
    settings: Settings = Depends(get_settings),
) -> StoredFilesService:
    return StoredFilesService(settings)


@router.get("/cursor-pulls", response_model=CursorPullRunListResponse)
async def list_cursor_pull_runs(
    _current_user: User = Depends(get_current_user),
    service: StoredFilesService = Depends(get_stored_files_service),
) -> CursorPullRunListResponse:
    return service.list_cursor_pull_runs()


@router.get("/cursor-pulls/{tool_id}/{run_id}/{filename}")
async def download_cursor_pull_file(
    tool_id: str,
    run_id: str,
    filename: str,
    _current_user: User = Depends(get_current_user),
    service: StoredFilesService = Depends(get_stored_files_service),
) -> FileResponse:
    file_path, media_type = service.resolve_cursor_pull_file(tool_id, run_id, filename)
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )


@router.get("/copilot-pulls", response_model=CursorPullRunListResponse)
async def list_copilot_pull_runs(
    _current_user: User = Depends(get_current_user),
    service: StoredFilesService = Depends(get_stored_files_service),
) -> CursorPullRunListResponse:
    return service.list_copilot_pull_runs()


@router.get("/copilot-pulls/{tool_id}/{run_id}/{filename}")
async def download_copilot_pull_file(
    tool_id: str,
    run_id: str,
    filename: str,
    _current_user: User = Depends(get_current_user),
    service: StoredFilesService = Depends(get_stored_files_service),
) -> FileResponse:
    file_path, media_type = service.resolve_copilot_pull_file(tool_id, run_id, filename)
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )


@router.get("/openai-pulls", response_model=CursorPullRunListResponse)
async def list_openai_pull_runs(
    _current_user: User = Depends(get_current_user),
    service: StoredFilesService = Depends(get_stored_files_service),
) -> CursorPullRunListResponse:
    return service.list_openai_pull_runs()


@router.get("/openai-pulls/{tool_id}/{run_id}/{filename}")
async def download_openai_pull_file(
    tool_id: str,
    run_id: str,
    filename: str,
    _current_user: User = Depends(get_current_user),
    service: StoredFilesService = Depends(get_stored_files_service),
) -> FileResponse:
    file_path, media_type = service.resolve_openai_pull_file(tool_id, run_id, filename)
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )
