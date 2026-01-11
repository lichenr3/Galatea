from app.core.container import session_manager, web_manager, unity_manager, character_registry

# 定义依赖获取函数
def get_session_manager():
    return session_manager

def get_web_manager():
    return web_manager

def get_unity_manager():
    return unity_manager

def get_character_registry():
    return character_registry
