from app.services.session_service import (
    create_session_service,
    delete_session_service,
    get_contacts_service,
    get_history_service,
)
from app.api.deps import get_character_registry, get_session_repo, get_message_repo
from app.infrastructure.managers.character_registry import CharacterRegistry
from app.schemas.session import (
    CreateSessionRequest, CreateSessionResponse,
    ContactsResponse,
    GetHistoryResponse,
    CharactersResponse,
    CharacterInfo,
)
from app.schemas.common import UnifiedResponse
from app.repositories.session_repo import SessionRepository
from app.repositories.message_repo import MessageRepository
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/characters", response_model=UnifiedResponse[CharactersResponse])
def get_characters_endpoint(
    character_registry: CharacterRegistry = Depends(get_character_registry),
):
    """获取可用角色列表"""
    char_ids = character_registry.list_available_characters()
    
    characters = []
    for char_id in char_ids:
        gala_info = character_registry.get_character(char_id)
        if gala_info:
            avatar_url = ""
            if gala_info.avatar:
                from app.utils.path_utils import resolve_static_url
                avatar_url = resolve_static_url(gala_info.avatar.image)
            
            characters.append(CharacterInfo(
                character_id=char_id,
                name=gala_info.get_name(),
                description=gala_info.description.get("zh", ""),
                avatar_url=avatar_url,
            ))
    
    return UnifiedResponse.success(
        message="获取角色列表成功",
        data=CharactersResponse(characters=characters)
    )


@router.post("/create", response_model=UnifiedResponse[CreateSessionResponse])
async def create_session_endpoint(
    request: CreateSessionRequest,
    session_repo: SessionRepository = Depends(get_session_repo),
    character_registry: CharacterRegistry = Depends(get_character_registry),
):
    """创建新会话"""
    return await create_session_service(
        request=request,
        session_repo=session_repo,
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
