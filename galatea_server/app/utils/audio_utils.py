"""音频处理工具函数

提供 WAV 文件格式处理、修复等功能
"""
import struct
from app.core.logger import get_logger

logger = get_logger(__name__)


def fix_wav_header(wav_data: bytes, sample_rate: int = 32000) -> bytes:
    """
    修复 WAV header，确保 chunk size 字段正确
    
    GPT-SoVITS 等 TTS 服务在流式传输时可能生成不正确的 header，
    此函数会重新计算并修复 RIFF chunk size 和 data chunk size。
    
    Args:
        wav_data: 原始 WAV 数据
        sample_rate: 采样率（默认 32000Hz）
    
    Returns:
        bytes: 修复后的 WAV 数据
        
    Raises:
        ValueError: 当 WAV 数据太短时
    """
    if len(wav_data) < 44:
        logger.error(f"WAV 数据太短: {len(wav_data)} bytes")
        raise ValueError(f"Invalid WAV data: too short ({len(wav_data)} bytes)")
    
    # 检查是否是有效的 WAV 文件
    if wav_data[:4] != b'RIFF' or wav_data[8:12] != b'WAVE':
        logger.warning("不是有效的 WAV 文件，尝试添加 WAV header")
        return create_wav_header(wav_data, sample_rate)
    
    # 计算正确的文件大小
    data_size = len(wav_data) - 44  # 减去 header 大小
    file_size = len(wav_data) - 8   # RIFF chunk size
    
    # 创建新的 header
    header = bytearray(wav_data[:44])
    
    # 修复 RIFF chunk size (字节 4-7)
    header[4:8] = struct.pack('<I', file_size)
    
    # 修复 data chunk size (字节 40-43)
    header[40:44] = struct.pack('<I', data_size)
    
    logger.debug(f"修复 WAV header: file_size={file_size}, data_size={data_size}")
    
    return bytes(header) + wav_data[44:]


def create_wav_header(
    pcm_data: bytes, 
    sample_rate: int = 32000, 
    bits_per_sample: int = 16, 
    channels: int = 1
) -> bytes:
    """
    为原始 PCM 数据创建标准的 WAV header
    
    当接收到的数据不包含 WAV header 时，此函数会创建一个标准的
    PCM WAV header 并附加到原始数据前。
    
    Args:
        pcm_data: 原始 PCM 音频数据
        sample_rate: 采样率（Hz）
        bits_per_sample: 位深度（8 或 16）
        channels: 声道数（1=单声道, 2=立体声）
    
    Returns:
        bytes: 完整的 WAV 文件数据（header + PCM data）
    """
    data_size = len(pcm_data)
    file_size = data_size + 36  # 36 是 header 大小（不含 RIFF 和 size 字段）
    
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',           # Chunk ID
        file_size,         # Chunk size
        b'WAVE',           # Format
        b'fmt ',           # Subchunk1 ID
        16,                # Subchunk1 size (16 for PCM)
        1,                 # Audio format (1 = PCM)
        channels,          # Number of channels
        sample_rate,       # Sample rate
        byte_rate,         # Byte rate
        block_align,       # Block align
        bits_per_sample,   # Bits per sample
        b'data',           # Subchunk2 ID
        data_size          # Subchunk2 size
    )
    
    logger.debug(f"创建 WAV header: sample_rate={sample_rate}, data_size={data_size}")
    
    return header + pcm_data


def validate_wav_format(wav_data: bytes) -> dict:
    """
    验证并解析 WAV 文件格式信息
    
    Args:
        wav_data: WAV 文件数据
    
    Returns:
        dict: WAV 格式信息 {
            'valid': bool,
            'sample_rate': int,
            'channels': int,
            'bits_per_sample': int,
            'data_size': int,
            'duration': float
        }
    """
    if len(wav_data) < 44:
        return {'valid': False, 'error': 'WAV data too short'}
    
    if wav_data[:4] != b'RIFF' or wav_data[8:12] != b'WAVE':
        return {'valid': False, 'error': 'Not a valid WAV file'}
    
    # 解析格式信息
    channels = struct.unpack('<H', wav_data[22:24])[0]
    sample_rate = struct.unpack('<I', wav_data[24:28])[0]
    bits_per_sample = struct.unpack('<H', wav_data[34:36])[0]
    data_size = struct.unpack('<I', wav_data[40:44])[0]
    
    # 计算时长
    byte_rate = sample_rate * channels * bits_per_sample // 8
    duration = data_size / byte_rate if byte_rate > 0 else 0
    
    return {
        'valid': True,
        'sample_rate': sample_rate,
        'channels': channels,
        'bits_per_sample': bits_per_sample,
        'data_size': data_size,
        'duration': duration
    }
