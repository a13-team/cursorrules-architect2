#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from typing import List, Set, Dict
from datetime import datetime
import fnmatch
from collections import defaultdict

# Default exclusion sets
DEFAULT_EXCLUDE_DIRS = {
    'node_modules', '__pycache__', '.next', 'build', 'dist',
    'coverage', '.pytest_cache', '.sass-cache', '.turbo',
    'out', '.output', '.nuxt', '.cache', '.parcel-cache',
    'vendor', 'tmp', 'temp', '.temp', '.idea', '.vscode',
    'venv', '.venv', 'env', '.env', '.tox', 'eggs',
    '.mypy_cache', '.ruff_cache', '.pytest_cache',
    'htmlcov', '.coverage', '.hypothesis', '.git',
    'bootstrap/cache',  # Laravel cache
    'storage/framework',  # Laravel framework storage
    'storage/logs',      # Laravel logs
    'storage/app',       # Laravel app storage
}

DEFAULT_EXCLUDE_PATTERNS = {
    '*.svg', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.webp',  # Images
    '*.lock', '*.log',  # Lock and log files
    '*.map', '*.min.js', '*.min.css',  # Generated/minified files
    '*.woff', '*.woff2', '*.ttf', '*.eot',  # Fonts
    '*.mp4', '*.webm', '*.ogg', '*.mp3', '*.wav',  # Media files
    '*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx',  # Documents
    '*.pyc', '*.pyo', '*.pyd',  # Python compiled files
    '.DS_Store',  # System files
    'LICENSE', 'LICENSE.*',  # License files
    '.cursorrules',  # Cursor rules output
    '.gitignore',  # Git ignore
    '.dockerignore',  # Docker ignore
    '*.cache',          # Cache files
    '*.hot-update.js',  # Webpack hot updates
    '*.hot-update.json', # Webpack hot updates
    '*.phpunit.result.cache', # PHPUnit cache
    'mix-manifest.json',  # Laravel Mix manifest
    'yarn-error.log',    # Yarn errors
    'npm-debug.log',     # NPM debug
    '.phpstorm.meta.php', # PHPStorm meta
    '_ide_helper.php',    # IDE helper
    '.php_cs.cache',     # PHP CS Fixer cache
}

# File type emojis
FILE_ICONS: Dict[str, str] = {
    # Programming Languages
    '.py': '🐍',    # Python
    '.js': '📜',    # JavaScript
    '.jsx': '⚛️',    # React
    '.ts': '💠',    # TypeScript
    '.tsx': '⚛️',    # React TypeScript
    '.html': '🌐',   # HTML
    '.php': '🐘',    # PHP
    '.blade.php': '🔪',    # Blade PHP
    '.test.php': '🧪',    # PHP Test files
    '.spec.php': '🧪',    # PHP Spec files
    '.css': '🎨',    # CSS
    '.scss': '🎨',   # SCSS
    '.sass': '🎨',   # SASS
    '.less': '🎨',   # LESS
    '.json': '📋',   # JSON
    '.xml': '📋',    # XML
    '.yaml': '📋',   # YAML
    '.yml': '📋',    # YML
    '.md': '📝',     # Markdown
    '.txt': '📄',    # Text
    '.sh': '🐚',     # Shell
    '.bash': '🐚',   # Bash
    '.zsh': '🐚',    # Zsh
    '.env': '🔒',    # Environment
    'Dockerfile': '🐳',    # Dockerfile
    'docker-compose.yml': '🐳',  # Docker compose
    'package.json': '📦',  # Package JSON
    'requirements.txt': '📦',  # Python requirements
    'README': '��',        # README
    'artisan': '⚡',      # Laravel Artisan
    'composer.json': '📦',  # Composer
    'composer.lock': '📦',  # Composer lock
    '.env.example': '🔒',   # Environment example
    'phpunit.xml': '🧪',    # PHPUnit config
    'webpack.mix.js': '🔄',  # Laravel Mix
    'vite.config.js': '⚡',  # Vite config
    'tailwind.config.js': '🎨', # Tailwind config
}

# File type descriptions for the key
ICON_DESCRIPTIONS = {
    '📁': 'Directory',
    '🐍': 'Python',
    '📜': 'JavaScript',
    '⚛️': 'React',
    '💠': 'TypeScript',
    '🌐': 'HTML',
    '🐘': 'PHP',
    '🔪': 'Blade PHP',
    '🧪': 'Test file',
    '🎨': 'CSS/SCSS/SASS',
    '📋': 'Data file (JSON/YAML/XML)',
    '📝': 'Markdown',
    '📄': 'Text file',
    '🐚': 'Shell script',
    '🔒': 'Environment file',
    '📦': 'Package file',
    '📖': 'README',
    '🐳': 'Docker file',
    '⚡': 'Build/Config file',
    '🔄': 'Build process',
    '️': 'Error/Warning'
}

def get_file_icon(path: Path) -> str:
    """Get the appropriate emoji icon for a file."""
    if path.is_dir():
        return '📁'
    
    # Check for exact filename matches first
    if path.name in FILE_ICONS:
        return FILE_ICONS[path.name]
    
    # Then check extensions
    ext = path.suffix.lower()
    if ext in FILE_ICONS:
        return FILE_ICONS[ext]
    
    # Default file icon
    return '📄'

