#!/usr/bin/env python3
"""
Automated WordPress Theme Uploader & Deployment System
Enterprise-grade theme deployment with multiple upload methods and validation
"""

import asyncio
import ftplib
import paramiko
import requests
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import base64
import hashlib

from monitoring.enterprise_logging import enterprise_logger, LogCategory


class UploadMethod(Enum):
    """Supported upload methods."""

    FTP = "ftp"
    SFTP = "sftp"
    WORDPRESS_REST_API = "wordpress_rest_api"
    DIRECT_FILE_SYSTEM = "direct_file_system"
    STAGING_AREA = "staging_area"


class DeploymentStatus(Enum):
    """Deployment status levels."""

    PENDING = "pending"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    ACTIVATING = "activating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class WordPressCredentials:
    """WordPress site credentials."""

    site_url: str
    username: str
    password: str
    application_password: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_username: Optional[str] = None
    ftp_password: Optional[str] = None
    sftp_host: Optional[str] = None
    sftp_username: Optional[str] = None
    sftp_private_key: Optional[str] = None


@dataclass
class ThemePackage:
    """Theme package information."""

    name: str
    version: str
    description: str
    author: str
    package_path: str
    files: List[str] = field(default_factory=list)
    size_bytes: int = 0
    checksum: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DeploymentResult:
    """Deployment result information."""

    success: bool
    deployment_id: str
    status: DeploymentStatus
    theme_package: ThemePackage
    upload_method: UploadMethod
    deployed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_available: bool = False
    validation_results: Dict[str, Any] = field(default_factory=dict)


