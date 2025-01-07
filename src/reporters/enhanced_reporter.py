# src/reporters/enhanced_reporter.py
from typing import Dict, List
from pathlib import Path
import json
import asyncio
from ..models.entities import (
    CodeComponent, BusinessEntity, BusinessProcess, 
    DockerService, AnalysisReport
)
from ..utils.llm_handler import LLMHandler

class EnhancedReporter:
    def __init__(self, config: 'AnalyzerConfig'):
        self.config = config
        self.llm_handler = LLMHandler(config.llm_config, config.cache_dir)
    
    async def generate_report(self, 
                            code_components: Dict[str, CodeComponent],
                            business_entities: Dict[str, BusinessEntity],
                            business_processes: Dict[str, BusinessProcess],
                            docker_services: Dict[str, DockerService]) -> AnalysisReport:
        """Generate comprehensive analysis report with LLM-enhanced insights."""
        # Parallel analysis of different aspects
        analysis_tasks = [
            self._analyze_code_quality(code_components),
            self._analyze_business_architecture(business_entities, business_processes),
            self._analyze_deployment_architecture(docker_services),
            self._identify_risks_and_recommendations(
                code_components, business_entities, 
                business_processes, docker_services
            )
        ]
        
        code_quality, business_arch, deployment_arch, risks_and_recs = \
            await asyncio.gather(*analysis_tasks)
        
        # Combine all metrics
        metrics = {
            **code_quality.get('metrics', {}),
            **business_arch.get('metrics', {}),
            **deployment_arch.get('metrics', {})
        }
        
        return AnalysisReport(
            code_components=code_components,
            business_entities=business_entities,
            business_processes=business_processes,
            docker_services=docker_services,
            metrics=metrics,
            risks=risks_and_recs.get('risks', []),
            recommendations=risks_and_recs.get('recommendations', [])
        )
    
    async def _analyze_code_quality(self, 
                                  code_components: Dict[str, CodeComponent]) -> Dict:
        """Analyze code quality metrics and patterns."""
        analysis_data = {
            'components': {
                path: {
                    'type': comp.type,
                    'language': comp.language,
                    'complexity': comp.complexity,
                    'metrics': comp.metrics
                }
                for path, comp in code_components.items()
            }
        }
        
        return await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Code quality analysis"
        )
    
    async def _analyze_business_architecture(self,
                                          entities: Dict[str, BusinessEntity],
                                          processes: Dict[str, BusinessProcess]) -> Dict:
        """Analyze business architecture patterns and metrics."""
        analysis_data = {
            'entities': {
                name: {
                    'attributes': list(entity.attributes),
                    'methods': list(entity.methods),
                    'dependencies': list(entity.dependencies),
                    'rules': entity.rules
                }
                for name, entity in entities.items()
            },
            'processes': {
                name: {
                    'description': process.description,
                    'steps': process.steps,
                    'entities_involved': list(process.entities_involved),
                    'critical_paths': process.critical_paths
                }
                for name, process in processes.items()
            }
        }
        
        return await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Business architecture analysis"
        )
    
    async def _analyze_deployment_architecture(self,
                                            docker_services: Dict[str, DockerService]) -> Dict:
        """Analyze deployment architecture and container relationships."""
        analysis_data = {
            'services': {
                name: {
                    'image': service.image,
                    'dependencies': list(service.dependencies),
                    'volumes': service.volumes,
                    'environment': service.environment,
                    'ports': service.ports
                }
                for name, service in docker_services.items()
            }
        }
        
        return await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Deployment architecture analysis"
        )
    
    async def _identify_risks_and_recommendations(self,
                                                code_components: Dict[str, CodeComponent],
                                                business_entities: Dict[str, BusinessEntity],
                                                business_processes: Dict[str, BusinessProcess],
                                                docker_services: Dict[str, DockerService]) -> Dict:
        """Identify risks and generate recommendations across all aspects."""
        analysis_data = {
            'code_metrics': {
                path: {
                    'complexity': comp.complexity,
                    'metrics': comp.metrics
                }
                for path, comp in code_components.items()
            },
            'business_complexity': {
                'num_entities': len(business_entities),
                'num_processes': len(business_processes),
                'entity_relationships': sum(len(e.dependencies) 
                                         for e in business_entities.values()),
                'process_critical_paths': sum(len(p.critical_paths) 
                                           for p in business_processes.values())
            },
            'deployment_complexity': {
                'num_services': len(docker_services),
                'service_dependencies': sum(len(s.dependencies) 
                                         for s in docker_services.values()),
                'exposed_ports': sum(len(s.ports) 
                                   for s in docker_services.values())
            }
        }
        
        return await self.llm_handler.analyze_chunk(
            json.dumps(analysis_data),
            "Risk and recommendation analysis"
        )