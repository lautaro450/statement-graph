"""
Script to update imports in test files
"""
import os
import re

def update_imports(file_path):
    """Add parent directory to path in test files"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if path import already exists
    if "sys.path.insert" in content:
        return False
    
    # Add import statements if needed
    import_sys = "import sys\n" if "import sys" not in content else ""
    import_os = "import os\n" if "import os" not in content else ""
    
    # Prepare the path insert statement
    path_insert = "\n# Add parent directory to path to allow imports from parent\n"
    path_insert += "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))\n\n"
    
    # Find where to insert the path statement
    import_section_end = 0
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if i > 10 and not re.match(r'^import |^from ', line) and import_section_end == 0:
            import_section_end = i
            break
    
    # Insert imports at the top and path statement after imports
    if import_section_end > 0:
        new_content = '\n'.join(lines[:1]) + '\n'
        if import_sys:
            new_content += import_sys
        if import_os:
            new_content += import_os
        new_content += '\n'.join(lines[1:import_section_end]) + path_insert + '\n'.join(lines[import_section_end:])
    else:
        # Fallback if we can't find the import section
        new_content = content
        if not import_sys:
            new_content = "import sys\n" + new_content
        if not import_os:
            new_content = "import os\n" + new_content
        new_content = new_content.replace("import os\n", "import os\n" + path_insert)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    """Update all test files"""
    test_dir = "tests"
    updated = 0
    
    for file_name in os.listdir(test_dir):
        if file_name.startswith("test_") and file_name.endswith(".py"):
            file_path = os.path.join(test_dir, file_name)
            if update_imports(file_path):
                updated += 1
                print(f"Updated {file_path}")
    
    print(f"Updated {updated} files")

if __name__ == "__main__":
    main()
