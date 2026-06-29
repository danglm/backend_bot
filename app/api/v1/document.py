from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import uuid
from app.api.deps import get_db, get_current_user
from app.schemas import document as schemas_document
from app.models.employee import Credential
from app.models.document import Document, DocumentReminder

router = APIRouter()

def generate_next_document_id(db: Session) -> str:
    count = db.query(Document).count()
    while True:
        candidate = f"DOC{str(count + 1).zfill(4)}"
        if not db.query(Document).filter(Document.id == candidate).first():
            return candidate
        count += 1

@router.get("/get-documents", response_model=List[schemas_document.DocumentResponse])
async def api_get_documents(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Get documents.
    """
    try:
        query = db.query(Document)
        if category:
            query = query.filter(Document.category == category)
        if status:
            query = query.filter(Document.status == status)
        return query.all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-documents", response_model=List[schemas_document.DocumentResponse])
async def api_add_documents(
    documents_in: List[schemas_document.DocumentCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Add a list of new documents.
    """
    created_docs = []
    try:
        for doc_in in documents_in:
            # 1. If ID is provided, check if it already exists
            if doc_in.id:
                existing_id = db.query(Document).filter(Document.id == doc_in.id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Tài liệu với mã '{doc_in.id}' đã tồn tại trong hệ thống."
                    )
                new_id = doc_in.id
            else:
                new_id = generate_next_document_id(db)

            # Create document db object
            doc_data = doc_in.dict()
            doc_data.pop("id", None)
            db_obj = Document(
                id=new_id,
                **doc_data
            )
            db.add(db_obj)
            created_docs.append(db_obj)

        db.commit()
        for d in created_docs:
            db.refresh(d)
        return created_docs
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-documents", response_model=List[schemas_document.DocumentResponse])
async def api_update_documents(
    documents_in: List[schemas_document.DocumentBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Update a list of documents.
    """
    updated_docs = []
    try:
        for doc_in in documents_in:
            # Find by ID
            db_obj = db.query(Document).filter(Document.id == doc_in.id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy tài liệu với mã '{doc_in.id}'."
                )

            # Update fields
            update_data = doc_in.dict(exclude_unset=True)
            update_data.pop("id", None)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            updated_docs.append(db_obj)

        db.commit()
        for d in updated_docs:
            db.refresh(d)
        return updated_docs
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-documents")
async def api_delete_documents(
    ids: List[str],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Delete a list of documents by ID.
    """
    try:
        deleted_ids = []
        for doc_id in ids:
            db_obj = db.query(Document).filter(Document.id == doc_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(doc_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# --- DOCUMENTREMINDER API ENDPOINTS ---

@router.get("/get-document-reminders", response_model=List[schemas_document.DocumentReminderResponse])
async def api_get_document_reminders(
    document_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Get document reminders.
    """
    try:
        query = db.query(DocumentReminder)
        if document_id:
            query = query.filter(DocumentReminder.document_id == document_id)
        if status:
            query = query.filter(DocumentReminder.status == status)
        return query.all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-document-reminders", response_model=List[schemas_document.DocumentReminderResponse])
async def api_add_document_reminders(
    reminders_in: List[schemas_document.DocumentReminderCreate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Add a list of new document reminders.
    """
    created_reminders = []
    try:
        for reminder_in in reminders_in:
            new_id = reminder_in.id if reminder_in.id else uuid.uuid4()
            if reminder_in.id:
                existing_id = db.query(DocumentReminder).filter(DocumentReminder.id == reminder_in.id).first()
                if existing_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Lịch nhắc nhở với mã '{reminder_in.id}' đã tồn tại trong hệ thống."
                    )
            
            # Create document reminder db object
            reminder_data = reminder_in.dict()
            reminder_data.pop("id", None)
            db_obj = DocumentReminder(
                id=new_id,
                **reminder_data
            )
            db.add(db_obj)
            created_reminders.append(db_obj)

        db.commit()
        for r in created_reminders:
            db.refresh(r)
        return created_reminders
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-document-reminders", response_model=List[schemas_document.DocumentReminderResponse])
async def api_update_document_reminders(
    reminders_in: List[schemas_document.DocumentReminderBulkUpdate],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Update a list of document reminders.
    """
    updated_reminders = []
    try:
        for reminder_in in reminders_in:
            db_obj = db.query(DocumentReminder).filter(DocumentReminder.id == reminder_in.id).first()
            if not db_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy lịch nhắc nhở với mã '{reminder_in.id}'."
                )

            # Update fields
            update_data = reminder_in.dict(exclude_unset=True)
            update_data.pop("id", None)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            updated_reminders.append(db_obj)

        db.commit()
        for r in updated_reminders:
            db.refresh(r)
        return updated_reminders
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-document-reminders")
async def api_delete_document_reminders(
    ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: Credential = Depends(get_current_user)
):
    """
    Delete a list of document reminders by ID.
    """
    try:
        deleted_ids = []
        for reminder_id in ids:
            db_obj = db.query(DocumentReminder).filter(DocumentReminder.id == reminder_id).first()
            if db_obj:
                db.delete(db_obj)
                deleted_ids.append(reminder_id)
        db.commit()
        return {"deleted_ids": deleted_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
