import json
import re
import os
from datetime import datetime
from collections import defaultdict

def parse_version(v):
    """Parse version string into a tuple for comparison."""
    parts = []
    for part in re.split(r'(\d+)', v):
        if part.isdigit():
            parts.append((0, int(part))) # Use tuple (0, int) for numbers
        elif part and part not in ['.', '-']:
            parts.append((1, part)) # Use tuple (1, str) for strings
    return tuple(parts)

def main():
    # Read current packages from dynamically generated file
    with open('current_packages.json', 'r') as f:
        current_packages = json.load(f)
    
    # Read releases
    with open('releases.json', 'r') as f:
        releases = json.load(f)

    # Group releases by binary name
    packages = defaultdict(list)
    for release in releases:
        tag = release['tagName']
        name = release.get('name', '')

        # Extract binary name and version from tag (e.g., "gemini-1.2.3")
        match = re.match(r'^(.+?)-v?(\d+(?:\.\d+)*.*)$', tag)
        if match:
            binary = match.group(1)
            version = match.group(2)
            
            # Use publishedAt if available, otherwise createdAt
            date_str = release.get('publishedAt') or release.get('createdAt')
            created_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Extract package name from release title (e.g. "@scope/pkg v1.2.3")
            package_match = re.match(r'^(.+) v\d', name)
            package_name = package_match.group(1) if package_match else binary

            packages[binary].append({
                'version': version,
                'created_at': created_at,
                'tag': tag,
                'package_name': package_name
            })

    # Sort versions by version number (descending)
    for binary in packages:
        packages[binary].sort(key=lambda x: parse_version(x['version']), reverse=True)

    # Generate markdown table
    table = "## Package Status\n\n"
    table += "| Package | Binary | Version | Date | Status | Download |\n"
    table += "|---------|--------|---------|------|--------|----------|\n"

    for binary in sorted(packages.keys()):
        latest_release = packages[binary][0]
        
        # Check if package is still in current matrix
        is_active = binary in current_packages
        package_name = latest_release['package_name']
        
        release_date = latest_release['created_at'].strftime('%Y-%m-%d')
        
        # Use environment variable for repo name
        repo = os.environ.get('GITHUB_REPOSITORY')
        download_url = f"https://github.com/{repo}/releases/download/{latest_release['tag']}/{binary}"
        
        status_badge = "![Active](https://img.shields.io/badge/status-active-brightgreen)" if is_active else "![Deprecated](https://img.shields.io/badge/status-deprecated-red)"
        
        table += f"| {package_name} | `{binary}` | {latest_release['version']} | {release_date} | {status_badge} | [Download]({download_url}) |\n"

    # Read current README
    with open('README.md', 'r') as f:
        readme = f.read()

    # Replace or append the status table
    marker_start = "<!-- STATUS_TABLE_START -->"
    marker_end = "<!-- STATUS_TABLE_END -->"
    
    if marker_start in readme and marker_end in readme:
        # Replace existing table
        start_idx = readme.find(marker_start)
        end_idx = readme.find(marker_end) + len(marker_end)
        updated_readme = readme[:start_idx] + f"{marker_start}\n{table}\n{marker_end}" + readme[end_idx:]
    else:
        # Append table
        updated_readme = readme.rstrip() + f"\n\n{marker_start}\n{table}\n{marker_end}\n"

    # Write updated README
    with open('README.md', 'w') as f:
        f.write(updated_readme)

    print("README.md updated successfully!")

if __name__ == '__main__':
    main()
