"""Unity 进程管理器

负责启动、关闭和管理 Unity 客户端进程
"""
import subprocess
import os
from pathlib import Path
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class UnityProcess:
    """Unity 进程管理器"""
    
    def __init__(self):
        self.process: subprocess.Popen | None = None
        self._unity_exe_path: Path | None = None
    
    def _get_unity_exe_path(self) -> Path:
        """获取 Unity exe 的绝对路径"""
        if self._unity_exe_path is None:
            # 从相对路径计算绝对路径
            relative_path = settings.UNITY_EXE_PATH
            # BASE_DIR 是 galatea_server/ 目录
            base_dir = settings.BASE_DIR
            unity_path = (base_dir / relative_path).resolve()
            
            if not unity_path.exists():
                raise FileNotFoundError(
                    f"Unity exe not found at: {unity_path}\n"
                    f"请检查配置: UNITY_EXE_PATH={settings.UNITY_EXE_PATH}"
                )
            
            self._unity_exe_path = unity_path
            logger.info(f"📍 Unity exe path resolved: {unity_path}")
        
        return self._unity_exe_path
    
    def start(self) -> dict:
        """启动 Unity 进程
        
        Returns:
            dict: 包含状态信息的字典
        """
        if self.is_running():
            logger.warning("⚠️ Unity is already running!")
            return {
                "success": False,
                "message": "Unity 已经在运行中",
                "pid": self.process.pid if self.process else None
            }
        
        try:
            unity_exe = self._get_unity_exe_path()
            
            logger.info(f"🚀 Launching Unity from: {unity_exe}")
            
            # 启动 Unity 进程
            self.process = subprocess.Popen(
                [str(unity_exe)],
                cwd=unity_exe.parent,  # 工作目录设为 exe 所在目录
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )
            
            logger.info(f"✅ Unity started with PID: {self.process.pid}")
            
            return {
                "success": True,
                "message": "Unity 启动成功",
                "pid": self.process.pid
            }
            
        except FileNotFoundError as e:
            logger.error(f"❌ Unity exe not found: {e}")
            return {
                "success": False,
                "message": f"找不到 Unity 执行文件: {str(e)}",
                "pid": None
            }
        except Exception as e:
            logger.error(f"❌ Failed to start Unity: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"启动 Unity 失败: {str(e)}",
                "pid": None
            }
    
    def stop(self) -> dict:
        """关闭 Unity 进程
        
        Returns:
            dict: 包含状态信息的字典
        """
        if not self.process:
            logger.warning("⚠️ No Unity process to stop")
            return {
                "success": False,
                "message": "Unity 进程不存在"
            }
        
        if self.process.poll() is not None:
            # 进程已经结束
            logger.info("Unity process already terminated")
            self.process = None
            return {
                "success": True,
                "message": "Unity 进程已停止"
            }
        
        try:
            pid = self.process.pid
            logger.info(f"🛑 Stopping Unity (PID: {pid})...")
            
            # 先尝试优雅关闭
            self.process.terminate()
            
            try:
                # 等待最多 5 秒
                self.process.wait(timeout=5)
                logger.info("✅ Unity stopped gracefully")
            except subprocess.TimeoutExpired:
                # 如果超时，强制关闭
                logger.warning("⚠️ Unity did not stop gracefully, forcing kill...")
                self.process.kill()
                self.process.wait()
                logger.info("✅ Unity killed")
            
            self.process = None
            
            return {
                "success": True,
                "message": "Unity 已关闭"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to stop Unity: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"关闭 Unity 失败: {str(e)}"
            }
    
    def is_running(self) -> bool:
        """检查 Unity 进程是否正在运行
        
        Returns:
            bool: True 如果正在运行，否则 False
        """
        if self.process is None:
            return False
        
        # poll() 返回 None 表示进程仍在运行
        return self.process.poll() is None
    
    def get_status(self) -> dict:
        """获取 Unity 进程状态
        
        Returns:
            dict: 包含进程状态信息的字典
        """
        running = self.is_running()
        
        return {
            "running": running,
            "pid": self.process.pid if running else None
        }
