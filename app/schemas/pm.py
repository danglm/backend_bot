from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


# ==========================================
# Label Schemas
# ==========================================

class LabelBase(BaseModel):
    label_name: str
    color: str


class LabelCreate(LabelBase):
    board_id: UUID


class LabelBulkUpdate(BaseModel):
    id: UUID
    label_name: Optional[str] = None
    color: Optional[str] = None


class LabelResponse(LabelBase):
    id: UUID
    board_id: UUID

    class Config:
        from_attributes = True


# ==========================================
# Task Label Schemas (M2M)
# ==========================================

class TaskLabelCreate(BaseModel):
    task_id: UUID
    label_id: UUID


class TaskLabelResponse(BaseModel):
    id: UUID
    task_id: UUID
    label_id: UUID

    class Config:
        from_attributes = True


# ==========================================
# Comment Schemas
# ==========================================

class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    task_id: UUID
    author_id: str
    parent_comment_id: Optional[UUID] = None


class CommentBulkUpdate(BaseModel):
    id: UUID
    content: Optional[str] = None


class CommentResponse(CommentBase):
    id: UUID
    task_id: UUID
    author_id: str
    parent_comment_id: Optional[UUID] = None
    is_edited: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Attachment Schemas
# ==========================================

class AttachmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    uploader_id: str
    file_name: str
    file_path: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Activity Log Schemas
# ==========================================

class ActivityLogResponse(BaseModel):
    id: UUID
    task_id: UUID
    actor_id: str
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Task Schemas
# ==========================================

class TaskCreate(BaseModel):
    board_id: UUID
    column_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    task_type: Optional[str] = "TASK"
    assignee_id: Optional[str] = None
    reporter_id: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None


class TaskBulkUpdate(BaseModel):
    id: UUID
    column_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    task_type: Optional[str] = None
    assignee_id: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    status: Optional[str] = None


class TaskSummaryResponse(BaseModel):
    id: UUID
    task_code: str
    board_id: UUID
    column_id: UUID
    parent_task_id: Optional[UUID] = None
    title: str
    priority: str
    task_type: str
    assignee_id: Optional[str] = None
    due_date: Optional[date] = None
    position: int
    status: str
    labels: List[LabelResponse] = []
    sub_task_count: int = 0
    comment_count: int = 0

    class Config:
        from_attributes = True


# Column Response Forward Ref definition
class ColumnResponse(BaseModel):
    id: UUID
    board_id: UUID
    column_name: str
    position: int
    column_type: str
    wip_limit: Optional[int] = None
    color: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskDetailResponse(BaseModel):
    id: UUID
    task_code: str
    board_id: UUID
    column: ColumnResponse
    parent_task_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    priority: str
    task_type: str
    assignee_id: Optional[str] = None
    reporter_id: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    position: int
    status: str
    labels: List[LabelResponse] = []
    sub_tasks: List[TaskSummaryResponse] = []
    comments: List[CommentResponse] = []
    attachments: List[AttachmentResponse] = []
    activity_logs: List[ActivityLogResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MoveTaskRequest(BaseModel):
    task_id: UUID
    target_column_id: UUID
    position: Optional[int] = 0


class ReorderTaskItem(BaseModel):
    task_id: UUID
    position: int


class AssignTaskRequest(BaseModel):
    task_id: UUID
    assignee_id: Optional[str] = None


# ==========================================
# Column Schemas
# ==========================================

class ColumnCreate(BaseModel):
    board_id: UUID
    column_name: str
    position: Optional[int] = 0
    column_type: Optional[str] = "TODO"
    wip_limit: Optional[int] = None
    color: Optional[str] = None


class ColumnBulkUpdate(BaseModel):
    id: UUID
    column_name: Optional[str] = None
    position: Optional[int] = None
    column_type: Optional[str] = None
    wip_limit: Optional[int] = None
    color: Optional[str] = None


class ColumnWithTasksResponse(ColumnResponse):
    tasks: List[TaskSummaryResponse] = []


# ==========================================
# Board Schemas
# ==========================================

class BoardCreate(BaseModel):
    board_name: str
    board_key: str
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    owner_id: str
    default_assignee_id: Optional[str] = None
    status: Optional[str] = "ACTIVE"


class BoardBulkUpdate(BaseModel):
    id: UUID
    board_name: Optional[str] = None
    board_key: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    owner_id: Optional[str] = None
    default_assignee_id: Optional[str] = None
    status: Optional[str] = None


class BoardResponse(BaseModel):
    id: UUID
    board_name: str
    board_key: str
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    owner_id: str
    default_assignee_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class BoardDetailResponse(BoardResponse):
    columns: List[ColumnWithTasksResponse] = []
    labels: List[LabelResponse] = []


# ==========================================
# Board Stats Schema
# ==========================================

class BoardStatsResponse(BaseModel):
    board_id: UUID
    total_tasks: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    by_assignee: List[Dict[str, Any]]
    overdue_tasks: int
    completed_this_week: int
