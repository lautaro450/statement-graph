"""
Script to update imports after restructuring the project folders
"""
import os
import re

def update_file_imports(file_path):
    """Update imports in file to use the new folder structure"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Original content for comparison
    original_content = content
    
    # Update imports for helpers
    content = re.sub(
        r'from (db_connect|models|direct_connect) import', 
        r'from helpers.\1 import', 
        content
    )
    content = re.sub(
        r'import (db_connect|models|direct_connect)(\s|$)', 
        r'import helpers.\1\2', 
        content
    )
    
    # Update imports for schemas
    content = re.sub(
        r'from schemas import', 
        r'from core.schemas.schemas import', 
        content
    )
    content = re.sub(
        r'import schemas(\s|$)', 
        r'import core.schemas.schemas\1', 
        content
    )
    
    # Update imports for services
    content = re.sub(
        r'from services import', 
        r'from core.services.services import', 
        content
    )
    content = re.sub(
        r'import services(\s|$)', 
        r'import core.services.services\1', 
        content
    )
    
    # Update imports for llm_service
    content = re.sub(
        r'from llm_service import', 
        r'from core.services.llm_service import', 
        content
    )
    content = re.sub(
        r'import llm_service(\s|$)', 
        r'import core.services.llm_service\1', 
        content
    )
    
    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Update imports in all relevant files"""
    root_dir = '.'
    files_to_check = []
    
    # Files to skip
    files_to_skip = [
        'update_imports.py',
        'update_folder_imports.py', 
        'update_tests.py',
        'db_connect.py', 
        'models.py', 
        'direct_connect.py',
        'schemas.py',
        'services.py',
        'llm_service.py',
        'example.py',
        'topic_example.py'
    ]
    
    # Get all Python files
    for root, _, files in os.walk(root_dir):
        if 'venv' in root:  # Skip virtual environment
            continue
        for file in files:
            if file.endswith('.py') and file not in files_to_skip:
                files_to_check.append(os.path.join(root, file))
    
    # Update imports in all files
    updated_files = 0
    for file_path in files_to_check:
        if update_file_imports(file_path):
            print(f"Updated imports in {file_path}")
            updated_files += 1
    
    print(f"Updated {updated_files} files")

if __name__ == "__main__":
    main()
