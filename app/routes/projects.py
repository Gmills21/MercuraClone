"""
Projects API routes using local SQLite.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.database_sqlite import (
    create_project, get_project_by_id, list_projects, update_project, get_quotes_by_project
)
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    address: Optional[str] = None
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    address: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None


@router.post("/", response_model=ProjectResponse)
async def create_project_endpoint(
    project: ProjectCreate,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Create a new project."""
    user_id, org_id = user_org
    now = datetime.utcnow().isoformat()
    project_id = str(uuid.uuid4())
    
    project_data = {
        "id": project_id,
        "organization_id": org_id,
        "name": project.name,
        "address": project.address,
        "status": project.status,
        "created_at": now,
        "updated_at": now,
        "metadata": project.metadata or {}
    }
    
    if create_project(project_data):
        return ProjectResponse(**project_data)
    raise HTTPException(status_code=400, detail="Failed to create project")


@router.get("/", response_model=List[ProjectResponse])
async def list_projects_endpoint(
    limit: int = 100, 
    offset: int = 0,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """List all projects."""
    user_id, org_id = user_org
    projects = list_projects(organization_id=org_id, limit=limit, offset=offset)
    return [ProjectResponse(**p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get project by ID."""
    user_id, org_id = user_org
    project = get_project_by_id(project_id, organization_id=org_id)
    if project:
        return ProjectResponse(**project)
    raise HTTPException(status_code=404, detail="Project not found")


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_endpoint(
    project_id: str, 
    updates: ProjectUpdate,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Update project."""
    user_id, org_id = user_org
    update_dict = updates.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    if update_project(project_id, update_dict, organization_id=org_id):
        project = get_project_by_id(project_id, organization_id=org_id)
        return ProjectResponse(**project)
    raise HTTPException(status_code=404, detail="Project not found")


@router.get("/{project_id}/quotes")
async def get_project_quotes(
    project_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get all quotes for a project."""
    user_id, org_id = user_org
    # Verify project exists and belongs to org
    project = get_project_by_id(project_id, organization_id=org_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    quotes = get_quotes_by_project(project_id, org_id)
    return quotes
