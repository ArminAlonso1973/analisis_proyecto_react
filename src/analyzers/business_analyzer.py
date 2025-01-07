# src/analyzers/business_analyzer.py
from pathlib import Path
from typing import Dict, List, Set
import asyncio
from ..models.entities import BusinessEntity, BusinessProcess
from ..utils.chunking import CodeChunker
from ..utils.llm_handler import LLMHandler

class BusinessAnalyzer:
    def __init__(self, config: 'AnalyzerConfig'):
        self.config = config
        self.chunker = CodeChunker(config.llm_config.max_tokens)
        self.llm_handler = LLMHandler(config.llm_config, config.cache_dir)
        self.entities: Dict[str, BusinessEntity] = {}
        self.processes: Dict[str, BusinessProcess] = {}
    
    async def analyze_business_logic(self) -> tuple[Dict, Dict]:
        """Analyze project's business logic using layered approach."""
        # Define analysis layers
        layers = {
            'models': (r'models/.*\.py$', 'Domain model analysis'),
            'services': (r'services/.*\.py$', 'Business service analysis'),
            'controllers': (r'controllers/.*\.py$', 'Controller/API analysis'),
            'views': (r'views/.*\.(py|js|jsx|ts|tsx)$', 'View/UI analysis')
        }
        
        # Analyze each layer concurrently
        analyses = await asyncio.gather(
            *[self._analyze_layer(layer, pattern, context) 
              for layer, (pattern, context) in layers.items()]
        )
        
        # Merge layer analyses
        for layer_analysis in analyses:
            self._merge_layer_analysis(layer_analysis)
        
        # Perform cross-layer analysis
        await self._analyze_cross_layer_relationships()
        
        return self.entities, self.processes
    
    async def _analyze_layer(self, layer: str, pattern: str, context: str) -> Dict:
        """Analyze a specific architectural layer."""
        files = [f for f in self.config.project_root.rglob('*')
                if self._matches_pattern(f, pattern)]
        
        analyses = await asyncio.gather(
            *[self._analyze_file(f, layer, context) for f in files]
        )
        
        return self._merge_file_analyses(analyses)
    
    def _matches_pattern(self, file_path: Path, pattern: str) -> bool:
        """Check if file matches pattern and is in supported languages."""
        if not file_path.is_file():
            return False
            
        if any(p in str(file_path) for p in self.config.ignore_patterns):
            return False
            
        return bool(re.search(pattern, str(file_path)))
    
    async def _analyze_file(self, file_path: Path, layer: str, context: str) -> Dict:
        """Analyze a single file for business logic."""
        try:
            with open(file_path) as f:
                content = f.read()
            
            chunks = list(self.chunker.chunk_code(content))
            file_context = f"{context} - File: {file_path.name}"
            
            analyses = await asyncio.gather(
                *[self.llm_handler.analyze_chunk(chunk, file_context) 
                  for chunk in chunks]
            )
            
            return self._merge_chunk_analyses(analyses, file_path)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {}
    
    def _merge_chunk_analyses(self, analyses: List[Dict], file_path: Path) -> Dict:
        """Merge analyses from different chunks of the same file."""
        merged = {
            'entities': [],
            'processes': [],
            'relationships': [],
            'rules': []
        }
        
        seen_entities = set()
        seen_processes = set()
        
        for analysis in analyses:
            # Merge entities
            for entity in analysis.get('entities', []):
                if entity['name'] not in seen_entities:
                    seen_entities.add(entity['name'])
                    merged['entities'].append(entity)
            
            # Merge processes
            for process in analysis.get('processes', []):
                if process['name'] not in seen_processes:
                    seen_processes.add(process['name'])
                    merged['processes'].append(process)
                    merged['relationships'].extend(analysis.get('relationships', []))
            merged['rules'].extend(analysis.get('rules', []))
        
        merged['source_file'] = file_path
        return merged
    
    def _merge_file_analyses(self, analyses: List[Dict]) -> Dict:
        """Merge analyses from different files in the same layer."""
        merged = {
            'entities': {},
            'processes': {},
            'relationships': [],
            'rules': []
        }
        
        for analysis in analyses:
            # Merge entities
            for entity in analysis.get('entities', []):
                name = entity['name']
                if name not in merged['entities']:
                    merged['entities'][name] = entity
                    merged['entities'][name]['source_files'] = {analysis['source_file']}
                else:
                    self._merge_entity(merged['entities'][name], entity)
                    merged['entities'][name]['source_files'].add(analysis['source_file'])
            
            # Merge processes
            for process in analysis.get('processes', []):
                name = process['name']
                if name not in merged['processes']:
                    merged['processes'][name] = process
                else:
                    self._merge_process(merged['processes'][name], process)
            
            # Add relationships and rules
            merged['relationships'].extend(analysis.get('relationships', []))
            merged['rules'].extend(analysis.get('rules', []))
        
        return merged
    
    def _merge_entity(self, existing: Dict, new: Dict):
        """Merge two versions of the same business entity."""
        existing['attributes'].update(new.get('attributes', []))
        existing['methods'].update(new.get('methods', []))
        existing['relationships'].extend(new.get('relationships', []))
        existing['rules'].extend(new.get('rules', []))
    
    def _merge_process(self, existing: Dict, new: Dict):
        """Merge two versions of the same business process."""
        # Update description if new one is more detailed
        if len(new.get('description', '')) > len(existing['description']):
            existing['description'] = new['description']
        
        # Merge steps maintaining order
        existing_steps = set(existing['steps'])
        existing['steps'].extend([s for s in new.get('steps', [])
                                if s not in existing_steps])
        
        # Update entities involved
        existing['entities_involved'].update(new.get('entities_involved', []))
        
        # Merge critical paths
        existing['critical_paths'].extend(new.get('critical_paths', []))
    
    async def _analyze_cross_layer_relationships(self):
        """Analyze relationships between entities and processes across layers."""
        # Prepare data for cross-layer analysis
        analysis_data = {
            'entities': {name: self._prepare_entity_data(entity)
                        for name, entity in self.entities.items()},
            'processes': {name: self._prepare_process_data(process)
                         for name, process in self.processes.items()}
        }
        
        # Perform cross-layer analysis using LLM
        analysis = await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Cross-layer business logic analysis"
        )
        
        # Update entities and processes with cross-layer insights
        self._update_with_cross_layer_analysis(analysis)
    
    def _prepare_entity_data(self, entity: BusinessEntity) -> Dict:
        """Prepare entity data for cross-layer analysis."""
        return {
            'name': entity.name,
            'attributes': list(entity.attributes),
            'methods': list(entity.methods),
            'dependencies': list(entity.dependencies),
            'source_files': [str(p) for p in entity.source_files]
        }
    
    def _prepare_process_data(self, process: BusinessProcess) -> Dict:
        """Prepare process data for cross-layer analysis."""
        return {
            'name': process.name,
            'description': process.description,
            'steps': process.steps,
            'entities_involved': list(process.entities_involved),
            'entry_points': list(process.entry_points),
            'exit_points': list(process.exit_points)
        }
    
    def _update_with_cross_layer_analysis(self, analysis: Dict):
        """Update entities and processes with cross-layer analysis insights."""
        # Update entity relationships
        for entity_rel in analysis.get('entity_relationships', []):
            source = entity_rel['source']
            target = entity_rel['target']
            if source in self.entities and target in self.entities:
                self.entities[source].dependencies.add(target)
        
        # Update process relationships
        for process_rel in analysis.get('process_relationships', []):
            source = process_rel['source']
            target = process_rel['target']
            if source in self.processes and target in self.processes:
                self.processes[source].dependencies.add(target)
        
        # Update critical paths
        for process_name, paths in analysis.get('critical_paths', {}).items():
            if process_name in self.processes:
                self.processes[process_name].critical_paths = paths