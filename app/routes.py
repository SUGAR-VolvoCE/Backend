from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime
from uuid import UUID

load_dotenv()

router = APIRouter()

DATABASE_URL = (
    f"host='{os.getenv('PGHOST')}' "
    f"dbname='{os.getenv('PGDATABASE')}' "
    f"user='{os.getenv('PGUSER')}' "
    f"password='{os.getenv('PGPASSWORD')}'"
)

class ConversationMessage(BaseModel):
    thread_id: UUID
    ticket_id: Optional[int]
    sender: str
    message: str
    media_url: Optional[str]
    timestamp: Optional[datetime]

@router.post("/")
def add_conversation(msg: ConversationMessage):
    print(msg)
    if not msg.message and not msg.media_url:
        raise HTTPException(status_code=400, detail="You must provide either a message or media_url.")

    try:
        conn = psycopg2.connect(DATABASE_URL)
    except psycopg2.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

    try:
        cur = conn.cursor()
    except psycopg2.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Cursor creation error: {str(e)}")

    try:
        cur.execute("""
            INSERT INTO conversations (thread_id, ticket_id, sender, message, media_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *;
        """, (str(msg.thread_id), msg.ticket_id, msg.sender, msg.message, msg.media_url))

    except psycopg2.Error as e:
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"SQL execution error: {str(e)}")

    try:
        result = cur.fetchone()
    except psycopg2.Error as e:
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Fetch error: {str(e)}")

    try:
        conn.commit()
    except psycopg2.Error as e:
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Commit error: {str(e)}")

    try:
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Close connection error: {str(e)}")

    return {
        "id": result[0],
        "thread_id": result[1],
        "ticket_id": result[2],
        "sender": result[3],
        "message": result[4],
        "media_url": result[5],
        "timestamp": result[6]
    }
