import os
import glob

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
html_files = [os.path.join(frontend_dir, 'index.html')] + sorted(glob.glob(os.path.join(frontend_dir, 'pages', '*.html')))

favicon_block = """    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/assets/images/favicon.svg">
    <link rel="icon" type="image/x-icon" href="/assets/images/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/assets/images/apple-touch-icon.png">
"""

updated = []
for fpath in html_files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    if '/assets/images/favicon.svg' in content:
        print(f"Skipping (already present): {os.path.basename(fpath)}")
        continue

    # Insert before <!-- CSS or before first <link rel="stylesheet"
    if '<!-- CSS' in content:
        pos = content.find('<!-- CSS')
        new_content = content[:pos] + favicon_block + '    ' + content[pos:]
    elif '<link rel="stylesheet"' in content:
        pos = content.find('<link rel="stylesheet"')
        new_content = content[:pos] + favicon_block + '    ' + content[pos:]
    elif '</head>' in content:
        pos = content.find('</head>')
        new_content = content[:pos] + favicon_block + content[pos:]
    else:
        print(f"Warning: No head or link tag in {fpath}")
        continue

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    updated.append(os.path.relpath(fpath, frontend_dir))

print(f"\nSuccessfully updated {len(updated)} HTML files with favicon link tags:")
for u in updated:
    print(f" - {u}")
