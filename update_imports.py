"""
Script to update imports after moving modules to helpers package
"""
import os
import re

def update_file_imports(file_path):
    """Update imports in file to use helpers package"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update imports
    updated_content = re.sub(
        r'from (db_connect|models|direct_connect) import', 
        r'from helpers.\1 import', 
        content
    )
    updated_content = re.sub(
        r'import (db_connect|models|direct_connect)(\s|$)', 
        r'import helpers.\1\2', 
        updated_content
    )
    
    # Only write if changes were made
    if content != updated_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    return False

def main():
    """Update imports in all relevant files"""
    root_dir = '.'
    files_to_check = []
    
    # Get all Python files
    for root, _, files in os.walk(root_dir):
        if 'venv' in root:  # Skip virtual environment
            continue
        for file in files:
            if file.endswith('.py') and file not in ['update_imports.py', 'db_connect.py', 'models.py', 'direct_connect.py']:
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
