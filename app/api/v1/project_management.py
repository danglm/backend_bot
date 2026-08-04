import os
import uuid
import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.api.deps import get_db
from app.models.pm import (
    PmBoard,
    PmColumn,
    PmLabel,
    PmTask,
    PmTaskLabel,
    PmTaskComment,
    PmTaskAttachment,
    PmTaskActivityLog,
)
from app.schemas import pm as schemas

router = APIRouter()

UPLOAD_DIR = os.path.join("uploads", "pm_attachments")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==========================================
# Helper Functions
# ==========================================

def log_task_activity(
    db: Session,
    task_id: UUID,
    actor_id: str,
    action: str,
    field_name: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    details: Optional[str] = None,
):
    log = PmTaskActivityLog(
        id=uuid.uuid4(),
        task_id=task_id,
        actor_id=actor_id or "SYSTEM",
        action=action,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        details=details,
        created_at=datetime.datetime.now(),
    )
    db.add(log)


def generate_next_task_code(db: Session, board_id: UUID, board_key: str) -> str:
    # Lấy danh sách task_code có tiền tố board_key
    prefix = f"{board_key}-"
    tasks = db.query(PmTask.task_code).filter(
        PmTask.board_id == board_id,
        PmTask.task_code.like(f"{prefix}%")
    ).all()
    
    max_num = 0
    for (t_code,) in tasks:
        if t_code and t_code.startswith(prefix):
            num_part = t_code[len(prefix):]
            if num_part.isdigit():
                val = int(num_part)
                if val > max_num:
                    max_num = val
                    
    next_num = max_num + 1
    return f"{prefix}{str(next_num).zfill(3)}"


def build_task_summary(db: Session, task: PmTask) -> schemas.TaskSummaryResponse:
    # Labels
    task_labels = (
        db.query(PmLabel)
        .join(PmTaskLabel, PmLabel.id == PmTaskLabel.label_id)
        .filter(PmTaskLabel.task_id == task.id)
        .all()
    )
    label_responses = [schemas.LabelResponse.from_orm(lbl) for lbl in task_labels]
    
    # Counts
    sub_count = db.query(PmTask).filter(PmTask.parent_task_id == task.id).count()
    comment_count = db.query(PmTaskComment).filter(PmTaskComment.task_id == task.id).count()

    return schemas.TaskSummaryResponse(
        id=task.id,
        task_code=task.task_code,
        board_id=task.board_id,
        column_id=task.column_id,
        parent_task_id=task.parent_task_id,
        title=task.title,
        priority=task.priority,
        task_type=task.task_type,
        assignee_id=task.assignee_id,
        due_date=task.due_date,
        position=task.position,
        status=task.status,
        labels=label_responses,
        sub_task_count=sub_count,
        comment_count=comment_count,
    )


# ==========================================
# 1. BOARD APIs
# ==========================================

