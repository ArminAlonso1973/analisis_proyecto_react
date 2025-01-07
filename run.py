from src.core.config import AnalyzerConfig
from src.analyzers.code_analyzer import CodeAnalyzer
from pathlib import Path
import asyncio

async def main():
    config = AnalyzerConfig(project_root=Path("."), openai_api_key="tu_clave_api")
    analyzer = CodeAnalyzer(config)
    results = await analyzer.analyze_project()
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
