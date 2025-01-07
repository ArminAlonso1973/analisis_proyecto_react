# src/analyzers/dependency_analyzer.py
from pathlib import Path
from typing import Dict, Set, List
import networkx as nx
import asyncio
from ..models.entities import CodeComponent, BusinessEntity, DockerService
from ..utils.llm_handler import LLMHandler

class DependencyAnalyzer:
    def __init__(self, config: 'AnalyzerConfig'):
        self.config = config
        self.llm_handler = LLMHandler(config.llm_config, config.cache_dir)
        self.dependency_graph = nx.DiGraph()
    
    async def analyze_dependencies(self,
                                 code_components: Dict[str, CodeComponent],
                                 business_entities: Dict[str, BusinessEntity],
                                 docker_services: Dict[str, DockerService]) -> nx.DiGraph:
        """Analyze project dependencies across all layers."""
        # Analyze each layer in parallel
        await asyncio.gather(
            self._analyze_code_dependencies(code_components),
            self._analyze_business_dependencies(business_entities),
            self._analyze_infrastructure_dependencies(docker_services)
        )
        
        # Cross-layer dependency analysis
        await self._analyze_cross_layer_dependencies(
            code_components, business_entities, docker_services
        )
        
        return self.dependency_graph
    
    async def _analyze_code_dependencies(self, 
                                       components: Dict[str, CodeComponent]):
        """Analyze dependencies between code components."""
        # Build initial dependency graph
        for path, component in components.items():
            self.dependency_graph.add_node(
                path,
                type='code',
                component_type=component.type,
                language=component.language
            )
            
            for dep in component.dependencies:
                self.dependency_graph.add_edge(path, dep)
        
        # Enhance with LLM analysis
        analysis_data = {
            'components': {
                path: {
                    'type': comp.type,
                    'language': comp.language,
                    'dependencies': list(comp.dependencies),
                    'metrics': comp.metrics
                }
                for path, comp in components.items()
            }
        }
        
        analysis = await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Code dependency analysis"
        )
        
        # Add discovered implicit dependencies
        for dep in analysis.get('implicit_dependencies', []):
            if dep['source'] in components and dep['target'] in components:
                self.dependency_graph.add_edge(
                    dep['source'],
                    dep['target'],
                    type='implicit',
                    reason=dep.get('reason', '')
                )
    
    async def _analyze_business_dependencies(self, 
                                          entities: Dict[str, BusinessEntity]):
        """Analyze dependencies between business entities."""
        # Add entities to graph
        for name, entity in entities.items():
            self.dependency_graph.add_node(
                f"entity:{name}",
                type='business',
                attributes=list(entity.attributes),
                methods=list(entity.methods)
            )
            
            # Add explicit dependencies
            for dep in entity.dependencies:
                self.dependency_graph.add_edge(
                    f"entity:{name}",
                    f"entity:{dep}"
                )
        
        # Enhance with LLM analysis
        analysis_data = {
            'entities': {
                name: {
                    'attributes': list(entity.attributes),
                    'methods': list(entity.methods),
                    'dependencies': list(entity.dependencies),
                    'rules': entity.rules
                }
                for name, entity in entities.items()
            }
        }
        
        analysis = await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Business entity dependency analysis"
        )
        
        # Add discovered relationships
        for rel in analysis.get('relationships', []):
            self.dependency_graph.add_edge(
                f"entity:{rel['source']}",
                f"entity:{rel['target']}",
                type=rel.get('type', 'association'),
                strength=rel.get('strength', 'normal')
            )
    
    async def _analyze_infrastructure_dependencies(self, 
                                                services: Dict[str, DockerService]):
        """Analyze dependencies between infrastructure components."""
        # Add services to graph
        for name, service in services.items():
            self.dependency_graph.add_node(
                f"service:{name}",
                type='infrastructure',
                image=service.image,
                ports=service.ports
            )
            
            # Add explicit dependencies
            for dep in service.dependencies:
                self.dependency_graph.add_edge(
                    f"service:{name}",
                    f"service:{dep}"
                )
        
        # Enhance with LLM analysis
        analysis_data = {
            'services': {
                name: {
                    'image': service.image,
                    'dependencies': list(service.dependencies),
                    'ports': service.ports,
                    'volumes': service.volumes,
                    'environment': service.environment
                }
                for name, service in services.items()
            }
        }
        
        analysis = await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Infrastructure dependency analysis"
        )
        
        # Add discovered dependencies
        for dep in analysis.get('dependencies', []):
            self.dependency_graph.add_edge(
                f"service:{dep['source']}",
                f"service:{dep['target']}",
                type=dep.get('type', 'requires'),
                protocol=dep.get('protocol', '')
            )
    
    async def _analyze_cross_layer_dependencies(self,
                                              code_components: Dict[str, CodeComponent],
                                              business_entities: Dict[str, BusinessEntity],
                                              docker_services: Dict[str, DockerService]):
        """Analyze dependencies across different architectural layers."""
        analysis_data = {
            'code': {
                path: {
                    'type': comp.type,
                    'language': comp.language,
                    'metrics': comp.metrics
                }
                for path, comp in code_components.items()
            },
            'business': {
                name: {
                    'attributes': list(entity.attributes),
                    'methods': list(entity.methods)
                }
                for name, entity in business_entities.items()
            },
            'infrastructure': {
                name: {
                    'image': service.image,
                    'ports': service.ports
                }
                for name, service in docker_services.items()
            }
        }
        
        analysis = await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Cross-layer dependency analysis"
        )
        
        # Add cross-layer dependencies
        for dep in analysis.get('cross_layer_dependencies', []):
            source = self._get_node_id(dep['source'], dep['source_type'])
            target = self._get_node_id(dep['target'], dep['target_type'])
            
            if source and target:
                self.dependency_graph.add_edge(
                    source,
                    target,
                    type='cross_layer',
                    layer_type=f"{dep['source_type']}_to_{dep['target_type']}",
                    reason=dep.get('reason', '')
                )
    
    def _get_node_id(self, name: str, node_type: str) -> Optional[str]:
        """Get node identifier based on type."""
        if node_type == 'code':
            return name
        elif node_type == 'business':
            return f"entity:{name}"
        elif node_type == 'infrastructure':
            return f"service:{name}"
        return None