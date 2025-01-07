from dataclasses import dataclass, field
from typing import Optional, Dict, List
from pathlib import Path
from enum import Enum

class AnalysisDepth(Enum):
    BASIC = "basic"
    FULL = "full"
    DEEP = "deep"

@dataclass
class LLMConfig:
    model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.0
    system_prompt: str = "You are an expert code and business logic analyzer."
    batch_size: int = 3

@dataclass
class AnalyzerConfig:
    project_root: Path
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    openai_api_key: Optional[str] = None
    ignore_patterns: List[str] = field(default_factory=lambda: [
        '__pycache__', '*.pyc', 'venv', '.git', 'node_modules'
    ])
    analysis_depth: AnalysisDepth = AnalysisDepth.FULL
    supported_languages: Dict[str, List[str]] = field(default_factory=lambda: {
        'python': ['.py'],
        'javascript': ['.js', '.jsx', '.ts', '.tsx'],
        'docker': ['Dockerfile', 'docker-compose.yml'],
        'nginx': ['.conf']
    })
    cache_dir: Path = Path(".cache/project_analyzer")
    
    def __post_init__(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
