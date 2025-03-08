#!/usr/bin/env python3
import anthropic
from pathlib import Path
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from rich.tree import Tree
from typing import Dict, List, Set, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProjectComponent:
    """Represents a component of the project that needs analysis."""
    path: str
    type: str  # 'dependency', 'code', 'test', 'doc', 'config', etc.
    priority: int  # 1-5, with 1 being highest priority
    agent: str  # Which agent should handle this
    description: str

class ProjectArchitectAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.console = Console()
        
        # Define known file patterns and their analyzers
        self.file_patterns = {
            'dependencies': {
                'patterns': [
                    # PHP/Laravel Dependencies
                    'composer.json',
                    'composer.lock',
                    'package.json',
                    'package-lock.json',
                    'yarn.lock',
                    'auth.json',
                ],
                'agent': 'dependency_analyzer_agent',
                'priority': 1
            },
            'tests': {
                'patterns': [
                    # Laravel Tests
                    'tests/Feature/*.php',
                    'tests/Unit/*.php',
                    'tests/Browser/*.php',  # Laravel Dusk
                    'tests/Integration/*.php',
                    '*Test.php',
                    '*Spec.php',
                    'phpunit.xml',
                    '.env.testing',
                    'tests/CreatesApplication.php',
                    'tests/TestCase.php',
                ],
                'agent': 'test_analyzer_agent',
                'priority': 2
            },
            'documentation': {
                'patterns': [
                    '*.md',
                    'docs/*',
                    'README*',
                    'CONTRIBUTING*',
                    'resources/docs/*',
                    'resources/views/docs/*',
                    'phpDocumentor.xml',
                ],
                'agent': 'documentation_analyzer_agent',
                'priority': 2
            },
            'configuration': {
                'patterns': [
                    # Laravel Config Files
                    'config/*.php',
                    '.env*',
                    'phpunit.xml',
                    'artisan',
                    'webpack.mix.js',
                    'vite.config.js',
                    'tailwind.config.js',
                    'postcss.config.js',
                    '.htaccess',
                    'server.php',
                    'routes/*.php',
                    'bootstrap/app.php',
                    'bootstrap/cache/*.php',
                    '.styleci.yml',
                    '.php-cs-fixer.php',
                    '.php_cs',
                    '.php_cs.dist',
                    'docker-compose.yml',
                    'Dockerfile',
                    'nginx.conf',
                ],
                'agent': 'config_analyzer_agent',
                'priority': 1
            },
            'source_code': {
                'patterns': [
                    # Laravel Source Code
                    'app/*.php',
                    'app/**/*.php',
                    'database/migrations/*.php',
                    'database/seeders/*.php',
                    'database/factories/*.php',
                    'resources/views/**/*.blade.php',
                    'resources/js/**/*.js',
                    'resources/js/**/*.ts',
                    'resources/js/**/*.vue',
                    'resources/css/**/*.css',
                    'resources/sass/**/*.scss',
                    'routes/*.php',
                    'app/Http/Controllers/*.php',
                    'app/Http/Middleware/*.php',
                    'app/Models/*.php',
                    'app/Providers/*.php',
                    'app/Services/*.php',
                    'app/Repositories/*.php',
                    'app/Console/Commands/*.php',
                    'app/Jobs/*.php',
                    'app/Events/*.php',
                    'app/Listeners/*.php',
                    'app/Notifications/*.php',
                    'app/Policies/*.php',
                    'app/Rules/*.php',
                ],
                'agent': 'code_analyzer_agent',
                'priority': 1
            },
            'security': {
                'patterns': [
                    # Security-sensitive files
                    '.env*',
                    'config/auth.php',
                    'config/security.php',
                    'config/cors.php',
                    'config/sanctum.php',
                    'config/session.php',
                    'app/Http/Middleware/Authenticate.php',
                    'app/Http/Middleware/VerifyCsrfToken.php',
                    'routes/api.php',
                    'config/database.php',
                ],
                'agent': 'security_analyzer_agent',
                'priority': 1
            },
            'database': {
                'patterns': [
                    # Database related files
                    'database/migrations/*.php',
                    'database/seeders/*.php',
                    'database/factories/*.php',
                    'config/database.php',
                    'storage/database.sqlite',
                ],
                'agent': 'database_analyzer_agent',
                'priority': 2
            },
            'assets': {
                'patterns': [
                    # Asset files
                    'public/js/*.js',
                    'public/css/*.css',
                    'public/images/*',
                    'public/fonts/*',
                    'resources/js/**/*',
                    'resources/css/**/*',
                    'resources/sass/**/*',
                    'resources/assets/**/*',
                ],
                'agent': 'asset_analyzer_agent',
                'priority': 3
            }
        }

    def analyze_tree_structure(self, tree_content: str) -> Dict[str, List[ProjectComponent]]:
        """
        Analyze the tree structure and categorize components for different agents.
        """
        system = """You are a project architecture analyzer. Given a directory tree, categorize files into components that should be analyzed by different specialized agents. 
        Output ONLY in this exact JSON format:
        {
            "components": [
                {
                    "path": "path/to/file",
                    "type": "component_type",
                    "priority": priority_number,
                    "agent": "agent_name",
                    "description": "brief description of what needs analysis"
                }
            ],
            "metadata": {
                "total_components": number,
                "priority_distribution": {
                    "high": number,
                    "medium": number,
                    "low": number
                },
                "analysis_date": "YYYY-MM-DD"
            }
        }
        
        Component types: dependency, code, test, doc, config
        Priority levels: 1 (highest) to 5 (lowest)
        Agents: dependency_analyzer_agent, test_analyzer_agent, documentation_analyzer_agent, config_analyzer_agent, code_analyzer_agent
        """
        
        prompt = f"""Analyze this directory tree and categorize components for specialized analysis:

        Rules:
        1. Group related files that should be analyzed together
        2. Prioritize core functionality and dependencies
        3. Consider file relationships and dependencies
        4. Identify configuration that affects multiple components
        5. Flag security-sensitive files for priority analysis

        Tree:
        {tree_content}
        """
        
        self.console.print("\n[bold blue]Analyzing project structure with Claude 3.5 Sonnet 20241022...[/bold blue]")
        
        full_response = ""
        current_content = ""
        
        with Live(Panel("Analyzing project structure...", title="Claude-3-5-sonnet-20241022 Analysis", border_style="blue"), refresh_per_second=4) as live:
            with self.client.messages.stream(
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model="claude-3-7-sonnet-20250219",
                system=system,
                temperature=0.0
            ) as stream:
                for event in stream:
                    if event.type == "message_start":
                        live.update(Panel("Starting analysis...", title="Claude 3.5 Sonnet 20241022 Analysis", border_style="blue"))
                    elif event.type == "content_block_start":
                        current_content = ""
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            text = event.delta.text
                            current_content += text
                            full_response += text
                            live.update(Panel(current_content, title="Claude-3 Analysis", border_style="blue"))
                    elif event.type == "message_delta":
                        if event.delta.stop_reason:
                            live.update(Panel("Analysis complete!", title="Claude-3 Analysis", border_style="green"))

        try:
            analysis = json.loads(full_response)
            return self._organize_components(analysis)
        except json.JSONDecodeError:
            self.console.print("[bold red]Error parsing Claude's response[/bold red]")
            return {}

    def _organize_components(self, analysis: dict) -> Dict[str, List[ProjectComponent]]:
        """Organize analyzed components by agent."""
        organized = {}
        
        for component in analysis.get('components', []):
            agent = component.get('agent')
            if agent not in organized:
                organized[agent] = []
            
            organized[agent].append(ProjectComponent(
                path=component['path'],
                type=component['type'],
                priority=component['priority'],
                agent=agent,
                description=component['description']
            ))
        
        # Sort each agent's components by priority
        for agent in organized:
            organized[agent].sort(key=lambda x: x.priority)
        
        return organized

    def format_analysis_markdown(self, organized_components: Dict[str, List[ProjectComponent]], metadata: dict) -> str:
        """Format the analysis results as markdown."""
        md = "# Project Analysis Plan\n\n"
        
        # Add metadata section
        md += "## Analysis Overview\n"
        md += f"- Analysis Date: {metadata['analysis_date']}\n"
        md += f"- Total Components: {metadata['total_components']}\n"
        md += "\nPriority Distribution:\n"
        md += f"- High Priority: {metadata['priority_distribution']['high']}\n"
        md += f"- Medium Priority: {metadata['priority_distribution']['medium']}\n"
        md += f"- Low Priority: {metadata['priority_distribution']['low']}\n\n"
        
        # Add components by agent
        for agent, components in organized_components.items():
            md += f"## {agent.replace('_', ' ').title()}\n"
            
            # Group by priority
            for priority in range(1, 6):
                priority_components = [c for c in components if c.priority == priority]
                if priority_components:
                    md += f"\n### Priority {priority}\n"
                    for comp in priority_components:
                        md += f"- `{comp.path}` ({comp.type})\n"
                        md += f"  - {comp.description}\n"
            
            md += "\n"
        
        return md

    def display_results(self, organized_components: Dict[str, List[ProjectComponent]], metadata: dict):
        """Display the analysis results in a rich tree format."""
        tree = Tree("🎯 Project Analysis Plan")
        
        # Add metadata
        meta_branch = tree.add("📊 Analysis Overview")
        meta_branch.add(f"Date: {metadata['analysis_date']}")
        meta_branch.add(f"Total Components: {metadata['total_components']}")
        
        priority_branch = meta_branch.add("Priority Distribution")
        priority_branch.add(f"High: {metadata['priority_distribution']['high']}")
        priority_branch.add(f"Medium: {metadata['priority_distribution']['medium']}")
        priority_branch.add(f"Low: {metadata['priority_distribution']['low']}")
        
        # Add components by agent
        for agent, components in organized_components.items():
            agent_branch = tree.add(f"🤖 {agent.replace('_', ' ').title()}")
            
            # Group by priority
            for priority in range(1, 6):
                priority_components = [c for c in components if c.priority == priority]
                if priority_components:
                    priority_branch = agent_branch.add(f"Priority {priority}")
                    for comp in priority_components:
                        comp_node = priority_branch.add(f"`{comp.path}` ({comp.type})")
                        comp_node.add(comp.description)
        
        self.console.print(tree)

def main():
    # Example usage
    architect = ProjectArchitectAgent()
    
    try:
        import sys
        from pathlib import Path
        
        # Add the project root to Python path
        project_root = Path(__file__).parent.parent
        sys.path.append(str(project_root))
        
        # Import the tree generator
        from utils.project_doc_generator import generate_tree
        
        # Generate the tree
        tree_content = generate_tree(".")
        if not tree_content:
            print("Error: Could not generate tree structure")
            return
            
        # Convert tree list to string
        tree_str = "\n".join(tree_content)
        
        # Analyze the tree
        analysis = architect.analyze_tree_structure(tree_str)
        
        # Display results
        architect.display_results(analysis, {
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "total_components": sum(len(comps) for comps in analysis.values()),
            "priority_distribution": {
                "high": sum(1 for comps in analysis.values() for c in comps if c.priority <= 2),
                "medium": sum(1 for comps in analysis.values() for c in comps if c.priority == 3),
                "low": sum(1 for comps in analysis.values() for c in comps if c.priority >= 4)
            }
        })
        
    except ImportError as e:
        print(f"Error importing project_doc_generator: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 