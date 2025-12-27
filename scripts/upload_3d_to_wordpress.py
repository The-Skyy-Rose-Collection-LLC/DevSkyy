#!/usr/bin/env python3
"""
Upload 3D GLB models to WordPress via SFTP.

WordPress.com Business/eCommerce plans support SFTP access.
This script uploads GLB files to the uploads directory.

Usage:
    python3 scripts/upload_3d_to_wordpress.py [--collection NAME] [--dry-run]
"""

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


def get_sftp_credentials():
    """Get SFTP credentials from environment or .env file."""
    # Try environment first
    host = os.environ.get("SFTP_HOST")
    user = os.environ.get("SFTP_USERNAME")
    password = os.environ.get("SFTP_PASSWORD")

    # Load from .env if not in environment
    if not all([host, user, password]):
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key == "SFTP_HOST":
                            host = value
                        elif key == "SFTP_USERNAME":
                            user = value
                        elif key == "SFTP_PASSWORD":
                            password = value

    return host, user, password


def upload_via_sftp(
    local_path: Path, remote_path: str, host: str, user: str, password: str
) -> bool:
    """Upload a file via SFTP using sshpass."""
    try:
        # Create SFTP batch commands
        batch_file = Path("/tmp/sftp_batch.txt")
        batch_file.write_text(f"put {local_path} {remote_path}\n")

        cmd = [
            "sshpass",
            "-p",
            password,
            "sftp",
            "-oBatchMode=no",
            "-oStrictHostKeyChecking=no",
            "-b",
            str(batch_file),
            f"{user}@{host}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        batch_file.unlink(missing_ok=True)

        return result.returncode == 0
    except Exception as e:
        print(f"SFTP error: {e}")
        return False


def upload_via_scp(local_path: Path, remote_path: str, host: str, user: str, password: str) -> bool:
    """Upload a file via SCP."""
    try:
        # Check if sshpass is available
        result = subprocess.run(["which", "sshpass"], capture_output=True)
        has_sshpass = result.returncode == 0

        if has_sshpass:
            cmd = [
                "sshpass",
                "-p",
                password,
                "scp",
                "-oStrictHostKeyChecking=no",
                str(local_path),
                f"{user}@{host}:{remote_path}",
            ]
        else:
            # Will prompt for password
            cmd = [
                "scp",
                "-oStrictHostKeyChecking=no",
                str(local_path),
                f"{user}@{host}:{remote_path}",
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print(f"SCP error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload 3D models to WordPress")
    parser.add_argument("--collection", help="Specific collection to upload")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    parser.add_argument(
        "--method",
        choices=["sftp", "scp", "local"],
        default="local",
        help="Upload method (default: local)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    models_dir = project_root / "assets" / "3d-models-generated"

    print("=" * 60)
    print("3D MODEL UPLOADER FOR WORDPRESS")
    print("=" * 60)

    # Get SFTP credentials
    host, user, password = get_sftp_credentials()

    if args.method in ["sftp", "scp"] and not all([host, user, password]):
        print("\nERROR: SFTP credentials not found in .env")
        print("Required: SFTP_HOST, SFTP_USERNAME, SFTP_PASSWORD")
        return

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

    if args.method == "local":
        # Generate a manifest for local serving
        print("\n" + "=" * 60)
        print("GENERATING LOCAL MANIFEST")
        print("=" * 60)

        manifest = {
            "generated_at": datetime.now().isoformat(),
            "base_path": str(models_dir),
            "collections": {},
        }

        for name, files in collections.items():
            manifest["collections"][name] = {
                "files": [
                    {
                        "name": f.name,
                        "path": str(f),
                        "size_mb": f.stat().st_size / 1024 / 1024,
                        "url_path": f"/3d-models/{name}/{f.name}",
                    }
                    for f in files
                ]
            }

        manifest_path = models_dir / "UPLOAD_MANIFEST.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"\nManifest saved: {manifest_path}")
        print("\nTo serve locally, run:")
        print(f"  cd {models_dir}")
        print("  python3 -m http.server 8080")
        print("\nThen access models at: http://localhost:8080/<collection>/<file>.glb")

        # Also create a simple HTML viewer
        viewer_html = """<!DOCTYPE html>
<html>
<head>
    <title>SkyyRose 3D Model Viewer</title>
    <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.3.0/model-viewer.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        h1 { color: #B76E79; }
        .collection { margin: 20px 0; }
        .models { display: flex; flex-wrap: wrap; gap: 20px; }
        .model-card { background: #2a2a2a; padding: 15px; border-radius: 8px; }
        model-viewer { width: 300px; height: 300px; }
    </style>
</head>
<body>
    <h1>SkyyRose 3D Models</h1>
"""
        for name, files in collections.items():
            viewer_html += f'    <div class="collection"><h2>{name.replace("-", " ").title()}</h2><div class="models">\n'
            for f in files[:5]:  # Show first 5 per collection
                viewer_html += f"""        <div class="model-card">
            <model-viewer src="{name}/{f.name}" auto-rotate camera-controls></model-viewer>
            <p>{f.stem}</p>
        </div>\n"""
            viewer_html += "    </div></div>\n"

        viewer_html += """</body>
</html>"""

        viewer_path = models_dir / "viewer.html"
        with open(viewer_path, "w") as f:
            f.write(viewer_html)

        print(f"Viewer saved: {viewer_path}")
        return

    # SFTP/SCP upload
    print("\n" + "=" * 60)
    print(f"UPLOADING VIA {args.method.upper()}")
    print("=" * 60)

    # WordPress uploads directory path
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    remote_base = f"/wp-content/uploads/{year}/{month}/3d-models"

    results = {"success": [], "failed": []}

    for name, files in collections.items():
        print(f"\n[{name.upper()}]")
        remote_dir = f"{remote_base}/{name}"

        for f in files:
            print(f"  Uploading: {f.name}...", end=" ", flush=True)
            remote_path = f"{remote_dir}/{f.name}"

            if args.method == "sftp":
                success = upload_via_sftp(f, remote_path, host, user, password)
            else:
                success = upload_via_scp(f, remote_path, host, user, password)

            if success:
                print("OK")
                results["success"].append(str(f))
            else:
                print("FAILED")
                results["failed"].append(str(f))

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Success: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")

    if results["failed"]:
        print("\nFailed files:")
        for f in results["failed"]:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
