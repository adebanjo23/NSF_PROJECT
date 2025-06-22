from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import User, Conversation, Message, Document
from app.auth import require_admin

router = APIRouter()


class UserStats(BaseModel):
    id: int
    email: str
    role: str
    conversation_count: int
    last_active: datetime = None


class SystemStats(BaseModel):
    total_users: int
    total_conversations: int
    total_messages: int
    total_documents: int
    processed_documents: int


class ConversationAdmin(BaseModel):
    id: int
    user_email: str
    title: str
    message_count: int
    created_at: datetime


@router.get("/stats", response_model=SystemStats)
def get_system_stats(
        admin_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    total_documents = db.query(Document).count()
    processed_documents = db.query(Document).filter(Document.processed == True).count()

    return SystemStats(
        total_users=total_users,
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_documents=total_documents,
        processed_documents=processed_documents
    )


@router.get("/users", response_model=List[UserStats])
def get_all_users(
        admin_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    users = db.query(User).all()
    result = []

    for user in users:
        conversation_count = db.query(Conversation).filter(Conversation.user_id == user.id).count()
        last_conversation = db.query(Conversation).filter(
            Conversation.user_id == user.id
        ).order_by(Conversation.created_at.desc()).first()

        result.append(UserStats(
            id=user.id,
            email=user.email,
            role=user.role,
            conversation_count=conversation_count,
            last_active=last_conversation.created_at if last_conversation else None
        ))

    return result


@router.get("/conversations", response_model=List[ConversationAdmin])
def get_all_conversations(
        admin_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    conversations = db.query(Conversation).join(User).order_by(
        Conversation.created_at.desc()
    ).all()

    result = []
    for conv in conversations:
        message_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
        result.append(ConversationAdmin(
            id=conv.id,
            user_email=conv.user.email,
            title=conv.title,
            message_count=message_count,
            created_at=conv.created_at
        ))

    return result


@router.delete("/users/{user_id}")
def delete_user(
        user_id: int,
        admin_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}