class AutomatedThemeUploader:
    """
    Enterprise-grade automated WordPress theme uploader with multiple
    deployment methods, validation, and rollback capabilities.
    """

    def __init__(self):
        self.deployment_history = []
        self.active_deployments = {}
        self.staging_area = Path("staging/themes")
        self.staging_area.mkdir(parents=True, exist_ok=True)

        # Theme validation rules
        self.validation_rules = {
            "required_files": ["style.css", "index.php", "functions.php"],
            "recommended_files": ["screenshot.png", "readme.txt"],
            "max_size_mb": 50,
            "allowed_extensions": [
                ".php",
                ".css",
                ".js",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".svg",
                ".woff",
                ".woff2",
                ".ttf",
                ".eot",
            ],
        }

        enterprise_logger.info("Automated theme uploader initialized", category=LogCategory.SYSTEM)

    async def create_theme_package(self, theme_path: str, theme_info: Dict[str, Any]) -> ThemePackage:
        """Create a deployable theme package."""
        try:
            theme_path_obj = Path(theme_path)

            if not theme_path_obj.exists():
                raise FileNotFoundError(f"Theme path not found: {theme_path}")

            # Create package info
            package = ThemePackage(
                name=theme_info.get("name", theme_path_obj.name),
                version=theme_info.get("version", "1.0.0"),
                description=theme_info.get("description", ""),
                author=theme_info.get("author", "DevSkyy Platform"),
                package_path="",
            )

            # Create ZIP package
            package_filename = f"{package.name}-{package.version}.zip"
            package_path = self.staging_area / package_filename

            with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in theme_path_obj.rglob("*"):
                    if file_path.is_file():
                        # Skip hidden files and cache
                        if file_path.name.startswith(".") or "__pycache__" in str(file_path):
                            continue

                        arcname = file_path.relative_to(theme_path_obj)
                        zipf.write(file_path, arcname)
                        package.files.append(str(arcname))

            # Calculate package info
            package.package_path = str(package_path)
            package.size_bytes = package_path.stat().st_size
            package.checksum = self._calculate_checksum(package_path)

            enterprise_logger.info(
                f"Theme package created: {package.name}",
                category=LogCategory.SYSTEM,
                metadata={
                    "version": package.version,
                    "size_mb": round(package.size_bytes / 1024 / 1024, 2),
                    "files_count": len(package.files),
                },
            )

            return package

        except Exception as e:
            enterprise_logger.error(f"Failed to create theme package: {e}", category=LogCategory.SYSTEM, error=e)
            raise

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    async def validate_theme_package(self, package: ThemePackage) -> Dict[str, Any]:
        """Validate theme package before deployment."""
        validation_results = {"valid": True, "errors": [], "warnings": [], "info": []}

        try:
            # Check package exists
            if not Path(package.package_path).exists():
                validation_results["errors"].append("Package file not found")
                validation_results["valid"] = False
                return validation_results

            # Check package size
            size_mb = package.size_bytes / 1024 / 1024
            if size_mb > self.validation_rules["max_size_mb"]:
                validation_results["errors"].append(
                    f"Package too large: {size_mb:.1f}MB (max: {self.validation_rules['max_size_mb']}MB)"
                )
                validation_results["valid"] = False

            # Extract and validate contents
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(package.package_path, "r") as zipf:
                    zipf.extractall(temp_dir)

                temp_path = Path(temp_dir)

                # Check required files
                for required_file in self.validation_rules["required_files"]:
                    if not any(f.name == required_file for f in temp_path.rglob(required_file)):
                        validation_results["errors"].append(f"Missing required file: {required_file}")
                        validation_results["valid"] = False

                # Check recommended files
                for recommended_file in self.validation_rules["recommended_files"]:
                    if not any(f.name == recommended_file for f in temp_path.rglob(recommended_file)):
                        validation_results["warnings"].append(f"Missing recommended file: {recommended_file}")

                # Validate style.css header
                style_css = temp_path / "style.css"
                if style_css.exists():
                    with open(style_css, "r", encoding="utf-8") as f:
                        content = f.read(1000)  # Read first 1000 chars
                        if "Theme Name:" not in content:
                            validation_results["warnings"].append("style.css missing Theme Name header")
                        if "Version:" not in content:
                            validation_results["warnings"].append("style.css missing Version header")

                # Check file extensions
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        if file_path.suffix not in self.validation_rules["allowed_extensions"]:
                            validation_results["warnings"].append(
                                f"Unusual file extension: {file_path.suffix} ({file_path.name})"
                            )

            validation_results["info"].append(f"Package size: {size_mb:.1f}MB")
            validation_results["info"].append(f"Files count: {len(package.files)}")

            enterprise_logger.info(
                f"Theme package validation completed: {package.name}",
                category=LogCategory.SYSTEM,
                metadata={
                    "valid": validation_results["valid"],
                    "errors": len(validation_results["errors"]),
                    "warnings": len(validation_results["warnings"]),
                },
            )

            return validation_results

        except Exception as e:
            validation_results["errors"].append(f"Validation error: {str(e)}")
            validation_results["valid"] = False

            enterprise_logger.error(f"Theme validation failed: {e}", category=LogCategory.SYSTEM, error=e)

            return validation_results

    async def deploy_theme(
        self,
        package: ThemePackage,
        credentials: WordPressCredentials,
        upload_method: UploadMethod = UploadMethod.WORDPRESS_REST_API,
        activate_theme: bool = False,
    ) -> DeploymentResult:
        """Deploy theme package to WordPress site."""
        deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{package.name}"

        result = DeploymentResult(
            success=False,
            deployment_id=deployment_id,
            status=DeploymentStatus.PENDING,
            theme_package=package,
            upload_method=upload_method,
        )

        try:
            # Add to active deployments
            self.active_deployments[deployment_id] = result

            enterprise_logger.info(
                f"Starting theme deployment: {package.name}",
                category=LogCategory.SYSTEM,
                metadata={"deployment_id": deployment_id, "method": upload_method.value, "site": credentials.site_url},
            )

            # Validate package first
            validation_results = await self.validate_theme_package(package)
            result.validation_results = validation_results

            if not validation_results["valid"]:
                result.status = DeploymentStatus.FAILED
                result.error_message = f"Validation failed: {validation_results['errors']}"
                return result

            # Deploy based on method
            result.status = DeploymentStatus.UPLOADING

            if upload_method == UploadMethod.WORDPRESS_REST_API:
                success = await self._deploy_via_rest_api(package, credentials, activate_theme)
            elif upload_method == UploadMethod.FTP:
                success = await self._deploy_via_ftp(package, credentials)
            elif upload_method == UploadMethod.SFTP:
                success = await self._deploy_via_sftp(package, credentials)
            elif upload_method == UploadMethod.STAGING_AREA:
                success = await self._deploy_to_staging(package, credentials)
            else:
                raise ValueError(f"Unsupported upload method: {upload_method}")

            if success:
                result.success = True
                result.status = DeploymentStatus.COMPLETED
                result.deployed_at = datetime.now()
                result.rollback_available = True

                enterprise_logger.info(
                    f"Theme deployment successful: {package.name}",
                    category=LogCategory.SYSTEM,
                    metadata={"deployment_id": deployment_id},
                )
            else:
                result.status = DeploymentStatus.FAILED
                result.error_message = "Deployment method returned failure"

        except Exception as e:
            result.status = DeploymentStatus.FAILED
            result.error_message = str(e)

            enterprise_logger.error(
                f"Theme deployment failed: {e}",
                category=LogCategory.SYSTEM,
                error=e,
                metadata={"deployment_id": deployment_id},
            )

        finally:
            # Add to history and remove from active
            self.deployment_history.append(result)
            self.active_deployments.pop(deployment_id, None)

        return result

    async def _deploy_via_rest_api(
        self, package: ThemePackage, credentials: WordPressCredentials, activate_theme: bool = False
    ) -> bool:
        """Deploy theme via WordPress REST API."""
        try:
            # Prepare authentication
            auth_header = base64.b64encode(
                f"{credentials.username}:{credentials.application_password or credentials.password}".encode()
            ).decode()

            headers = {"Authorization": f"Basic {auth_header}", "Content-Type": "application/zip"}

            # Upload theme
            upload_url = f"{credentials.site_url.rstrip('/')}/wp-json/wp/v2/themes"

            with open(package.package_path, "rb") as f:
                response = requests.post(upload_url, headers=headers, data=f.read(), timeout=300)

            if response.status_code in [200, 201]:
                enterprise_logger.info(f"Theme uploaded via REST API: {package.name}", category=LogCategory.SYSTEM)

                # Activate theme if requested
                if activate_theme:
                    await self._activate_theme_via_api(package.name, credentials)

                return True
            else:
                enterprise_logger.error(
                    f"REST API upload failed: {response.status_code} - {response.text}", category=LogCategory.SYSTEM
                )
                return False

        except Exception as e:
            enterprise_logger.error(f"REST API deployment error: {e}", category=LogCategory.SYSTEM, error=e)
            return False

    async def _deploy_via_ftp(self, package: ThemePackage, credentials: WordPressCredentials) -> bool:
        """Deploy theme via FTP."""
        try:
            if not credentials.ftp_host:
                raise ValueError("FTP credentials not provided")

            # Extract theme to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(package.package_path, "r") as zipf:
                    zipf.extractall(temp_dir)

                # Connect to FTP
                with ftplib.FTP(credentials.ftp_host) as ftp:
                    ftp.login(credentials.ftp_username, credentials.ftp_password)

                    # Navigate to themes directory
                    ftp.cwd("/wp-content/themes/")

                    # Create theme directory
                    try:
                        ftp.mkd(package.name)
                    except ftplib.error_perm:
                        pass  # Directory might already exist

                    ftp.cwd(package.name)

                    # Upload files
                    temp_path = Path(temp_dir)
                    for file_path in temp_path.rglob("*"):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(temp_path)

                            # Create directories if needed
                            if relative_path.parent != Path("."):
                                self._create_ftp_directories(ftp, str(relative_path.parent))

                            # Upload file
                            with open(file_path, "rb") as f:
                                ftp.storbinary(f"STOR {relative_path}", f)

            enterprise_logger.info(f"Theme uploaded via FTP: {package.name}", category=LogCategory.SYSTEM)
            return True

        except Exception as e:
            enterprise_logger.error(f"FTP deployment error: {e}", category=LogCategory.SYSTEM, error=e)
            return False

    def _create_ftp_directories(self, ftp: ftplib.FTP, path: str):
        """Create FTP directories recursively."""
        parts = path.split("/")
        current_path = ""

        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part
            try:
                ftp.mkd(current_path)
            except ftplib.error_perm:
                pass  # Directory might already exist

    async def _deploy_via_sftp(self, package: ThemePackage, credentials: WordPressCredentials) -> bool:
        """Deploy theme via SFTP."""
        try:
            if not credentials.sftp_host:
                raise ValueError("SFTP credentials not provided")

            # Setup SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect
            if credentials.sftp_private_key:
                key = paramiko.RSAKey.from_private_key_file(credentials.sftp_private_key)
                ssh.connect(credentials.sftp_host, username=credentials.sftp_username, pkey=key)
            else:
                ssh.connect(
                    credentials.sftp_host, username=credentials.sftp_username, password=credentials.ftp_password
                )

            # Extract and upload theme
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(package.package_path, "r") as zipf:
                    zipf.extractall(temp_dir)

                sftp = ssh.open_sftp()

                # Create theme directory
                theme_path = f"/wp-content/themes/{package.name}"
                try:
                    sftp.mkdir(theme_path)
                except IOError:
                    pass  # Directory might already exist

                # Upload files
                temp_path = Path(temp_dir)
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(temp_path)
                        remote_path = f"{theme_path}/{relative_path}"

                        # Create remote directories if needed
                        remote_dir = str(Path(remote_path).parent)
                        try:
                            sftp.mkdir(remote_dir)
                        except IOError:
                            pass

                        sftp.put(str(file_path), remote_path)

                sftp.close()

            ssh.close()

            enterprise_logger.info(f"Theme uploaded via SFTP: {package.name}", category=LogCategory.SYSTEM)
            return True

        except Exception as e:
            enterprise_logger.error(f"SFTP deployment error: {e}", category=LogCategory.SYSTEM, error=e)
            return False

    async def _deploy_to_staging(self, package: ThemePackage, credentials: WordPressCredentials) -> bool:
        """Deploy theme to staging area."""
        try:
            staging_path = self.staging_area / "deployed" / package.name
            staging_path.mkdir(parents=True, exist_ok=True)

            # Extract theme to staging
            with zipfile.ZipFile(package.package_path, "r") as zipf:
                zipf.extractall(staging_path)

            enterprise_logger.info(
                f"Theme deployed to staging: {package.name}",
                category=LogCategory.SYSTEM,
                metadata={"staging_path": str(staging_path)},
            )
            return True

        except Exception as e:
            enterprise_logger.error(f"Staging deployment error: {e}", category=LogCategory.SYSTEM, error=e)
            return False

    async def _activate_theme_via_api(self, theme_name: str, credentials: WordPressCredentials) -> bool:
        """Activate theme via WordPress REST API."""
        try:
            auth_header = base64.b64encode(
                f"{credentials.username}:{credentials.application_password or credentials.password}".encode()
            ).decode()

            headers = {"Authorization": f"Basic {auth_header}", "Content-Type": "application/json"}

            activate_url = f"{credentials.site_url.rstrip('/')}/wp-json/wp/v2/themes/{theme_name}/activate"

            response = requests.post(activate_url, headers=headers, timeout=60)

            if response.status_code == 200:
                enterprise_logger.info(f"Theme activated: {theme_name}", category=LogCategory.SYSTEM)
                return True
            else:
                enterprise_logger.error(
                    f"Theme activation failed: {response.status_code} - {response.text}", category=LogCategory.SYSTEM
                )
                return False

        except Exception as e:
            enterprise_logger.error(f"Theme activation error: {e}", category=LogCategory.SYSTEM, error=e)
            return False

    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """Get deployment status by ID."""
        # Check active deployments
        if deployment_id in self.active_deployments:
            return self.active_deployments[deployment_id]

        # Check history
        for result in self.deployment_history:
            if result.deployment_id == deployment_id:
                return result

        return None

    def get_system_status(self) -> Dict[str, Any]:
        """Get uploader system status."""
        return {
            "active_deployments": len(self.active_deployments),
            "total_deployments": len(self.deployment_history),
            "successful_deployments": len([r for r in self.deployment_history if r.success]),
            "staging_area": str(self.staging_area),
            "supported_methods": [method.value for method in UploadMethod],
        }


# Global theme uploader instance
automated_theme_uploader = AutomatedThemeUploader()


# Convenience functions
async def deploy_theme_package(
    theme_path: str,
    theme_info: Dict[str, Any],
    credentials: WordPressCredentials,
    upload_method: UploadMethod = UploadMethod.WORDPRESS_REST_API,
    activate_theme: bool = False,
) -> DeploymentResult:
    """Deploy theme with automatic package creation."""
    package = await automated_theme_uploader.create_theme_package(theme_path, theme_info)
    return await automated_theme_uploader.deploy_theme(package, credentials, upload_method, activate_theme)


async def quick_deploy_theme(
    theme_path: str, site_url: str, username: str, password: str, theme_name: str = None, activate: bool = False
) -> DeploymentResult:
    """Quick theme deployment with minimal configuration."""
    credentials = WordPressCredentials(
        site_url=site_url, username=username, password=password, application_password=password
    )

    theme_info = {
        "name": theme_name or Path(theme_path).name,
        "version": "1.0.0",
        "description": f"Auto-generated theme for {site_url}",
        "author": "DevSkyy Platform",
    }

    return await deploy_theme_package(theme_path, theme_info, credentials, activate_theme=activate)
