#!/usr/bin/env python3
"""
Clean up ugly www.* folder names and update all internal links.
"""
import os
import re
import subprocess
import glob

REPO = "/mnt/c/Users/Administrator/code/case-outcomes"

# Mapping: old_folder_name -> new_slug
FOLDER_MAP = {
    "www.austlii.edu.au": "austlii",
    "www.bailii.org": "bailii",
    "www.commonlii.org": "commonlii",
    "www.cylaw.org": "cylaw",
    "www.droit.org": "droit",
    "www.glin.gov": "glin",
    "www.hklii.org": "hklii",
    "www.irlii.org": "irlii",
    "www.jura.uni-saarland.de": "jura-uni-saarland",
    "www.law.cornell.edu": "law-cornell",
    "www.lawphil.net": "lawphil",
    "www.lawreform.go.th": "lawreform",
    "www.legalabbrevs.cardiff.ac.uk": "legalabbrevs-cardiff",
    "www.nzlii.org": "nzlii",
    "www.paclii.org": "paclii",
    "www.saflii.org": "saflii",
    "www.ulii.org": "ulii",
    "www.unsw.edu.au": "unsw",
    "www.uts.edu.au": "uts",
    "www.worldlii.org": "worldlii",
}

def find_html_files():
    """Find all .html files in the repo."""
    files = []
    for root, dirs, fnames in os.walk(REPO):
        if '.git' in root:
            continue
        for f in fnames:
            if f.endswith('.html'):
                files.append(os.path.join(root, f))
    return files

def update_links_in_file(filepath, stats):
    """Update all internal href/src links in an HTML file to use new folder names."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    changes_made = []

    # For each folder mapping, replace occurrences that appear as PATH components
    # (not preceded by :// which would mean it's a full external URL)
    for old_name, new_name in FOLDER_MAP.items():
        # Pattern: old_name appearing after a path separator (/, .., or at start of href)
        # We need to catch: /www.xxx, ../www.xxx, "./www.xxx
        # But NOT: https://www.xxx, http://www.xxx
        
        # Strategy: find all occurrences of old_name in href/src attribute values
        # that are NOT preceded by ://
        
        # Simple approach: replace in href="/... and href="../... and src="/... and src="../...
        # These are unambiguous path references
        
        # Pattern 1: href="/www.xxx -> href="/xxx
        count = content.count(f'href="/{old_name}')
        if count > 0:
            content = content.replace(f'href="/{old_name}', f'href="/{new_name}')
            changes_made.append(f'href=/{old_name} -> /{new_name} ({count}x)')

        # Pattern 2: src="/www.xxx -> src="/xxx
        count = content.count(f'src="/{old_name}')
        if count > 0:
            content = content.replace(f'src="/{old_name}', f'src="/{new_name}')
            changes_made.append(f'src=/{old_name} -> /{new_name} ({count}x)')

        # Pattern 3: href="../...www.xxx -> href="../...xxx (any depth of ../)
        # Use regex: href="(\.\./)+www.xxx -> href="\1xxx
        pattern = re.compile(r'(href="(?:\.\./)+)' + re.escape(old_name))
        count = len(pattern.findall(content))
        if count > 0:
            content = pattern.sub(r'\1' + new_name, content)
            changes_made.append(f'href=../{old_name} -> ../{new_name} ({count}x)')

        # Pattern 4: src="../...www.xxx -> src="../...xxx (any depth of ../)
        pattern = re.compile(r'(src="(?:\.\./)+)' + re.escape(old_name))
        count = len(pattern.findall(content))
        if count > 0:
            content = pattern.sub(r'\1' + new_name, content)
            changes_made.append(f'src=../{old_name} -> ../{new_name} ({count}x)')

        # Pattern 5: action="/www.xxx -> action="/xxx (for forms)
        count = content.count(f'action="/{old_name}')
        if count > 0:
            content = content.replace(f'action="/{old_name}', f'action="/{new_name}')
            changes_made.append(f'action=/{old_name} -> /{new_name} ({count}x)')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        relpath = os.path.relpath(filepath, REPO)
        stats['files_updated'] += 1
        for c in changes_made:
            stats['changes'].append(f"  {relpath}: {c}")
        print(f"  UPDATED: {relpath}")
        for c in changes_made:
            print(f"    {c}")
    else:
        stats['files_skipped'] += 1

def rename_folders():
    """Use git mv to rename all folders."""
    os.chdir(REPO)
    for old_name, new_name in FOLDER_MAP.items():
        old_path = os.path.join(REPO, old_name)
        new_path = os.path.join(REPO, new_name)
        if os.path.isdir(old_path) and not os.path.exists(new_path):
            result = subprocess.run(
                ['git', 'mv', old_path, new_path],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  RENAMED: {old_name} -> {new_name}")
            else:
                print(f"  FAILED: {old_name} -> {new_name}: {result.stderr}")

def main():
    print("=" * 60)
    print("STEP 1: Scan all HTML files for references to update")
    print("=" * 60)
    
    html_files = find_html_files()
    print(f"Found {len(html_files)} HTML files to check.")

    stats = {'files_updated': 0, 'files_skipped': 0, 'changes': []}

    print("\n" + "=" * 60)
    print("STEP 2: Update internal links in all HTML files")
    print("=" * 60)
    
    for f in html_files:
        update_links_in_file(f, stats)

    print(f"\n\nSUMMARY:")
    print(f"  Files updated: {stats['files_updated']}")
    print(f"  Files skipped (no changes): {stats['files_skipped']}")

    print("\n" + "=" * 60)
    print("STEP 3: Rename folders with git mv")
    print("=" * 60)
    
    rename_folders()

    print("\n" + "=" * 60)
    print("ALL DONE!")
    print("=" * 60)

if __name__ == '__main__':
    main()
