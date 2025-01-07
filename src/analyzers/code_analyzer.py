import ast
from pathlib import Path
from typing import Dict, List, Any
import openai
from ..core.config import AnalyzerConfig

class CodeAnalyzer:
    def __init__(self, config: AnalyzerConfig):
        self.config = config
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        
    async def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analiza un archivo individual usando OpenAI."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Análisis estático básico
        try:
            ast.parse(content)
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
            
        # Análisis con OpenAI
        prompt = f"""Analiza el siguiente código Python y proporciona:
        1. Un resumen de su funcionalidad
        2. Posibles problemas o mejoras
        3. Complejidad ciclomática estimada
        4. Calidad del código (1-10)
        
        Código:
        {content}
        """
        
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "Eres un experto analista de código Python que proporciona análisis detallados y objetivos."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        analysis = response.choices[0].message.content
        
        return {
            "file_path": str(file_path),
            "syntax_valid": syntax_valid,
            "ai_analysis": analysis,
            "loc": len(content.splitlines())
        }
    
    async def analyze_project(self) -> Dict[str, List[Dict[str, Any]]]:
        """Analiza todo el proyecto React."""
        results = []
        
        # Buscar archivos Python recursivamente
        python_files = list(self.config.project_root.rglob("*.py"))
        
        # Analizar cada archivo
        for file_path in python_files:
            result = await self.analyze_file(file_path)
            results.append(result)
            
        return {
            "project_root": str(self.config.project_root),
            "files_analyzed": len(results),
            "results": results
        }
