# app/services/tts_runner.py
import subprocess
import sys
import os
import signal
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class TTSServer:
    def __init__(self):
        self.process = None

    def start(self):
        """启动 TTS 子进程"""
        if self.process:
            logger.warning("⚠️ TTS Service is already running!")
            return

        try:
            tts_path = str(settings.TTS_ROUTE)
            python_exec = os.path.join(tts_path, "runtime", "python.exe")
            if not os.path.exists(python_exec):
                 python_exec = "python"
            
            cmd = [
                python_exec, 
                "api_v2.py",
                "-a", settings.TTS_API_HOST,
                "-p", str(settings.TTS_API_PORT),
                "-c", os.path.join("GPT_SoVITS", "configs", "tts_infer.yaml")
            ]

            logger.info(f"🚀 Launching GPT-SoVITS V2...")
            
            self.process = subprocess.Popen(
                cmd,
                cwd=tts_path,
                shell=True,
                stdout=sys.stdout, 
                stderr=sys.stderr
            )
            logger.info(f"✅ TTS Service started with PID: {self.process.pid}")

        except Exception as e:
            logger.error(f"❌ Failed to start TTS Service: {e}")

    def stop(self):
        """优雅关闭 TTS 子进程"""
        if self.process:
            if self.process.poll() is None:
                logger.info(f"🛑 Stopping TTS Service (PID: {self.process.pid})...")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            self.process = None
            logger.info("✅ TTS Service stopped.")

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None
