from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app.models import Base
from app.routers import auth, chat, admin, documents
from app.config import settings
from dotenv import load_dotenv

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NSF AI Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])


@app.get("/")
async def root():
    return {"message": "NSF AI Assistant API", "status": "running"}


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}
