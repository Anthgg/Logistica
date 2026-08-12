#!/usr/bin/env python3
"""
Deploy script for Google Cloud Run and Docker with version management.
Ensures every build/deployment uses a unique, explicit version tag and revision.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
CONFIG_FILE = BACKEND_DIR / "app" / "core" / "config.py"
PYPROJECT_FILE = BACKEND_DIR / "pyproject.toml"

DEFAULT_GCP_PROJECT = "gen-lang-client-0356667380"
DEFAULT_REGION = "southamerica-west1"
DEFAULT_SERVICE_NAME = "autenticacion-continua-api"
DEFAULT_REPOSITORY = "cloud-run-source-deploy"
GCLOUD_COMMAND = "gcloud.cmd" if os.name == "nt" else "gcloud"


def get_current_version() -> str:
    """Extract APP_VERSION from config.py."""
    if CONFIG_FILE.exists():
        content = CONFIG_FILE.read_text(encoding="utf-8")
        match = re.search(r'APP_VERSION:\s*str\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return "0.9.2"


def update_version_in_files(version: str) -> None:
    """Update version in config.py and pyproject.toml."""
    if CONFIG_FILE.exists():
        content = CONFIG_FILE.read_text(encoding="utf-8")
        new_content = re.sub(
            r'(APP_VERSION:\s*str\s*=\s*")[^"]+(")',
            rf"\g<1>{version}\g<2>",
            content
        )
        CONFIG_FILE.write_text(new_content, encoding="utf-8")
        print(f"[OK] Updated APP_VERSION in {CONFIG_FILE.name} to {version}")

    if PYPROJECT_FILE.exists():
        content = PYPROJECT_FILE.read_text(encoding="utf-8")
        new_content = re.sub(
            r'(version\s*=\s*")[^"]+(")',
            rf"\g<1>{version}\g<2>",
            content
        )
        PYPROJECT_FILE.write_text(new_content, encoding="utf-8")
        print(f"[OK] Updated version in {PYPROJECT_FILE.name} to {version}")


def run_command(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a shell command and print real-time output."""
    print(f"\n[RUNNING] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and deploy to Docker & Cloud Run with versioning.")
    parser.add_argument("--version", type=str, help="Specific version to build and deploy (e.g. 0.9.2)")
    parser.add_argument("--project", type=str, default=DEFAULT_GCP_PROJECT, help="GCP Project ID")
    parser.add_argument("--region", type=str, default=DEFAULT_REGION, help="GCP Region")
    parser.add_argument("--service", type=str, default=DEFAULT_SERVICE_NAME, help="Cloud Run Service Name")
    parser.add_argument("--repo", type=str, default=DEFAULT_REPOSITORY, help="Artifact Registry Repository")
    args = parser.parse_args()

    version = args.version or get_current_version()

    # Generate timestamp tag to guarantee version uniqueness
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    version_tag = f"v{version}"
    unique_build_tag = f"v{version}-{timestamp}"
    revision_suffix = f"v{version.replace('.', '-')}-{timestamp.replace('-', '')}"

    print("==================================================")
    print(f" Deploying Service:  {args.service}")
    print(f" Target Version:     {version_tag}")
    print(f" Unique Build Tag:   {unique_build_tag}")
    print(f" GCP Project:        {args.project}")
    print(f" Region:             {args.region}")
    print("==================================================")

    # 1. Update version in files
    update_version_in_files(version)

    # 2. Local Docker Build
    local_image_semver = f"{args.service}:{version_tag}"
    local_image_unique = f"{args.service}:{unique_build_tag}"
    run_command(["docker", "build", "-t", local_image_semver, "-t", local_image_unique, "."], cwd=BACKEND_DIR)

    # 3. Artifact Registry Image Target
    registry_host = f"{args.region}-docker.pkg.dev"
    remote_image_semver = f"{registry_host}/{args.project}/{args.repo}/{args.service}:{version_tag}"
    remote_image_unique = f"{registry_host}/{args.project}/{args.repo}/{args.service}:{unique_build_tag}"
    remote_image_latest = f"{registry_host}/{args.project}/{args.repo}/{args.service}:latest"

    # Configure Docker for Artifact Registry
    print("\n[INFO] Authenticating Docker with GCP Artifact Registry...")
    subprocess.run(
        [GCLOUD_COMMAND, "auth", "configure-docker", registry_host, "--quiet"],
        check=True,
    )

    # Tag remote images
    run_command(["docker", "tag", local_image_unique, remote_image_semver])
    run_command(["docker", "tag", local_image_unique, remote_image_unique])
    run_command(["docker", "tag", local_image_unique, remote_image_latest])

    # Push images
    print("\n[INFO] Pushing images to Artifact Registry...")
    run_command(["docker", "push", remote_image_semver])
    run_command(["docker", "push", remote_image_unique])
    run_command(["docker", "push", remote_image_latest])

    # 4. Deploy to Cloud Run
    print("\n[INFO] Deploying new revision to Cloud Run...")
    deploy_cmd = [
        GCLOUD_COMMAND, "run", "deploy", args.service,
        "--image", remote_image_unique,
        "--region", args.region,
        "--project", args.project,
        "--revision-suffix", revision_suffix,
        "--update-env-vars", f"APP_VERSION={version}",
        "--platform", "managed",
        "--quiet"
    ]
    run_command(deploy_cmd)

    print("\n==================================================")
    print(f" [SUCCESS] Deployment completed successfully!")
    print(f" Deployed Version: {version_tag} ({unique_build_tag})")
    print(f" Cloud Run Service: {args.service}")
    print("==================================================")


if __name__ == "__main__":
    main()
