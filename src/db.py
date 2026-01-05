import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL: Use DATABASE_URL from env (Railway) or local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./newsletter.db")

# Fix for Heroku/Railway Postgres URLs that start with postgres:// instead of postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class NewsletterModel(Base):
    __tablename__ = "newsletters"

    id = Column(Integer, primary_key=True, index=True)
    week_number = Column(Integer)
    date_start = Column(String)
    date_end = Column(String)
    content_json = Column(Text)  # Stores the full JSON
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def save_newsletter_to_db(content_json: str, week_number: int, date_start: str, date_end: str):
    db = SessionLocal()
    try:
        new_item = NewsletterModel(
            week_number=week_number,
            date_start=date_start,
            date_end=date_end,
            content_json=content_json
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    finally:
        db.close()

def get_all_newsletters_from_db():
    db = SessionLocal()
    try:
        return db.query(NewsletterModel).order_by(NewsletterModel.created_at.desc()).all()
    finally:
        db.close()

def get_newsletter_by_id(news_id: int):
    db = SessionLocal()
    try:
        return db.query(NewsletterModel).filter(NewsletterModel.id == news_id).first()
    finally:
        db.close()
