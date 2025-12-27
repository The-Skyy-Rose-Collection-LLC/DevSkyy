#!/usr/bin/env python3
"""
Upload 3D GLB models to GitHub Releases.

This creates a release and uploads GLB files as release assets.
Files are then accessible via:
  https://github.com/OWNER/REPO/releases/download/TAG/filename.glb

Usage:
    export GITHUB_TOKEN="ghp_..."
    python3 scripts/upload_3d_to_github.py [--collection NAME] [--dry-run]
"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


def run_gh_command(args: list) -> tuple[bool, str]:
    """Run a gh CLI command and return success status and output."""
    try:
        result = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=300)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Upload 3D models to GitHub Releases")
    parser.add_argument("--collection", help="Specific collection to upload")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    parser.add_argument("--tag", default=None, help="Release tag (default: 3d-models-YYYYMMDD)")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    models_dir = project_root / "assets" / "3d-models-generated"

    print("=" * 60)
    print("GITHUB RELEASES 3D MODEL UPLOADER")
    print("=" * 60)

    # Check gh CLI
    success, output = run_gh_command(["--version"])
    if not success:
        print("\nERROR: GitHub CLI (gh) not found or not authenticated")
        print("Install: brew install gh")
        print("Auth: gh auth login")
        return

    # Check authentication
    success, output = run_gh_command(["auth", "status"])
    if not success:
        print("\nERROR: Not authenticated with GitHub")
        print("Run: gh auth login")
        return

    print("GitHub CLI authenticated")

    # Find all GLB files
    collections = {}
    if args.collection:
        coll_dir = models_dir / args.collection
        if coll_dir.exists():
            collections[args.collection] = list(coll_dir.glob("*.glb"))
    else:
        for coll_dir in models_dir.iterdir():
            if coll_dir.is_dir():
                glb_files = list(coll_dir.glob("*.glb"))
                if glb_files:
                    collections[coll_dir.name] = glb_files

    total_files = sum(len(files) for files in collections.values())
    total_size = sum(f.stat().st_size for files in collections.values() for f in files)

    print(f"\nFound {total_files} GLB files ({total_size / 1024 / 1024:.1f} MB)")
    for name, files in collections.items():
        size = sum(f.stat().st_size for f in files) / 1024 / 1024
        print(f"  {name}: {len(files)} files ({size:.1f} MB)")

    if args.dry_run:
        print("\n[DRY RUN] No files uploaded.")
        return

    # Create release tag
    tag = args.tag or f"3d-models-{datetime.now().strftime('%Y%m%d')}"
    release_title = f"3D Models - {datetime.now().strftime('%Y-%m-%d')}"
    release_notes = """# SkyyRose 3D Models

Automatically generated 3D models for the SkyyRose fashion collections.

## Collections
"""
    for name, files in collections.items():
        size = sum(f.stat().st_size for f in files) / 1024 / 1024
        release_notes += f"- **{name}**: {len(files)} models ({size:.1f} MB)\n"

    release_notes += f"""
## Usage

Models are in GLB format and can be viewed with:
- [model-viewer](https://modelviewer.dev/) web component
- Any 3D software supporting GLB/glTF

## URLs

Access models at:
```
https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/releases/download/{tag}/<filename>.glb
```

Generated: {datetime.now().isoformat()}
"""

    print("\n" + "=" * 60)
    print(f"CREATING RELEASE: {tag}")
    print("=" * 60)

    # Check if release exists
    success, output = run_gh_command(["release", "view", tag])
    if success:
        print(f"Release {tag} already exists. Uploading additional assets...")
    else:
        # Create new release
        print(f"Creating release: {tag}")
        success, output = run_gh_command(
            ["release", "create", tag, "--title", release_title, "--notes", release_notes]
        )
        if not success:
            print(f"Failed to create release: {output}")
            return
        print("Release created!")

    # Upload files
    print("\n" + "=" * 60)
    print("UPLOADING FILES")
    print("=" * 60)

    results = {"success": [], "failed": []}
    upload_urls = {}

    for name, files in collections.items():
        print(f"\n[{name.upper()}]")
        upload_urls[name] = []

        for f in files:
            # Create unique filename with collection prefix
            f"{name}_{f.name}".replace(" ", "_")
            print(f"  {f.name}...", end=" ", flush=True)

            success, output = run_gh_command(
                ["release", "upload", tag, str(f), "--clobber"]  # Overwrite if exists
            )

            if success:
                print("OK")
                results["success"].append(str(f))
                url = f"https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/releases/download/{tag}/{f.name.replace(' ', '%20')}"
                upload_urls[name].append({"name": f.name, "url": url})
            else:
                print(f"FAILED: {output[:100]}")
                results["failed"].append(str(f))

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Success: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")

    # Save URL manifest
    manifest = {
        "release_tag": tag,
        "uploaded_at": datetime.now().isoformat(),
        "base_url": f"https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/releases/download/{tag}",
        "collections": upload_urls,
    }

    manifest_path = models_dir / "GITHUB_RELEASE_URLS.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nURL manifest saved: {manifest_path}")
    print(
        f"\nRelease URL: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/releases/tag/{tag}"
    )


if __name__ == "__main__":
    main()
