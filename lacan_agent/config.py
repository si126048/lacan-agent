from __future__ import annotations
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    dashscope_api_key: str = ''
    db_path: str = './data/lacan.db'
    model: str = 'qwen-plus'
    temperature: float = 0.3
    log_level: str = 'INFO'

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            dashscope_api_key=os.environ.get('DASHSCOPE_API_KEY', ''),
            db_path=os.environ.get('LACAN_DB_PATH', './data/lacan.db'),
            model=os.environ.get('LACAN_MODEL', 'qwen-plus'),
            temperature=float(os.environ.get('LACAN_TEMPERATURE', '0.3')),
            log_level=os.environ.get('LACAN_LOG_LEVEL', 'INFO'),
        )
