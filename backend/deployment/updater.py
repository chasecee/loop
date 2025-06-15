"""Deployment and update management system."""

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
import tarfile
import zipfile

from utils.logger import get_logger


class UpdaterError(Exception):
    """Custom exception for updater errors."""
    pass


class GitUpdater:
    """Git-based updater for simple deployments."""
    
    def __init__(self, repo_path: Path):
        """Initialize git updater."""
        self.repo_path = repo_path
        self.logger = get_logger("git_updater")
        
        # Check if git is available
        self.git_available = shutil.which('git') is not None
        if not self.git_available:
            self.logger.warning("Git not available")
    
    def check_for_updates(self) -> bool:
        """Check if updates are available."""
        if not self.git_available:
            return False
        
        try:
            # Fetch latest from remote
            subprocess.run(['git', 'fetch'], cwd=self.repo_path, check=True, capture_output=True)
            
            # Check if local is behind remote
            result = subprocess.run(
                ['git', 'status', '-uno', '--porcelain=v1'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            return 'behind' in result.stdout
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git fetch failed: {e}")
            return False
    
    def update(self) -> bool:
        """Update from git repository."""
        if not self.git_available:
            raise UpdaterError("Git not available")
        
        try:
            self.logger.info("Updating from git repository...")
            
            # Pull latest changes
            subprocess.run(['git', 'pull'], cwd=self.repo_path, check=True)
            
            self.logger.info("Git update completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git update failed: {e}")
            return False


class RemoteUpdater:
    """Remote archive-based updater."""
    
    def __init__(self, current_version: str = "1.0.0"):
        """Initialize remote updater."""
        self.current_version = current_version
        self.logger = get_logger("remote_updater")
    
    def check_for_updates(self, update_url: str, timeout: int = 10) -> Optional[Dict]:
        """Check for updates from remote server."""
        try:
            # Fetch update manifest
            response = requests.get(f"{update_url}/manifest.json", timeout=timeout)
            response.raise_for_status()
            
            manifest = response.json()
            remote_version = manifest.get('version', '0.0.0')
            
            if self._version_compare(remote_version, self.current_version) > 0:
                return manifest
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to check for remote updates: {e}")
            return None
    
    def download_and_apply_update(self, manifest: Dict, update_url: str, target_path: Path) -> bool:
        """Download and apply update."""
        try:
            archive_name = manifest.get('archive')
            if not archive_name:
                raise UpdaterError("No archive specified in manifest")
            
            download_url = f"{update_url}/{archive_name}"
            
            self.logger.info(f"Downloading update from {download_url}")
            
            # Download update archive
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                archive_path = temp_path / archive_name
                
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                
                with open(archive_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract archive
                extract_path = temp_path / "extracted"
                extract_path.mkdir()
                
                if archive_name.endswith('.tar.gz'):
                    with tarfile.open(archive_path, 'r:gz') as tar:
                        tar.extractall(extract_path)
                elif archive_name.endswith('.zip'):
                    with zipfile.ZipFile(archive_path, 'r') as zip_file:
                        zip_file.extractall(extract_path)
                else:
                    raise UpdaterError(f"Unsupported archive format: {archive_name}")
                
                # Apply update
                self._apply_update(extract_path, target_path)
                
                self.logger.info("Update applied successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to apply update: {e}")
            return False
    
    def _apply_update(self, source_path: Path, target_path: Path) -> None:
        """Apply update by copying files."""
        # Create backup
        backup_path = target_path.parent / f"{target_path.name}_backup_{int(time.time())}"
        shutil.copytree(target_path, backup_path)
        
        try:
            # Find the actual source directory (might be nested)
            source_dirs = [d for d in source_path.iterdir() if d.is_dir()]
            if len(source_dirs) == 1:
                actual_source = source_dirs[0]
            else:
                actual_source = source_path
            
            # Copy new files
            for item in actual_source.iterdir():
                dest_item = target_path / item.name
                
                if item.is_dir():
                    if dest_item.exists():
                        shutil.rmtree(dest_item)
                    shutil.copytree(item, dest_item)
                else:
                    shutil.copy2(item, dest_item)
            
            # Clean up old backup (keep only last 3)
            self._cleanup_backups(target_path.parent, target_path.name)
            
        except Exception as e:
            # Restore from backup on failure
            if backup_path.exists():
                shutil.rmtree(target_path)
                shutil.move(backup_path, target_path)
            raise e
    
    def _cleanup_backups(self, parent_path: Path, base_name: str) -> None:
        """Clean up old backup directories."""
        backups = sorted([
            d for d in parent_path.iterdir() 
            if d.is_dir() and d.name.startswith(f"{base_name}_backup_")
        ], key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Keep only the 3 most recent backups
        for backup in backups[3:]:
            shutil.rmtree(backup)
    
    def _version_compare(self, version1: str, version2: str) -> int:
        """Compare version strings. Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal."""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = normalize(version1)
        v2_parts = normalize(version2)
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for a, b in zip(v1_parts, v2_parts):
            if a > b:
                return 1
            elif a < b:
                return -1
        
        return 0


class SystemUpdater:
    """Main system updater that coordinates different update methods."""
    
    def __init__(self, 
                 repo_path: Path,
                 current_version: str = "1.0.0",
                 update_config: Optional[Dict] = None):
        """Initialize system updater."""
        self.repo_path = repo_path
        self.current_version = current_version
        self.update_config = update_config or {}
        self.logger = get_logger("system_updater")
        self.git_updater = GitUpdater(repo_path)

    def check_all_sources(self) -> Dict[str, any]:
        """Check git update source only."""
        return {
            'git': self.git_updater.check_for_updates(),
            'timestamp': int(time.time())
        }

    def update_from_git(self) -> bool:
        """Update from git repository and restart service if successful."""
        if not self.update_config.get('git_enabled', True):
            raise UpdaterError("Git updates are disabled")
        updated = self.git_updater.update()
        if updated:
            # Restart the service after a successful update
            try:
                subprocess.run(['sudo', 'systemctl', 'restart', 'loop'], check=True)
                self.logger.info("Service restarted successfully after git update")
            except Exception as e:
                self.logger.error(f"Failed to restart service: {e}")
        return updated

    def auto_update(self) -> Tuple[bool, str]:
        """Auto-update from git only."""
        try:
            if self.check_all_sources()['git']:
                if self.update_from_git():
                    return True, "Updated from git repository and service restarted"
            return False, "No updates available"
        except Exception as e:
            self.logger.error(f"Auto-update failed: {e}")
            return False, f"Update failed: {str(e)}"

    def get_update_status(self) -> Dict:
        """Get current update status."""
        return {
            'current_version': self.current_version,
            'git_available': self.git_updater.git_available,
            'last_check': self.update_config.get('last_check'),
            'update_sources': self.check_all_sources()
        } 