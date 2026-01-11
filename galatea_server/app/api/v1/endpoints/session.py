from app.services.session_service import *
from app.schemas.session import *
from app.schemas.common import UnifiedResponse
from fastapi import APIRouter, Depends
from app.api.deps import get_session_manager, get_character_registry, get_unity_manager
from app.infrastructure.managers.session_manager import SessionManager
from app.infrastructure.managers.character_registry import CharacterRegistry
from app.infrastructure.managers.unity_connection import UnityConnectionManager

router = APIRouter()


@router.post("/create", response_model=UnifiedResponse[CreateSessionResponse])   
async def create_session_endpoint(
    request: CreateSessionRequest,
    session_manager: SessionManager = Depends(get_session_manager),
    character_registry: CharacterRegistry = Depends(get_character_registry),
    unity_manager: UnityConnectionManager = Depends(get_unity_manager)
):
    """创建新会话的端点"""
    try:
        return await create_session_service(
            request=request,
            session_manager=session_manager,
            character_registry=character_registry,
            unity_manager=unity_manager
        )
    except Exception as e:
        raise e


@router.delete("/delete/{session_id}", response_model=UnifiedResponse)   
def delete_session_endpoint(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """删除会话的端点"""
    try:
        return delete_session_service(
            session_id=session_id,
            session_manager=session_manager
        )
    except Exception as e:
        raise e


@router.get("/contacts", response_model=UnifiedResponse[ContactsResponse])
def get_contacts_endpoint(
    language: str = "zh",
    session_manager: SessionManager = Depends(get_session_manager),
    character_registry: CharacterRegistry = Depends(get_character_registry)
):
    """
    获取通讯录
    
    返回所有角色及其会话，按两级排序：
    1. 角色按最近交互排序（最新的在前）
    2. 每个角色下的会话也按最近交互排序（最新的在前）
    
    Args:
        language: 语言代码（zh/en），用于返回对应语言的角色名称
    """
    try:
        return get_contacts_service(
            session_manager=session_manager,
            character_registry=character_registry,
            language=language
        )
    except Exception as e:
        raise e


@router.get("/history/{session_id}", response_model=UnifiedResponse[GetHistoryResponse])
def get_history_endpoint(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    获取会话历史记录
    """
    try:
        return get_history_service(
            session_id=session_id,
            session_manager=session_manager
        )
    except Exception as e:
        raise e


@router.get("/characters", response_model=UnifiedResponse[list[CharacterInfo]])
def get_available_characters_endpoint(
    character_registry: CharacterRegistry = Depends(get_character_registry)
):
    """
    获取所有可用角色的完整信息（用于角色选择界面）
    """
    return get_available_characters_service(character_registry)
