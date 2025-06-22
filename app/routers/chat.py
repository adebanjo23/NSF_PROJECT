from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, Conversation, Message
from app.auth import get_current_user
from app.graphrag_service import graphrag_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: int


class MessageResponse(BaseModel):
    id: int
    user_message: str
    ai_response: str
    timestamp: datetime


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    message_count: int


@router.post("/chat", response_model=ChatResponse)
async def chat(
        request: ChatRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:50] + ("..." if len(request.message) > 50 else ""),
            created_at=datetime.utcnow()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    recent_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.timestamp.desc()).limit(3).all()

    conversation_history = [
        {
            "user_message": msg.user_message,
            "ai_response": msg.ai_response
        }
        for msg in reversed(recent_messages)
    ]

    ai_response = await graphrag_service.query_async(request.message, conversation_history)

    new_message = Message(
        conversation_id=conversation.id,
        user_message=request.message,
        ai_response=ai_response,
        timestamp=datetime.utcnow()
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return ChatResponse(
        response=ai_response,
        conversation_id=conversation.id
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()

    result = []
    for conv in conversations:
        message_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
        result.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            message_count=message_count
        ))

    return result


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(
        conversation_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp).all()

    return messages