def should_exclude(item: Path, exclude_dirs: Set[str], exclude_patterns: Set[str]) -> bool:
    """
    Check if an item should be excluded based on directory name or file pattern.
    
    Args:
        item: Path object to check
        exclude_dirs: Set of directory names to exclude
        exclude_patterns: Set of file patterns to exclude
    
    Returns:
        bool: True if item should be excluded, False otherwise
    """
    # Check if it's a directory in the exclude list
    if item.is_dir() and (item.name in exclude_dirs):
        return True
        
    # Check file patterns
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(item.name.lower(), pattern.lower()):
            return True
            
    return False

def generate_tree(
    path: str,
    prefix: str = "",
    exclude_dirs: Set[str] = None,
    exclude_patterns: Set[str] = None
) -> List[str]:
    """
    Generate a tree structure of the specified directory path.
    
    Args:
        path: The directory path to generate tree for
        prefix: Current prefix for the tree line (used for recursion)
        exclude_dirs: Set of directory names to exclude
        exclude_patterns: Set of patterns to exclude (e.g., "*.pyc")
    
    Returns:
        List of strings representing the tree structure
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    if exclude_patterns is None:
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS
        
    tree = []
    path = Path(path)
    
    try:
        # Get all items in the directory
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        
        # Filter out excluded items
        items = [item for item in items if not should_exclude(item, exclude_dirs, exclude_patterns)]
        
        # Process each item
        for index, item in enumerate(items):
            is_last = index == len(items) - 1
            connector = "└── " if is_last else "├── "
            
            # Add the current item to the tree with its icon
            icon = get_file_icon(item)
            tree.append(f"{prefix}{connector}{icon} {item.name}")
            
            # If it's a directory, recursively process its contents
            if item.is_dir():
                extension = "    " if is_last else "│   "
                tree.extend(
                    generate_tree(
                        item,
                        prefix + extension,
                        exclude_dirs,
                        exclude_patterns
                    )
                )
    except PermissionError:
        tree.append(f"{prefix}└── ⚠️ <Permission Denied>")
    except Exception as e:
        tree.append(f"{prefix}└── ⚠️ <Error: {str(e)}>")
    
    return tree

def generate_key(tree_content: List[str]) -> List[str]:
    """Generate a key of emojis used in the tree."""
    used_icons = set()
    
    # Extract all emojis used in the tree
    for line in tree_content:
        # Find emoji in the line (emojis are between connector and filename)
        parts = line.split(' ')
        for part in parts:
            if any(icon in part for icon in ICON_DESCRIPTIONS):
                used_icons.add(part.strip())
    
    if not used_icons:
        return []
        
    # Generate key lines
    key_lines = [
        "File Type Key:",
        "------------"
    ]
    
    # Add descriptions for used icons
    for icon in sorted(used_icons):
        if icon in ICON_DESCRIPTIONS:
            key_lines.append(f"{icon} : {ICON_DESCRIPTIONS[icon]}")
    
    return key_lines + [""]  # Add empty line after key

def save_tree_to_file(tree_content: List[str], path: str) -> str:
    """
    Save the tree structure to a .cursorrules file.
    
    Args:
        tree_content: List of strings containing the tree structure
        path: The directory path that was processed
    
    Returns:
        The path to the saved file
    """
    output_file = Path(path) / ".cursorrules"
    
    # Generate key for used icons
    key = generate_key(tree_content)
    
    header = [
        "<!-- BEGIN_STRUCTURE -->",
        "# Project Directory Structure",
        "------------------------------"
    ]
    
    if key:  # Only add key if there are icons used
        header.extend(key)
    
    header.append("```")
    
    footer = [
        "```",
        "<!-- END_STRUCTURE -->"
    ]
    
    with output_file.open('w', encoding='utf-8') as f:
        f.write('\n'.join(header + tree_content + footer))
    
    return str(output_file)

def main():
    parser = argparse.ArgumentParser(description='Generate a directory tree structure.')
    parser.add_argument('path', nargs='?', default='.',
                       help='Path to generate tree for (default: current directory)')
    parser.add_argument('--exclude-dirs', nargs='+', default=None,
                       help='Additional directories to exclude')
    parser.add_argument('--exclude-patterns', nargs='+', default=None,
                       help='Additional patterns to exclude (e.g., *.pyc)')
    parser.add_argument('--show-excluded', action='store_true',
                       help='Show what files and directories are being excluded')
    
    args = parser.parse_args()
    
    # Combine default and custom exclusions if provided
    exclude_dirs = DEFAULT_EXCLUDE_DIRS.union(set(args.exclude_dirs or []))
    exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.union(set(args.exclude_patterns or []))
    
    if args.show_excluded:
        print("\nExcluded Directories:")
        print('\n'.join(f"- {d}" for d in sorted(exclude_dirs)))
        print("\nExcluded Patterns:")
        print('\n'.join(f"- {p}" for p in sorted(exclude_patterns)))
        print()
    
    # Generate and print the tree
    path = os.path.abspath(args.path)
    print(f"\nDirectory Tree for: {path}\n")
    
    tree = generate_tree(path, exclude_dirs=exclude_dirs, exclude_patterns=exclude_patterns)
    
    # Generate and print key
    key = generate_key(tree)
    if key:
        print('\n'.join(key))
    
    # Print tree
    print('\n'.join(tree))
    
    # Save to .cursorrules file
    output_file = save_tree_to_file(tree, path)
    print(f"\nTree structure saved to: {output_file}")

if __name__ == '__main__':
    main()
        
