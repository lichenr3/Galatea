from app.services.session_service import (
    create_session_service,
    delete_session_service,
    get_contacts_service,
    get_characters_service,
    get_history_service,
)
from app.api.deps import get_character_registry, get_session_repo, get_message_repo
from app.infrastructure.managers.character_registry import CharacterRegistry
from app.schemas.session import (
    CreateSessionRequest, CreateSessionResponse,
    ContactsResponse,
    GetHistoryResponse,
    CharacterInfo,
)
from app.schemas.common import UnifiedResponse
from app.repositories.session_repo import SessionRepository
from app.repositories.message_repo import MessageRepository
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/characters", response_model=UnifiedResponse[list[CharacterInfo]])
def get_characters_endpoint(
    character_registry: CharacterRegistry = Depends(get_character_registry),
):
    """获取可用角色列表"""
    return get_characters_service(character_registry=character_registry)


@router.post("/create", response_model=UnifiedResponse[CreateSessionResponse])
async def create_session_endpoint(
    request: CreateSessionRequest,
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
    character_registry: CharacterRegistry = Depends(get_character_registry),
):
    """创建新会话"""
    return await create_session_service(
        request=request,
        session_repo=session_repo,
        message_repo=message_repo,
        character_registry=character_registry,
    )


@router.delete("/{session_id}", response_model=UnifiedResponse)
async def delete_session_endpoint(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo),
):
    """删除会话"""
    return await delete_session_service(
        session_id=session_id,
        session_repo=session_repo,
    )


@router.get("/contacts", response_model=UnifiedResponse[ContactsResponse])
async def get_contacts_endpoint(
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
    character_registry: CharacterRegistry = Depends(get_character_registry),
):
    """获取通讯录"""
    return await get_contacts_service(
        session_repo=session_repo,
        message_repo=message_repo,
        character_registry=character_registry,
    )


@router.get("/history/{session_id}", response_model=UnifiedResponse[GetHistoryResponse])
async def get_history_endpoint(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
):
    """获取会话历史记录"""
    return await get_history_service(
        session_id=session_id,
        session_repo=session_repo,
        message_repo=message_repo,
    )
