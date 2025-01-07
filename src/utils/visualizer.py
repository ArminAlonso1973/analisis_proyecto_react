from typing import Dict, List
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pathlib import Path

class ProjectVisualizer:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_dependency_graph(self, dependency_graph: nx.DiGraph,
                                output_format: str = 'html') -> Path:
        """Generate visual representation of dependency graph."""
        if output_format == 'html':
            return self._generate_interactive_graph(dependency_graph)
        else:
            return self._generate_static_graph(dependency_graph)
    
    def _generate_interactive_graph(self, graph: nx.DiGraph) -> Path:
        """Generate interactive HTML visualization using Plotly."""
        # Prepare node positions using NetworkX layout
        pos = nx.spring_layout(graph, k=1, iterations=50)
        
        # Create node traces by type
        node_traces = {}
        for node, data in graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            if node_type not in node_traces:
                node_traces[node_type] = go.Scatter(
                    x=[], y=[],
                    mode='markers+text',
                    name=node_type,
                    text=[],
                    hoverinfo='text',
                    marker=dict(size=20)
                )
            
            x, y = pos[node]
            node_traces[node_type].x += (x,)
            node_traces[node_type].y += (y,)
            node_traces[node_type].text += (node,)
        
        # Create edge trace
        edge_x = []
        edge_y = []
        edge_text = []
        
        for edge in graph.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_text.append(edge[2].get('type', 'unknown'))
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='text',
            text=edge_text,
            mode='lines'
        )
        
        # Create figure
        fig = go.Figure(
            data=[edge_trace] + list(node_traces.values()),
            layout=go.Layout(
                title='Project Dependencies',
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        
        # Save to file
        output_path = self.output_dir / 'dependency_graph.html'
        fig.write_html(str(output_path))
        return output_path
    
    def _generate_static_graph(self, graph: nx.DiGraph) -> Path:
        """Generate static visualization using Matplotlib."""
        plt.figure(figsize=(15, 10))
        
        # Create layout
        pos = nx.spring_layout(graph)
        
        # Draw nodes by type
        node_colors = {
            'code': 'lightblue',
            'business': 'lightgreen',
            'infrastructure': 'lightcoral'
        }
        
        for node_type, color in node_colors.items():
            nodes = [n for n, d in graph.nodes(data=True)
                    if d.get('type') == node_type]
            nx.draw_networkx_nodes(graph, pos,
                                 nodelist=nodes,
                                 node_color=color,
                                 node_size=1000)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, edge_color='gray', arrows=True)
        
        # Add labels
        labels = {node: node for node in graph.nodes()}
        nx.draw_networkx_labels(graph, pos, labels)
        
        # Save to file
        output_path = self.output_dir / 'dependency_graph.png'
        plt.savefig(output_path)
        plt.close()
        return output_path
    
    def generate_metrics_dashboard(self, metrics: Dict) -> Path:
        """Generate dashboard visualization of project metrics."""
        fig = go.Figure()
        
        # Add metrics by category
        categories = {
            'Code Quality': ['complexity', 'maintainability', 'test_coverage'],
            'Business Logic': ['num_entities', 'num_processes', 'process_complexity'],
            'Infrastructure': ['num_services', 'deployment_complexity']
        }
        
        for category, metric_keys in categories.items():
            values = [metrics.get(key, 0) for key in metric_keys]
            fig.add_trace(go.Bar(
                name=category,
                x=metric_keys,
                y=values,
                text=values,
                textposition='auto',
            ))
        
        # Update layout
        fig.update_layout(
            title='Project Metrics Dashboard',
            barmode='group',
            xaxis_title='Metrics',
            yaxis_title='Values'
        )
        
        # Save to file
        output_path = self.output_dir / 'metrics_dashboard.html'
        fig.write_html(str(output_path))
        return output_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze software project')
    parser.add_argument('project_path', help='Path to project root directory')
    parser.add_argument('--openai-key', help='OpenAI API key')
    parser.add_argument('--depth', choices=['basic', 'full', 'deep'],
                       default='full', help='Analysis depth')
    
    args = parser.parse_args()
    
    # Run analysis
    asyncio.run(analyze_project(
        args.project_path,
        args.openai_key,
        args.depth
    ))