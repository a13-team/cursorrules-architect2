import anthropic
from pathlib import Path
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from typing import Dict, List, Optional, Union

class ClaudeAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.console = Console()

    def find_dependency_files(self, path: Union[str, Path]) -> Dict[str, Path]:
        """
        Find dependency files in the given path.
        
        Args:
            path: Directory path to search in
            
        Returns:
            Dictionary of found dependency files
        """
        path = Path(path)
        dependency_files = {}
        
        # Laravel/PHP Dependencies
        composer_files = {
            'composer.json': path / 'composer.json',
            'composer.lock': path / 'composer.lock',
            'auth.json': path / 'auth.json',
        }
        
        # Frontend Dependencies
        frontend_files = {
            'package.json': path / 'package.json',
            'package-lock.json': path / 'package-lock.json',
            'yarn.lock': path / 'yarn.lock',
        }
        
        # Build/Asset Dependencies
        build_files = {
            'webpack.mix.js': path / 'webpack.mix.js',
            'vite.config.js': path / 'vite.config.js',
            'tailwind.config.js': path / 'tailwind.config.js',
            'postcss.config.js': path / 'postcss.config.js',
        }
        
        # Check and add existing files
        for file_type, file_path in {**composer_files, **frontend_files, **build_files}.items():
            if file_path.exists():
                dependency_files[file_type] = file_path
            
        return dependency_files

    def analyze_project_dependencies(self, path: Union[str, Path]) -> Dict[str, dict]:
        """
        Analyze all dependency files found in the given path.
        
        Args:
            path: Directory path containing dependency files
            
        Returns:
            Dictionary containing analysis results for each dependency file
        """
        path = Path(path)
        if not path.exists():
            self.console.print(f"[bold red]Error: Path {path} does not exist[/bold red]")
            return {}
            
        dependency_files = self.find_dependency_files(path)
        if not dependency_files:
            self.console.print(f"[bold yellow]No dependency files (composer.json/package.json/requirements.txt) found in {path}[/bold yellow]")
            return {}
            
        analysis_results = {}
        
        for file_name, file_path in dependency_files.items():
            self.console.print(f"\n[bold blue]Found {file_name}, analyzing...[/bold blue]")
            analysis = self.analyze_dependencies(str(file_path))
            if analysis:
                analysis_results[file_name] = analysis
                # Format and display the results
                markdown = self.format_analysis_markdown(analysis, Path(file_name).suffix)
                self.console.print(Markdown(markdown))
            
        return analysis_results

    def analyze_dependencies(self, file_path: str) -> dict:
        """Analyze dependency files with Claude and return the analysis."""
        try:
            with open(file_path, 'r') as f:
                file_content = f.read()

            file_name = Path(file_path).name
            
            # Define analysis systems based on file type
            if file_name == 'composer.json':
                system = """You are a PHP/Laravel dependency analyzer. Output ONLY in this exact JSON format:
{
    "php_dependencies": [
        {
            "name": "package-name",
            "current_version": "version-constraint",
            "latest_version": "latest-available",
            "type": "require/require-dev",
            "is_latest": boolean,
            "is_security_risk": boolean,
            "description": "brief package description"
        }
    ],
    "metadata": {
        "total_packages": number,
        "outdated_count": number,
        "security_issues": number,
        "php_version": "version-constraint",
        "laravel_version": "version-constraint",
        "analysis_date": "YYYY-MM-DD"
    }
}"""
                prompt = f"Analyze PHP/Laravel dependencies from this composer.json:\n\n{file_content}"
                
            elif file_name == 'package.json':
                system = """You are a frontend dependency analyzer for Laravel projects. Output ONLY in this exact JSON format:
{
    "dependencies": [
        {
            "name": "package-name",
            "current_version": "version-specified",
            "latest_version": "latest-available",
            "type": "dependency/devDependency",
            "is_latest": boolean,
            "is_security_risk": boolean,
            "category": "framework/ui/build/test"
        }
    ],
    "metadata": {
        "total_packages": number,
        "outdated_count": number,
        "security_issues": number,
        "node_version": "version-specified",
        "analysis_date": "YYYY-MM-DD"
    }
}"""
                prompt = f"Analyze frontend dependencies from this package.json:\n\n{file_content}"
                
            elif file_name in ['webpack.mix.js', 'vite.config.js']:
                system = """You are a Laravel build configuration analyzer. Output ONLY in this exact JSON format:
{
    "build_config": {
        "tool": "webpack/vite",
        "entry_points": ["list-of-entry-points"],
        "output_paths": ["list-of-output-paths"],
        "plugins": [
            {
                "name": "plugin-name",
                "purpose": "brief-description"
            }
        ]
    },
    "metadata": {
        "total_plugins": number,
        "uses_typescript": boolean,
        "uses_sass": boolean,
        "uses_postcss": boolean,
        "analysis_date": "YYYY-MM-DD"
    }
}"""
                prompt = f"Analyze build configuration from {file_name}:\n\n{file_content}"
                
            else:
                system = """You are a dependency file analyzer. Output ONLY in this exact JSON format:
{
    "file_analysis": {
        "file_type": "file-type",
        "purpose": "file-purpose",
        "dependencies": [
            {
                "name": "dependency-name",
                "version": "version-info",
                "type": "dependency-type"
            }
        ]
    },
    "metadata": {
        "total_entries": number,
        "analysis_date": "YYYY-MM-DD"
    }
}"""
                prompt = f"Analyze dependency information from {file_name}:\n\n{file_content}"

            self.console.print(f"\n[bold blue]Starting analysis with Claude-3-5-sonnet-20241022 for {Path(file_path).name}...[/bold blue]")
            
            # Initialize response accumulator
            full_response = ""
            current_content = ""
            
            # Create a live display for the streaming output
            with Live(Panel("Analyzing...", title="Claude-3-5-sonnet-20241022 Analysis", border_style="blue"), refresh_per_second=4) as live:
                with self.client.messages.stream(
                    max_tokens=1024,
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
                            live.update(Panel("Starting analysis...", title="Claude-3-5-sonnet-20241022 Analysis", border_style="blue"))
                        elif event.type == "content_block_start":
                            current_content = ""
                        elif event.type == "content_block_delta":
                            if event.delta.type == "text_delta":
                                text = event.delta.text
                                current_content += text
                                full_response += text
                                # Update the live display with the current content
                                live.update(Panel(current_content, title="Claude-3-5-sonnet-20241022 Analysis", border_style="blue"))
                        elif event.type == "content_block_stop":
                            # Content block is complete
                            pass
                        elif event.type == "message_delta":
                            if event.delta.stop_reason:
                                live.update(Panel("Analysis complete!", title="Claude-3-5-sonnet-20241022 Analysis", border_style="green"))
                        elif event.type == "message_stop":
                            # Message is complete
                            pass
                        elif event.type == "error":
                            error_msg = f"Error: {event.error.message}"
                            live.update(Panel(error_msg, title="Error", border_style="red"))
                            raise Exception(error_msg)

            try:
                # Parse the JSON response
                analysis = json.loads(full_response)
                return analysis
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw response in a structured format
                return {
                    "raw_analysis": full_response,
                    "error": "Could not parse response as JSON"
                }

        except FileNotFoundError:
            self.console.print(f"[bold red]Error: {Path(file_path).name} not found[/bold red]")
            return None
        except Exception as e:
            self.console.print(f"[bold red]Error during analysis: {str(e)}[/bold red]")
            return None

    def format_analysis_markdown(self, analysis: dict, file_type: str) -> str:
        """Convert the analysis to a nicely formatted markdown string."""
        if not analysis:
            return "\n\n## Dependency Analysis\nError during analysis."
            
        if "raw_analysis" in analysis:
            return f"\n\n## Dependency Analysis\n\n{analysis['raw_analysis']}"

        md = "\n\n## Dependency Analysis\n\n"
        
        if "php_dependencies" in analysis:  # composer.json
            md += f"### PHP/Laravel Dependencies\n"
            md += f"Analysis Date: {analysis['metadata']['analysis_date']}\n"
            md += f"PHP Version: `{analysis['metadata']['php_version']}`\n"
            md += f"Laravel Version: `{analysis['metadata']['laravel_version']}`\n\n"
            
            md += f"Total Packages: {analysis['metadata']['total_packages']}\n"
            md += f"Outdated Packages: {analysis['metadata']['outdated_count']}\n"
            md += f"Security Issues: {analysis['metadata']['security_issues']}\n\n"
            
            for pkg in analysis['php_dependencies']:
                status = "🔴" if pkg['is_security_risk'] else "✅" if pkg['is_latest'] else "⚠️"
                md += f"{status} **{pkg['name']}** ({pkg['type']})\n"
                md += f"  - Current: `{pkg['current_version']}`\n"
                md += f"  - Latest: `{pkg['latest_version']}`\n"
                md += f"  - {pkg['description']}\n\n"
                
        elif "dependencies" in analysis:  # package.json
            md += f"### Frontend Dependencies\n"
            md += f"Analysis Date: {analysis['metadata']['analysis_date']}\n"
            md += f"Node Version: `{analysis['metadata']['node_version']}`\n\n"
            
            md += f"Total Packages: {analysis['metadata']['total_packages']}\n"
            md += f"Outdated Packages: {analysis['metadata']['outdated_count']}\n"
            md += f"Security Issues: {analysis['metadata']['security_issues']}\n\n"
            
            # Group by category
            categories = {}
            for pkg in analysis['dependencies']:
                if pkg['category'] not in categories:
                    categories[pkg['category']] = []
                categories[pkg['category']].append(pkg)
            
            for category, packages in categories.items():
                md += f"#### {category.title()}\n"
                for pkg in packages:
                    status = "🔴" if pkg['is_security_risk'] else "✅" if pkg['is_latest'] else "⚠️"
                    md += f"{status} **{pkg['name']}** ({pkg['type']})\n"
                    md += f"  - Current: `{pkg['current_version']}`\n"
                    md += f"  - Latest: `{pkg['latest_version']}`\n\n"
                    
        elif "build_config" in analysis:  # webpack.mix.js/vite.config.js
            md += f"### Build Configuration\n"
            md += f"Tool: {analysis['build_config']['tool']}\n\n"
            
            md += "#### Entry Points\n"
            for entry in analysis['build_config']['entry_points']:
                md += f"- {entry}\n"
            
            md += "\n#### Plugins\n"
            for plugin in analysis['build_config']['plugins']:
                md += f"- **{plugin['name']}**: {plugin['purpose']}\n"
            
            md += f"\n#### Features\n"
            md += f"- TypeScript: {'✅' if analysis['metadata']['uses_typescript'] else '❌'}\n"
            md += f"- Sass: {'✅' if analysis['metadata']['uses_sass'] else '❌'}\n"
            md += f"- PostCSS: {'✅' if analysis['metadata']['uses_postcss'] else '❌'}\n"
        
        return md

    def analyze_directory_structure(self, tree_content: str) -> dict:
        """Analyze directory structure and provide file descriptions."""
        system = """You are a code structure analyzer. For each file in the directory tree, provide a brief (max 50 chars) 
        description of its purpose based on its name and location. Output in this exact JSON format:
        {
            "file_descriptions": {
                "path/to/file.ext": "Brief description of file purpose",
                "another/path/file.ext": "Another brief description"
            }
        }
        Exclude directories and focus only on files."""
        
        prompt = f"Analyze this directory tree and provide brief descriptions for each file:\n\n{tree_content}"
        
        self.console.print("\n[bold blue]Analyzing directory structure with Claude-3-5-sonnet-20241022...[/bold blue]")
        
        full_response = ""
        current_content = ""
        
        with Live(Panel("Analyzing directory structure...", title="Claude-3-5-sonnet-20241022 Analysis", border_style="blue"), refresh_per_second=4) as live:
            with self.client.messages.stream(
                max_tokens=1024,
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
                        live.update(Panel("Starting analysis...", title="Claude-3-5-sonnet-20241022 Analysis", border_style="blue"))
                    elif event.type == "content_block_start":
                        current_content = ""
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            text = event.delta.text
                            current_content += text
                            full_response += text
                            # Update the live display with the current content
                            live.update(Panel(current_content, title="Claude-3-5-sonnet-20241022 Analysis", border_style="blue"))
                    elif event.type == "content_block_stop":
                        # Content block is complete
                        pass
                    elif event.type == "message_delta":
                        if event.delta.stop_reason:
                            live.update(Panel("Analysis complete!", title="Claude-3-5-sonnet-20241022 Analysis", border_style="green"))
                    elif event.type == "message_stop":
                        # Message is complete
                        pass
                    elif event.type == "error":
                        error_msg = f"Error: {event.error.message}"
                        live.update(Panel(error_msg, title="Error", border_style="red"))
                        raise Exception(error_msg)

        try:
            return json.loads(full_response)
        except json.JSONDecodeError:
            return {"file_descriptions": {}}

if __name__ == "__main__":
    analyzer = ClaudeAnalyzer()
    # Example usage with path
    analyzer.analyze_project_dependencies(".")
    