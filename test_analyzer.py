import os
import asyncio
from src.core.config import AnalyzerConfig
from src.analyzers.code_analyzer import CodeAnalyzer
from pathlib import Path

async def test_analysis():
    # Configurar con una clave API de prueba
    config = AnalyzerConfig(
        project_root=Path("/tmp/analisis_proyecto_react"),
        openai_api_key=os.getenv("OPENAI_API_KEY", "tu_clave_api")
    )
    
    # Crear el analizador
    analyzer = CodeAnalyzer(config)
    
    # Analizar un archivo específico
    result = await analyzer.analyze_file(Path("/tmp/analisis_proyecto_react/src/core/config.py"))
    
    # Imprimir resultados
    print("\nResultados del análisis de archivo:")
    print(f"Archivo: {result['file_path']}")
    print(f"Sintaxis válida: {result['syntax_valid']}")
    print(f"Líneas de código: {result['loc']}")
    print("\nAnálisis AI:")
    print(result['ai_analysis'])
    
    # Analizar todo el proyecto
    print("\nAnalizando todo el proyecto...")
    project_results = await analyzer.analyze_project()
    
    print(f"\nArchivos analizados: {project_results['files_analyzed']}")
    for file_result in project_results['results']:
        print(f"\nArchivo: {file_result['file_path']}")
        print(f"Sintaxis válida: {file_result['syntax_valid']}")
        print(f"Líneas de código: {file_result['loc']}")

if __name__ == "__main__":
    asyncio.run(test_analysis())