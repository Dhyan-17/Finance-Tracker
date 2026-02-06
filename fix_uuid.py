#!/usr/bin/env python3
"""Fix UUID defaults in schema.sql"""

import re

def fix_uuid_defaults():
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all UUID defaults
    content = re.sub(
        r'DEFAULT \(lower\(hex\(randomblob\(16\)\)\)\)',
        '',
        content
    )

    with open('database/schema.sql', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Fixed all UUID defaults in schema.sql")

if __name__ == "__main__":
    fix_uuid_defaults()