@router.get("/get-boards", response_model=List[schemas.BoardResponse])
async def get_boards(
    status: Optional[str] = "ACTIVE",
    db: Session = Depends(get_db)
):
    """Lấy danh sách boards."""
    try:
        query = db.query(PmBoard)
        if status:
            query = query.filter(PmBoard.status == status)
        return query.order_by(PmBoard.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-board/{board_id}", response_model=schemas.BoardDetailResponse)
async def get_board_detail(
    board_id: UUID,
    db: Session = Depends(get_db)
):
    """Lấy chi tiết 1 board (kèm columns, tasks, labels)."""
    board = db.query(PmBoard).filter(PmBoard.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Không tìm thấy board")

    # Fetch columns
    columns = (
        db.query(PmColumn)
        .filter(PmColumn.board_id == board_id)
        .order_by(PmColumn.position.asc())
        .all()
    )

    # Fetch labels
    labels = db.query(PmLabel).filter(PmLabel.board_id == board_id).all()
    label_responses = [schemas.LabelResponse.from_orm(l) for l in labels]

    col_responses = []
    for col in columns:
        tasks = (
            db.query(PmTask)
            .filter(PmTask.column_id == col.id)
            .order_by(PmTask.position.asc())
            .all()
        )
        task_summaries = [build_task_summary(db, t) for t in tasks]

        col_dict = schemas.ColumnResponse.from_orm(col)
        col_responses.append(
            schemas.ColumnWithTasksResponse(
                **col_dict.dict(),
                tasks=task_summaries
            )
        )

    board_res = schemas.BoardResponse.from_orm(board)
    return schemas.BoardDetailResponse(
        **board_res.dict(),
        columns=col_responses,
        labels=label_responses
    )


@router.post("/add-boards", response_model=List[schemas.BoardResponse])
async def add_boards(
    boards_in: List[schemas.BoardCreate],
    db: Session = Depends(get_db)
):
    """Tạo mới danh sách boards (tự động tạo 4 cột mặc định)."""
    created_boards = []
    try:
        for b_in in boards_in:
            # Check unique board_key
            existing = db.query(PmBoard).filter(PmBoard.board_key == b_in.board_key.upper()).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Mã Board Key '{b_in.board_key}' đã tồn tại.")

            board_id = uuid.uuid4()
            db_board = PmBoard(
                id=board_id,
                board_name=b_in.board_name,
                board_key=b_in.board_key.upper(),
                description=b_in.description,
                project_id=b_in.project_id,
                owner_id=b_in.owner_id,
                default_assignee_id=b_in.default_assignee_id,
                status=b_in.status or "ACTIVE",
            )
            db.add(db_board)

            # Auto-create 4 default columns
            default_cols = [
                {"name": "Cần Làm", "type": "TODO", "pos": 0, "color": "#3B82F6"},
                {"name": "Đang Làm", "type": "IN_PROGRESS", "pos": 1, "color": "#F59E0B"},
                {"name": "Hoàn Thành", "type": "DONE", "pos": 2, "color": "#10B981"},
                {"name": "Huỷ", "type": "CANCELLED", "pos": 3, "color": "#6B7280"},
            ]
            for col_info in default_cols:
                db_col = PmColumn(
                    id=uuid.uuid4(),
                    board_id=board_id,
                    column_name=col_info["name"],
                    position=col_info["pos"],
                    column_type=col_info["type"],
                    color=col_info["color"]
                )
                db.add(db_col)

            created_boards.append(db_board)

        db.commit()
        for b in created_boards:
            db.refresh(b)
        return created_boards
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-boards", response_model=List[schemas.BoardResponse])
async def update_boards(
    boards_in: List[schemas.BoardBulkUpdate],
    db: Session = Depends(get_db)
):
    """Cập nhật hàng loạt boards."""
    updated = []
    try:
        for b_in in boards_in:
            db_board = db.query(PmBoard).filter(PmBoard.id == b_in.id).first()
            if not db_board:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy board với ID '{b_in.id}'")

            update_data = b_in.dict(exclude_unset=True)
            update_data.pop("id", None)

            if "board_key" in update_data and update_data["board_key"]:
                update_data["board_key"] = update_data["board_key"].upper()
                # Check uniqueness if changed
                chk = db.query(PmBoard).filter(
                    PmBoard.board_key == update_data["board_key"],
                    PmBoard.id != b_in.id
                ).first()
                if chk:
                    raise HTTPException(status_code=400, detail=f"Mã Board Key '{update_data['board_key']}' đã tồn tại.")

            for field, val in update_data.items():
                setattr(db_board, field, val)

            updated.append(db_board)

        db.commit()
        for b in updated:
            db.refresh(b)
        return updated
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-boards")
async def delete_boards(
    ids: List[UUID] = Query(...),
    db: Session = Depends(get_db)
):
    """Xoá hàng loạt boards."""
    try:
        deleted_ids = []
        for board_id in ids:
            db_board = db.query(PmBoard).filter(PmBoard.id == board_id).first()
            if db_board:
                db.delete(db_board)
                deleted_ids.append(board_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive-board/{board_id}", response_model=schemas.BoardResponse)
async def archive_board(
    board_id: UUID,
    db: Session = Depends(get_db)
):
    """Archive board (thay đổi status = ARCHIVED)."""
    db_board = db.query(PmBoard).filter(PmBoard.id == board_id).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Không tìm thấy board")

    db_board.status = "ARCHIVED"
    db.commit()
    db.refresh(db_board)
    return db_board


# ==========================================
# 2. COLUMN APIs
# ==========================================

@router.get("/get-columns", response_model=List[schemas.ColumnResponse])
async def get_columns(
    board_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Lấy danh sách columns."""
    try:
        query = db.query(PmColumn)
        if board_id:
            query = query.filter(PmColumn.board_id == board_id)
        return query.order_by(PmColumn.position.asc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-columns", response_model=List[schemas.ColumnResponse])
async def add_columns(
    cols_in: List[schemas.ColumnCreate],
    db: Session = Depends(get_db)
):
    """Tạo mới columns."""
    created = []
    try:
        for c_in in cols_in:
            db_col = PmColumn(
                id=uuid.uuid4(),
                board_id=c_in.board_id,
                column_name=c_in.column_name,
                position=c_in.position or 0,
                column_type=c_in.column_type or "TODO",
                wip_limit=c_in.wip_limit,
                color=c_in.color
            )
            db.add(db_col)
            created.append(db_col)

        db.commit()
        for c in created:
            db.refresh(c)
        return created
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-columns", response_model=List[schemas.ColumnResponse])
async def update_columns(
    cols_in: List[schemas.ColumnBulkUpdate],
    db: Session = Depends(get_db)
):
    """Cập nhật / Sắp xếp thứ tự columns."""
    updated = []
    try:
        for c_in in cols_in:
            db_col = db.query(PmColumn).filter(PmColumn.id == c_in.id).first()
            if not db_col:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy column ID '{c_in.id}'")

            update_data = c_in.dict(exclude_unset=True)
            update_data.pop("id", None)

            for field, val in update_data.items():
                setattr(db_col, field, val)

            updated.append(db_col)

        db.commit()
        for c in updated:
            db.refresh(c)
        return updated
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-columns")
async def delete_columns(
    ids: List[UUID] = Query(...),
    move_to: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Xoá columns (tuỳ chọn chuyển tasks sang column khác trước khi xoá)."""
    try:
        deleted_ids = []
        for col_id in ids:
            db_col = db.query(PmColumn).filter(PmColumn.id == col_id).first()
            if db_col:
                if move_to:
                    # Move tasks first
                    db.query(PmTask).filter(PmTask.column_id == col_id).update({"column_id": move_to})
                db.delete(db_col)
                deleted_ids.append(col_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 3. LABEL APIs
# ==========================================

@router.get("/get-labels", response_model=List[schemas.LabelResponse])
async def get_labels(
    board_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Lấy danh sách labels."""
    try:
        query = db.query(PmLabel)
        if board_id:
            query = query.filter(PmLabel.board_id == board_id)
        return query.all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-labels", response_model=List[schemas.LabelResponse])
async def add_labels(
    labels_in: List[schemas.LabelCreate],
    db: Session = Depends(get_db)
):
    """Tạo mới labels."""
    created = []
    try:
        for l_in in labels_in:
            db_lbl = PmLabel(
                id=uuid.uuid4(),
                board_id=l_in.board_id,
                label_name=l_in.label_name,
                color=l_in.color
            )
            db.add(db_lbl)
            created.append(db_lbl)

        db.commit()
        for l in created:
            db.refresh(l)
        return created
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-labels", response_model=List[schemas.LabelResponse])
async def update_labels(
    labels_in: List[schemas.LabelBulkUpdate],
    db: Session = Depends(get_db)
):
    """Cập nhật labels."""
    updated = []
    try:
        for l_in in labels_in:
            db_lbl = db.query(PmLabel).filter(PmLabel.id == l_in.id).first()
            if not db_lbl:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy label ID '{l_in.id}'")

            update_data = l_in.dict(exclude_unset=True)
            update_data.pop("id", None)

            for field, val in update_data.items():
                setattr(db_lbl, field, val)

            updated.append(db_lbl)

        db.commit()
        for l in updated:
            db.refresh(l)
        return updated
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-labels")
async def delete_labels(
    ids: List[UUID] = Query(...),
    db: Session = Depends(get_db)
):
    """Xoá labels."""
    try:
        deleted_ids = []
        for lbl_id in ids:
            db_lbl = db.query(PmLabel).filter(PmLabel.id == lbl_id).first()
            if db_lbl:
                db.delete(db_lbl)
                deleted_ids.append(lbl_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 4. TASK APIs
# ==========================================

@router.get("/get-tasks", response_model=List[schemas.TaskSummaryResponse])
async def get_tasks(
    board_id: UUID = Query(...),
    column_id: Optional[UUID] = None,
    assignee_id: Optional[str] = None,
    reporter_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    task_type: Optional[str] = None,
    parent_task_id: Optional[UUID] = None,
    search: Optional[str] = None,
    due_date_from: Optional[datetime.date] = None,
    due_date_to: Optional[datetime.date] = None,
    db: Session = Depends(get_db)
):
    """Lấy danh sách tasks với bộ lọc đa chiều."""
    try:
        query = db.query(PmTask).filter(PmTask.board_id == board_id)

        if column_id:
            query = query.filter(PmTask.column_id == column_id)
        if assignee_id:
            query = query.filter(PmTask.assignee_id == assignee_id)
        if reporter_id:
            query = query.filter(PmTask.reporter_id == reporter_id)
        if status:
            query = query.filter(PmTask.status == status)
        if priority:
            query = query.filter(PmTask.priority == priority)
        if task_type:
            query = query.filter(PmTask.task_type == task_type)
        if parent_task_id:
            query = query.filter(PmTask.parent_task_id == parent_task_id)
        if due_date_from:
            query = query.filter(PmTask.due_date >= due_date_from)
        if due_date_to:
            query = query.filter(PmTask.due_date <= due_date_to)
        if search:
            query = query.filter(
                or_(
                    PmTask.title.ilike(f"%{search}%"),
                    PmTask.task_code.ilike(f"%{search}%")
                )
            )

        tasks = query.order_by(PmTask.position.asc()).all()
        return [build_task_summary(db, t) for t in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-task/{task_id}", response_model=schemas.TaskDetailResponse)
async def get_task_detail(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """Lấy chi tiết đầy đủ của 1 task."""
    task = db.query(PmTask).filter(PmTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy task")

    # Column
    column = db.query(PmColumn).filter(PmColumn.id == task.column_id).first()
    col_response = schemas.ColumnResponse.from_orm(column) if column else None

    # Labels
    task_labels = (
        db.query(PmLabel)
        .join(PmTaskLabel, PmLabel.id == PmTaskLabel.label_id)
        .filter(PmTaskLabel.task_id == task_id)
        .all()
    )
    labels_res = [schemas.LabelResponse.from_orm(l) for l in task_labels]

    # Subtasks
    sub_tasks = db.query(PmTask).filter(PmTask.parent_task_id == task_id).all()
    sub_summaries = [build_task_summary(db, st) for st in sub_tasks]

    # Comments
    comments = (
        db.query(PmTaskComment)
        .filter(PmTaskComment.task_id == task_id)
        .order_by(PmTaskComment.created_at.asc())
        .all()
    )
    comments_res = [schemas.CommentResponse.from_orm(c) for c in comments]

    # Attachments
    attachments = db.query(PmTaskAttachment).filter(PmTaskAttachment.task_id == task_id).all()
    attachments_res = [schemas.AttachmentResponse.from_orm(a) for a in attachments]

    # Activity logs
    logs = (
        db.query(PmTaskActivityLog)
        .filter(PmTaskActivityLog.task_id == task_id)
        .order_by(PmTaskActivityLog.created_at.desc())
        .all()
    )
    logs_res = [schemas.ActivityLogResponse.from_orm(lg) for lg in logs]

    task_dict = {
        "id": task.id,
        "task_code": task.task_code,
        "board_id": task.board_id,
        "column": col_response,
        "parent_task_id": task.parent_task_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "task_type": task.task_type,
        "assignee_id": task.assignee_id,
        "reporter_id": task.reporter_id,
        "start_date": task.start_date,
        "due_date": task.due_date,
        "completed_at": task.completed_at,
        "estimated_hours": task.estimated_hours,
        "actual_hours": task.actual_hours,
        "position": task.position,
        "status": task.status,
        "labels": labels_res,
        "sub_tasks": sub_summaries,
        "comments": comments_res,
        "attachments": attachments_res,
        "activity_logs": logs_res,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }
    return schemas.TaskDetailResponse(**task_dict)


@router.post("/add-tasks", response_model=List[schemas.TaskSummaryResponse])
async def add_tasks(
    tasks_in: List[schemas.TaskCreate],
    db: Session = Depends(get_db)
):
    """Tạo mới danh sách tasks (tự động sinh task_code)."""
    created_tasks = []
    try:
        for t_in in tasks_in:
            board = db.query(PmBoard).filter(PmBoard.id == t_in.board_id).first()
            if not board:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy Board '{t_in.board_id}'")

            # Xử lý column_id nếu không truyền -> đặt vào column TODO đầu tiên
            target_col_id = t_in.column_id
            if not target_col_id:
                first_col = (
                    db.query(PmColumn)
                    .filter(PmColumn.board_id == t_in.board_id)
                    .order_by(PmColumn.position.asc())
                    .first()
                )
                if not first_col:
                    raise HTTPException(status_code=400, detail="Board chưa có column nào để chứa task.")
                target_col_id = first_col.id

            task_id = uuid.uuid4()
            task_code = generate_next_task_code(db, t_in.board_id, board.board_key)

            # Lấy position cuối trong column
            max_pos = (
                db.query(func.max(PmTask.position))
                .filter(PmTask.column_id == target_col_id)
                .scalar()
            )
            next_pos = (max_pos + 1) if max_pos is not None else 0

            db_task = PmTask(
                id=task_id,
                task_code=task_code,
                board_id=t_in.board_id,
                column_id=target_col_id,
                parent_task_id=t_in.parent_task_id,
                title=t_in.title,
                description=t_in.description,
                priority=t_in.priority or "MEDIUM",
                task_type=t_in.task_type or "TASK",
                assignee_id=t_in.assignee_id or board.default_assignee_id,
                reporter_id=t_in.reporter_id,
                start_date=t_in.start_date,
                due_date=t_in.due_date,
                estimated_hours=t_in.estimated_hours,
                position=next_pos,
                status="OPEN",
            )
            db.add(db_task)

            # Activity log
            log_task_activity(
                db=db,
                task_id=task_id,
                actor_id=t_in.reporter_id or "SYSTEM",
                action="CREATED",
                details=f"Tạo task {task_code}: {t_in.title}"
            )

            created_tasks.append(db_task)

        db.commit()
        for t in created_tasks:
            db.refresh(t)
        return [build_task_summary(db, t) for t in created_tasks]
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-tasks", response_model=List[schemas.TaskSummaryResponse])
async def update_tasks(
    tasks_in: List[schemas.TaskBulkUpdate],
    db: Session = Depends(get_db)
):
    """Cập nhật thông tin task."""
    updated = []
    try:
        for t_in in tasks_in:
            db_task = db.query(PmTask).filter(PmTask.id == t_in.id).first()
            if not db_task:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy task ID '{t_in.id}'")

            update_data = t_in.dict(exclude_unset=True)
            update_data.pop("id", None)

            for field, new_val in update_data.items():
                old_val = getattr(db_task, field)
                if old_val != new_val:
                    setattr(db_task, field, new_val)

                    # Auto activity log
                    log_action = "STATUS_CHANGED" if field == "status" else "UPDATED"
                    log_task_activity(
                        db=db,
                        task_id=db_task.id,
                        actor_id="USER",
                        action=log_action,
                        field_name=field,
                        old_value=str(old_val),
                        new_value=str(new_val),
                    )

            if t_in.status == "DONE" and not db_task.completed_at:
                db_task.completed_at = datetime.datetime.now()

            updated.append(db_task)

        db.commit()
        for t in updated:
            db.refresh(t)
        return [build_task_summary(db, t) for t in updated]
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-tasks")
async def delete_tasks(
    ids: List[UUID] = Query(...),
    db: Session = Depends(get_db)
):
    """Xoá tasks."""
    try:
        deleted_ids = []
        for task_id in ids:
            db_task = db.query(PmTask).filter(PmTask.id == task_id).first()
            if db_task:
                db.delete(db_task)
                deleted_ids.append(task_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/move-task", response_model=schemas.TaskSummaryResponse)
async def move_task(
    req: schemas.MoveTaskRequest,
    db: Session = Depends(get_db)
):
    """Di chuyển task giữa các columns (Kanban drag & drop)."""
    db_task = db.query(PmTask).filter(PmTask.id == req.task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Không tìm thấy task")

    target_col = db.query(PmColumn).filter(PmColumn.id == req.target_column_id).first()
    if not target_col:
        raise HTTPException(status_code=404, detail="Không tìm thấy column đích")

    old_col_id = db_task.column_id
    old_status = db_task.status

    db_task.column_id = req.target_column_id
    db_task.position = req.position or 0

    # Auto sync status based on column type
    if target_col.column_type == "DONE":
        db_task.status = "DONE"
        if not db_task.completed_at:
            db_task.completed_at = datetime.datetime.now()
    elif target_col.column_type == "IN_PROGRESS":
        db_task.status = "IN_PROGRESS"
    elif target_col.column_type == "CANCELLED":
        db_task.status = "CANCELLED"
    elif target_col.column_type == "TODO":
        db_task.status = "OPEN"

    log_task_activity(
        db=db,
        task_id=db_task.id,
        actor_id="USER",
        action="MOVED",
        field_name="column_id",
        old_value=str(old_col_id),
        new_value=str(req.target_column_id),
        details=f"Di chuyển sang cột '{target_col.column_name}'"
    )

    if old_status != db_task.status:
        log_task_activity(
            db=db,
            task_id=db_task.id,
            actor_id="USER",
            action="STATUS_CHANGED",
            field_name="status",
            old_value=old_status,
            new_value=db_task.status,
        )

    db.commit()
    db.refresh(db_task)
    return build_task_summary(db, db_task)


@router.post("/reorder-tasks")
async def reorder_tasks(
    items: List[schemas.ReorderTaskItem],
    db: Session = Depends(get_db)
):
    """Sắp xếp lại vị trí thứ tự của các tasks trong 1 column."""
    try:
        for item in items:
            db.query(PmTask).filter(PmTask.id == item.task_id).update({"position": item.position})
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign-task", response_model=schemas.TaskSummaryResponse)
async def assign_task(
    req: schemas.AssignTaskRequest,
    db: Session = Depends(get_db)
):
    """Giao task cho người khác."""
    db_task = db.query(PmTask).filter(PmTask.id == req.task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Không tìm thấy task")

    old_assignee = db_task.assignee_id
    db_task.assignee_id = req.assignee_id

    log_task_activity(
        db=db,
        task_id=db_task.id,
        actor_id="USER",
        action="ASSIGNED",
        field_name="assignee_id",
        old_value=old_assignee,
        new_value=req.assignee_id,
        details=f"Giao task cho '{req.assignee_id or 'Bỏ giao việc'}'"
    )

    db.commit()
    db.refresh(db_task)
    return build_task_summary(db, db_task)


# ==========================================
# 5. TASK LABEL APIs
# ==========================================

@router.post("/add-task-labels", response_model=List[schemas.TaskLabelResponse])
async def add_task_labels(
    links_in: List[schemas.TaskLabelCreate],
    db: Session = Depends(get_db)
):
    """Gắn label vào task."""
    created = []
    try:
        for link in links_in:
            # Check exist
            chk = db.query(PmTaskLabel).filter(
                PmTaskLabel.task_id == link.task_id,
                PmTaskLabel.label_id == link.label_id
            ).first()
            if not chk:
                db_link = PmTaskLabel(
                    id=uuid.uuid4(),
                    task_id=link.task_id,
                    label_id=link.label_id
                )
                db.add(db_link)
                created.append(db_link)

                log_task_activity(
                    db=db,
                    task_id=link.task_id,
                    actor_id="USER",
                    action="LABEL_ADDED",
                    details=f"Gắn label ID '{link.label_id}'"
                )

        db.commit()
        for l in created:
            db.refresh(l)
        return created
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-task-labels")
async def delete_task_labels(
    ids: List[UUID] = Query(...),
    db: Session = Depends(get_db)
):
    """Gỡ label khỏi task."""
    try:
        deleted_ids = []
        for link_id in ids:
            db_link = db.query(PmTaskLabel).filter(PmTaskLabel.id == link_id).first()
            if db_link:
                log_task_activity(
                    db=db,
                    task_id=db_link.task_id,
                    actor_id="USER",
                    action="LABEL_REMOVED",
                    details=f"Gỡ label ID '{db_link.label_id}'"
                )
                db.delete(db_link)
                deleted_ids.append(link_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 6. COMMENT APIs
# ==========================================

@router.get("/get-task-comments", response_model=List[schemas.CommentResponse])
async def get_task_comments(
    task_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Lấy danh sách bình luận trong task."""
    try:
        return (
            db.query(PmTaskComment)
            .filter(PmTaskComment.task_id == task_id)
            .order_by(PmTaskComment.created_at.asc())
            .all()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-task-comments", response_model=List[schemas.CommentResponse])
async def add_task_comments(
    comments_in: List[schemas.CommentCreate],
    db: Session = Depends(get_db)
):
    """Thêm bình luận mới vào task."""
    created = []
    try:
        for c_in in comments_in:
            db_cm = PmTaskComment(
                id=uuid.uuid4(),
                task_id=c_in.task_id,
                author_id=c_in.author_id,
                content=c_in.content,
                parent_comment_id=c_in.parent_comment_id,
            )
            db.add(db_cm)
            created.append(db_cm)

            log_task_activity(
                db=db,
                task_id=c_in.task_id,
                actor_id=c_in.author_id,
                action="COMMENTED",
                details=f"Bình luận: {c_in.content[:50]}"
            )

        db.commit()
        for c in created:
            db.refresh(c)
        return created
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-task-comments", response_model=List[schemas.CommentResponse])
async def update_task_comments(
    comments_in: List[schemas.CommentBulkUpdate],
    db: Session = Depends(get_db)
):
    """Chỉnh sửa bình luận."""
    updated = []
    try:
        for c_in in comments_in:
            db_cm = db.query(PmTaskComment).filter(PmTaskComment.id == c_in.id).first()
            if db_cm:
                if c_in.content is not None and c_in.content != db_cm.content:
                    db_cm.content = c_in.content
                    db_cm.is_edited = True
                    updated.append(db_cm)

        db.commit()
        for c in updated:
            db.refresh(c)
        return updated
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-task-comments")
async def delete_task_comments(
    ids: List[UUID] = Query(...),
    db: Session = Depends(get_db)
):
    """Xoá bình luận."""
    try:
        deleted_ids = []
        for cm_id in ids:
            db_cm = db.query(PmTaskComment).filter(PmTaskComment.id == cm_id).first()
            if db_cm:
                db.delete(db_cm)
                deleted_ids.append(cm_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 7. ATTACHMENT APIs
# ==========================================

@router.get("/get-task-attachments", response_model=List[schemas.AttachmentResponse])
async def get_task_attachments(
    task_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Lấy danh sách file đính kèm trong task."""
    try:
        return db.query(PmTaskAttachment).filter(PmTaskAttachment.task_id == task_id).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-task-attachment", response_model=schemas.AttachmentResponse)
async def upload_task_attachment(
    task_id: UUID = Form(...),
    uploader_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload file đính kèm vào task."""
    try:
        db_task = db.query(PmTask).filter(PmTask.id == task_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Không tìm thấy task")

        ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        saved_path = os.path.join(UPLOAD_DIR, unique_name)

        content = await file.read()
        file_size = len(content)

        with open(saved_path, "wb") as f:
            f.write(content)

        attachment = PmTaskAttachment(
            id=uuid.uuid4(),
            task_id=task_id,
            uploader_id=uploader_id,
            file_name=file.filename,
            file_path=saved_path,
            file_type=file.content_type,
            file_size=file_size,
        )
        db.add(attachment)

        log_task_activity(
            db=db,
            task_id=task_id,
            actor_id=uploader_id,
            action="ATTACHMENT_ADDED",
            details=f"Tải lên file '{file.filename}'"
        )

        db.commit()
        db.refresh(attachment)
        return attachment
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-task-attachments")
async def delete_task_attachments(
    ids: List[UUID] = Query(...),
    db: Session = Depends(get_db)
):
    """Xoá file đính kèm."""
    try:
        deleted_ids = []
        for att_id in ids:
            db_att = db.query(PmTaskAttachment).filter(PmTaskAttachment.id == att_id).first()
            if db_att:
                if os.path.exists(db_att.file_path):
                    try:
                        os.remove(db_att.file_path)
                    except Exception:
                        pass

                log_task_activity(
                    db=db,
                    task_id=db_att.task_id,
                    actor_id="USER",
                    action="ATTACHMENT_REMOVED",
                    details=f"Xoá file '{db_att.file_name}'"
                )
                db.delete(db_att)
                deleted_ids.append(att_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 8. ACTIVITY LOG API
# ==========================================

@router.get("/get-task-activity-logs", response_model=List[schemas.ActivityLogResponse])
async def get_task_activity_logs(
    task_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Lấy lịch sử hoạt động của task."""
    try:
        return (
            db.query(PmTaskActivityLog)
            .filter(PmTaskActivityLog.task_id == task_id)
            .order_by(PmTaskActivityLog.created_at.desc())
            .all()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 9. DASHBOARD STATS API
# ==========================================

@router.get("/board-stats/{board_id}", response_model=schemas.BoardStatsResponse)
async def get_board_stats(
    board_id: UUID,
    db: Session = Depends(get_db)
):
    """Lấy thống kê tổng quan của board."""
    board = db.query(PmBoard).filter(PmBoard.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Không tìm thấy board")

    all_tasks = db.query(PmTask).filter(PmTask.board_id == board_id).all()
    total_tasks = len(all_tasks)

    # By status
    by_status = {"OPEN": 0, "IN_PROGRESS": 0, "DONE": 0, "BLOCKED": 0, "CANCELLED": 0}
    # By priority
    by_priority = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    # By assignee
    assignees_map = {}

    now = datetime.datetime.now()
    today_date = now.date()
    start_of_week = today_date - datetime.timedelta(days=today_date.weekday())

    overdue = 0
    completed_this_week = 0

    for t in all_tasks:
        # Status
        if t.status in by_status:
            by_status[t.status] += 1
        else:
            by_status[t.status] = 1

        # Priority
        if t.priority in by_priority:
            by_priority[t.priority] += 1
        else:
            by_priority[t.priority] = 1

        # Assignee
        ass = t.assignee_id or "Unassigned"
        assignees_map[ass] = assignees_map.get(ass, 0) + 1

        # Overdue
        if t.due_date and t.due_date < today_date and t.status not in ["DONE", "CANCELLED"]:
            overdue += 1

        # Completed this week
        if t.completed_at and t.completed_at.date() >= start_of_week:
            completed_this_week += 1

    by_assignee_list = [{"assignee_id": k, "count": v} for k, v in assignees_map.items()]

    return schemas.BoardStatsResponse(
        board_id=board_id,
        total_tasks=total_tasks,
        by_status=by_status,
        by_priority=by_priority,
        by_assignee=by_assignee_list,
        overdue_tasks=overdue,
        completed_this_week=completed_this_week,
    )
