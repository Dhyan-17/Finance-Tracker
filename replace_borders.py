import os
import re

def replace_borders_in_file(filepath):
    """Replace all '-' with '%' in box borders within a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern to match box borders: lines starting with '+' followed by '-' and ending with '+'
        # We need to be careful not to replace '-' in other contexts
        lines = content.split('\n')
        modified_lines = []

        for line in lines:
            # Check if this is a box border line (contains only '+', '-' and possibly spaces)
            stripped = line.strip()
            if stripped.startswith('+') and stripped.endswith('+') and all(c in '+- ' for c in stripped):
                # Replace '-' with '%' in the border
                modified_line = line.replace('-', '%')
                modified_lines.append(modified_line)
            else:
                modified_lines.append(line)

        new_content = '\n'.join(modified_lines)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"Processed: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    """Process all Python files in the Finance-Tracker directory"""
    for root, dirs, files in os.walk('Finance-Tracker'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                replace_borders_in_file(filepath)

if __name__ == "__main__":
    main()
