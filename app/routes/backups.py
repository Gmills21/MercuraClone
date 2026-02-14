"""
Backup API Routes
Manage database backups and restores.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
from pydantic import BaseModel

from app.services.backup_service import backup_service, run_scheduled_backup
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/backups", tags=["backups"])


class CreateBackupRequest(BaseModel):
    type: Optional[str] = "manual"


class RestoreRequest(BaseModel):
    backup_id: str
    verify: bool = True


class BackupResponse(BaseModel):
    id: str
    filename: str
    created_at: str
    type: str
    size_bytes: int
    compressed: bool
    file_exists: bool
    age_days: int


@router.post("/create")
async def create_backup(
    request: CreateBackupRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Create a new database backup."""
    user_id, org_id = user_org
    
    result = backup_service.create_backup(backup_type=request.type)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/", response_model=List[BackupResponse])
async def list_backups(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """List all available backups."""
    backups = backup_service.list_backups()
    return backups


@router.get("/stats")
async def get_backup_stats(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get backup statistics."""
    return backup_service.get_stats()


@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Restore database from a backup. Only admins can restore."""
    user_id, org_id = user_org
    
    # Check user role - only admins can restore
    from app.database_sqlite import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role FROM organization_members WHERE user_id = ? AND organization_id = ?",
            (user_id, org_id)
        )
        row = cursor.fetchone()
        if not row or row["role"] not in ["admin"]:
            raise HTTPException(status_code=403, detail="Only organization admins can restore backups")
    
    # Validate backup_id format (alphanumeric and hyphens only)
    import re
    if not re.match(r'^[a-f0-9-]+$', request.backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup ID format")
    
    result = backup_service.restore_backup(request.backup_id, verify=request.verify)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/verify/{backup_id}")
async def verify_backup(
    backup_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Verify a backup's integrity."""
    # Validate backup_id format
    import re
    if not re.match(r'^[a-f0-9-]+$', backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup ID format")
    
    result = backup_service.verify_backup(backup_id)
    return result


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Delete a backup."""
    # Validate backup_id format
    import re
    if not re.match(r'^[a-f0-9-]+$', backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup ID format")
    
    result = backup_service.delete_backup(backup_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/cleanup")
async def cleanup_old_backups(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Remove backups older than retention policy."""
    result = backup_service.cleanup_old_backups()
    return result


@router.post("/scheduled")
async def trigger_scheduled_backup(
    background_tasks: BackgroundTasks,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Trigger a scheduled backup (for cron/job runner)."""
    # Run in background to not block response
    background_tasks.add_task(run_scheduled_backup)
    
    return {
        "success": True,
        "message": "Scheduled backup started in background"
    }
