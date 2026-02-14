"""
Automated Backup Service
Handles scheduled database backups with retention policies.
"""

import os
import shutil
import gzip
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import json

from loguru import logger

from app.config import settings


class BackupService:
    """
    Service for managing automated database backups.
    
    Features:
    - Scheduled daily/hourly backups
    - Configurable retention policies
    - Backup verification
    - Compression (gzip)
    - Remote upload support (S3, etc.)
    """
    
    def __init__(self):
        self.db_path = self._get_db_path()
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
        self.retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
        self.max_backups = int(os.getenv("BACKUP_MAX_COUNT", "100"))
        self.compression_enabled = os.getenv("BACKUP_COMPRESSION", "true").lower() == "true"
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_db_path(self) -> str:
        """Get the database file path from settings."""
        db_url = settings.database_url
        if db_url.startswith("sqlite:///"):
            path = db_url.replace("sqlite:///", "")
            if path.startswith("./"):
                path = path[2:]
            return os.path.abspath(path)
        return "mercura.db"
    
    def create_backup(self, backup_type: str = "manual") -> Dict:
        """
        Create a new database backup.
        
        Args:
            backup_type: 'manual', 'scheduled', or 'pre_migration'
        
        Returns:
            Dict with backup metadata
        """
        timestamp = datetime.utcnow()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Generate backup filename
        base_name = f"mercura_backup_{backup_type}_{timestamp_str}"
        backup_filename = f"{base_name}.db"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Compress if enabled
            final_path = backup_path
            final_size = backup_path.stat().st_size
            
            if self.compression_enabled:
                compressed_path = self._compress_file(backup_path)
                final_path = compressed_path
                final_size = compressed_path.stat().st_size
                # Remove uncompressed file
                backup_path.unlink()
            
            # Create metadata file
            metadata = {
                "id": hashlib.sha256(f"{backup_filename}{timestamp_str}".encode()).hexdigest()[:16],
                "filename": final_path.name,
                "created_at": timestamp.isoformat(),
                "type": backup_type,
                "size_bytes": final_size,
                "checksum": checksum,
                "compressed": self.compression_enabled,
                "database_path": self.db_path,
                "version": "1.0.0"
            }
            
            metadata_path = final_path.with_suffix(final_path.suffix + ".json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created: {final_path.name} ({self._format_size(final_size)})")
            
            return {
                "success": True,
                "backup": metadata,
                "path": str(final_path)
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            # Clean up partial backup
            if backup_path.exists():
                backup_path.unlink()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _compress_file(self, file_path: Path) -> Path:
        """Compress a file using gzip."""
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return compressed_path
    
    def _decompress_file(self, file_path: Path, output_path: Path):
        """Decompress a gzip file."""
        with gzip.open(file_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        backups = []
        
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                # Check if backup file exists
                backup_file = self.backup_dir / metadata["filename"]
                metadata["file_exists"] = backup_file.exists()
                metadata["age_days"] = (datetime.utcnow() - datetime.fromisoformat(metadata["created_at"])).days
                
                backups.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to read backup metadata {metadata_file}: {e}")
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def restore_backup(self, backup_id: str, verify: bool = True) -> Dict:
        """
        Restore database from a backup.
        
        Args:
            backup_id: The backup ID to restore
            verify: Whether to verify checksum before restore
        
        Returns:
            Dict with restore result
        """
        # Find backup by ID
        backup = None
        backup_file = None
        
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if metadata["id"] == backup_id:
                        backup = metadata
                        backup_file = self.backup_dir / metadata["filename"]
                        break
            except:
                continue
        
        if not backup or not backup_file or not backup_file.exists():
            return {
                "success": False,
                "error": f"Backup {backup_id} not found"
            }
        
        try:
            # Create pre-restore backup
            pre_restore = self.create_backup(backup_type="pre_restore")
            if not pre_restore["success"]:
                return {
                    "success": False,
                    "error": "Failed to create pre-restore backup"
                }
            
            # Verify checksum if requested
            if verify:
                current_checksum = self._calculate_checksum(backup_file)
                if current_checksum != backup["checksum"]:
                    return {
                        "success": False,
                        "error": "Backup checksum mismatch - file may be corrupted"
                    }
            
            # Decompress if needed
            temp_file = None
            source_file = backup_file
            
            if backup.get("compressed") or str(backup_file).endswith('.gz'):
                temp_file = self.backup_dir / f"temp_restore_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.db"
                self._decompress_file(backup_file, temp_file)
                source_file = temp_file
            
            # Perform restore
            shutil.copy2(source_file, self.db_path)
            
            # Clean up temp file
            if temp_file and temp_file.exists():
                temp_file.unlink()
            
            logger.info(f"Database restored from backup: {backup['filename']}")
            
            return {
                "success": True,
                "message": f"Database restored from backup created at {backup['created_at']}",
                "pre_restore_backup": pre_restore["backup"]["id"]
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_backup(self, backup_id: str) -> Dict:
        """Delete a backup and its metadata."""
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if metadata["id"] == backup_id:
                        # Delete backup file
                        backup_file = self.backup_dir / metadata["filename"]
                        if backup_file.exists():
                            backup_file.unlink()
                        
                        # Delete metadata file
                        metadata_file.unlink()
                        
                        logger.info(f"Backup deleted: {backup_id}")
                        return {"success": True, "message": "Backup deleted"}
            except:
                continue
        
        return {"success": False, "error": "Backup not found"}
    
    def cleanup_old_backups(self) -> Dict:
        """
        Remove backups older than retention policy.
        
        Returns:
            Dict with cleanup results
        """
        deleted = []
        errors = []
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                created_at = datetime.fromisoformat(metadata["created_at"])
                
                # Delete if older than retention
                if created_at < cutoff_date:
                    backup_file = self.backup_dir / metadata["filename"]
                    if backup_file.exists():
                        backup_file.unlink()
                    metadata_file.unlink()
                    deleted.append(metadata["id"])
                    
            except Exception as e:
                errors.append(str(e))
        
        # Also enforce max backups limit (keep newest)
        backups = self.list_backups()
        if len(backups) > self.max_backups:
            to_delete = backups[self.max_backups:]
            for backup in to_delete:
                result = self.delete_backup(backup["id"])
                if result["success"]:
                    deleted.append(backup["id"])
                else:
                    errors.append(result.get("error"))
        
        logger.info(f"Backup cleanup complete: {len(deleted)} deleted, {len(errors)} errors")
        
        return {
            "success": True,
            "deleted_count": len(deleted),
            "deleted_ids": deleted,
            "errors": errors if errors else None
        }
    
    def verify_backup(self, backup_id: str) -> Dict:
        """Verify a backup's integrity."""
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if metadata["id"] == backup_id:
                        backup_file = self.backup_dir / metadata["filename"]
                        
                        if not backup_file.exists():
                            return {"valid": False, "error": "Backup file not found"}
                        
                        current_checksum = self._calculate_checksum(backup_file)
                        valid = current_checksum == metadata["checksum"]
                        
                        return {
                            "valid": valid,
                            "backup_id": backup_id,
                            "stored_checksum": metadata["checksum"],
                            "current_checksum": current_checksum,
                            "message": "Backup is valid" if valid else "Checksum mismatch - backup may be corrupted"
                        }
            except:
                continue
        
        return {"valid": False, "error": "Backup not found"}
    
    def get_stats(self) -> Dict:
        """Get backup statistics."""
        backups = self.list_backups()
        total_size = sum(b.get("size_bytes", 0) for b in backups)
        
        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_formatted": self._format_size(total_size),
            "retention_days": self.retention_days,
            "max_backups": self.max_backups,
            "backup_directory": str(self.backup_dir),
            "compression_enabled": self.compression_enabled,
            "latest_backup": backups[0] if backups else None,
            "oldest_backup": backups[-1] if backups else None
        }


# Global backup service instance
backup_service = BackupService()


def run_scheduled_backup():
    """Function to be called by scheduler for automated backups."""
    logger.info("Running scheduled backup...")
    
    # Create backup
    result = backup_service.create_backup(backup_type="scheduled")
    
    if result["success"]:
        # Cleanup old backups
        cleanup_result = backup_service.cleanup_old_backups()
        logger.info(f"Scheduled backup complete. Cleanup: {cleanup_result['deleted_count']} old backups removed")
    else:
        logger.error(f"Scheduled backup failed: {result.get('error')}")
    
    return result
