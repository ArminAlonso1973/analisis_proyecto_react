# src/analyzers/code_analyzer.py
from pathlib import Path
from typing import Dict, Set, List
import asyncio
from ..models.entities import CodeComponent
from ..utils.code_parser import CodeParser
from ..utils.chunking import CodeChunker
from ..utils.llm_handler import LLMHandler

class CodeAnalyzer:
    def __init__(self, config: 'AnalyzerConfig'):
        self.config = config
        self.components: Dict[str, CodeComponent] = {}
        self.chunker = CodeChunker(config.llm_config.max_tokens)
        self.llm_handler = LLMHandler(config.llm_config, config.cache_dir)
        
    async def analyze_project(self) -> Dict[str, CodeComponent]:
        """Analyze project code structure with parallel processing."""
        analysis_tasks = []
        
        for file_path in self.config.project_root.rglob('*'):
            if self._should_analyze(file_path):
                analysis_tasks.append(self._analyze_file(file_path))
        
        # Execute analyses in parallel with controlled concurrency
        results = await asyncio.gather(*analysis_tasks)
        
        # Merge results
        for result in results:
            if result:
                self.components.update(result)
        
        # Analyze cross-component relationships
        await self._analyze_relationships()
        
        return self.components
    
    def _should_analyze(self, file_path: Path) -> bool:
        """Determine if a file should be analyzed based on configuration."""
        if not file_path.is_file():
            return False
            
        # Check against ignore patterns
        if any(pattern in str(file_path) for pattern in self.config.ignore_patterns):
            return False
            
        # Check if file extension is supported
        ext = file_path.suffix.lower()
        return any(ext in exts 
                  for exts in self.config.supported_languages.values())
    
    async def _analyze_file(self, file_path: Path) -> Dict[str, CodeComponent]:
        """Analyze a single file using both static analysis and LLM."""
        try:
            # Read file content
            with open(file_path) as f:
                content = f.read()
            
            # Static analysis
            static_analysis = self._perform_static_analysis(file_path, content)
            
            # LLM analysis for deeper insights
            llm_analysis = await self._perform_llm_analysis(file_path, content)
            
            # Merge analyses
            component = self._merge_analyses(file_path, static_analysis, llm_analysis)
            
            return {str(file_path): component}
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {}
    
    def _perform_static_analysis(self, file_path: Path, content: str) -> Dict:
        """Perform static code analysis."""
        parser = CodeParser()
        extension = file_path.suffix.lower()
        
        if extension == '.py':
            return parser.parse_python_file(content)
        elif extension in ['.js', '.jsx', '.ts', '.tsx']:
            return parser.parse_javascript_file(content)
        elif 'Dockerfile' in str(file_path):
            return parser.parse_dockerfile(content)
        else:
            return {}
    
    async def _perform_llm_analysis(self, file_path: Path, content: str) -> Dict:
        """Perform LLM-based analysis on code chunks."""
        chunks = list(self.chunker.chunk_code(content))
        context = f"File: {file_path.name}, Type: {self._determine_component_type(file_path)}"
        
        analyses = await asyncio.gather(
            *[self.llm_handler.analyze_chunk(chunk, context) for chunk in chunks]
        )
        
        # Merge chunk analyses
        merged_analysis = {}
        for analysis in analyses:
            for key, value in analysis.items():
                if key in merged_analysis:
                    if isinstance(value, list):
                        merged_analysis[key].extend(value)
                    elif isinstance(value, dict):
                        merged_analysis[key].update(value)
                else:
                    merged_analysis[key] = value
        
        return merged_analysis
    
    def _merge_analyses(self, file_path: Path, static_analysis: Dict, llm_analysis: Dict) -> CodeComponent:
        """Merge static and LLM analyses into a CodeComponent."""
        return CodeComponent(
            path=file_path,
            type=self._determine_component_type(file_path),
            language=file_path.suffix.lstrip('.'),
            complexity=self._calculate_complexity(static_analysis, llm_analysis),
            dependencies=self._extract_dependencies(static_analysis, llm_analysis),
            metrics=self._calculate_metrics(static_analysis, llm_analysis)
        )
    
    async def _analyze_relationships(self):
        """Analyze relationships between components using LLM."""
        components_data = {str(comp.path): {
            'type': comp.type,
            'dependencies': list(comp.dependencies),
            'metrics': comp.metrics
        } for comp in self.components.values()}
        
        analysis = await self.llm_handler.analyze_chunk(
            json.dumps(components_data),
            "Project component relationships"
        )
        
        # Update components with relationship information
        if 'relationships' in analysis:
            for rel in analysis['relationships']:
                if rel['source'] in self.components:
                    self.components[rel['source']].relationships[rel['target']] = rel['type']