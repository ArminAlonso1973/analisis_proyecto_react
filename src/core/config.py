from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class AnalyzerConfig:
    project_root: Path
    openai_api_key: str
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def __post_init__(self):
        if not isinstance(self.project_root, Path):
            self.project_root = Path(self.project_root)
