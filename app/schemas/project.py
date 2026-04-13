from pydantic import BaseModel, UUID4
from typing import Optional

class ProjectBase(BaseModel):
    project_name: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: UUID4

    class Config:
        from_attributes = True
