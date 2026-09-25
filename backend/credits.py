import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import User

load_dotenv()

DAILY_CREDITS = int(os.getenv("DAILY_CREDITS", 300))
WEBSITE_COST = int(os.getenv("WEBSITE_COST", 10))
APK_COST = int(os.getenv("APK_COST", 50))


def reset_if_needed(user: User, db: Session) -> None:
    now = datetime.utcnow()
    if now - user.last_reset >= timedelta(days=1):
        user.credits = DAILY_CREDITS
        user.last_reset = now
        db.commit()


def consume(user: User, db: Session, cost: int) -> None:
    reset_if_needed(user, db)
    if user.credits < cost:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Not enough credits",
                "credits": user.credits,
                "needed": cost,
                "resets_at": (user.last_reset + timedelta(days=1)).isoformat(),
            },
        )
    user.credits -= cost
    db.commit()
