from fastapi import APIRouter, Request, Depends, Response
from sqlalchemy.orm import Session
from Application.database import get_db, ChatTransfer, Session_Table, AgentID
from datetime import datetime
import logging

chat_transfer_router = APIRouter()


# Utility Function to transfer the user to customer care
def transfer_to_customer_care(session_id: str, db: Session):
    chat_transfer = ChatTransfer(session_id=session_id, transferred_at=datetime.utcnow())
    db.add(chat_transfer)
    db.commit()
    logging.info(f"Session {session_id} transferred to customer care.")
    return {"message": "User successfully transferred to customer care."}


async def transfer_guest_to_customer_care(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"error": "Session ID not found in cookies."}

    session = db.query(Session_Table).filter_by(session_id=session_id).first()
    if not session:
        return {"error": "Session not found."}

    return transfer_to_customer_care(session_id, db)
