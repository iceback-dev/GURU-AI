import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import User, Project
from auth import hash_password, verify_password, create_token, current_user
from credits import reset_if_needed, consume, WEBSITE_COST, APK_COST, DAILY_CREDITS
from generators import generate_website, generate_android_project

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ForgeAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class PromptIn(BaseModel):
    prompt: str


# ---------- AUTH ----------
@app.post("/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        credits=DAILY_CREDITS,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@app.post("/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@app.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    reset_if_needed(user, db)
    return {
        "email": user.email,
        "credits": user.credits,
        "daily_credits": DAILY_CREDITS,
        "website_cost": WEBSITE_COST,
        "apk_cost": APK_COST,
        "last_reset": user.last_reset.isoformat(),
    }


# ---------- GENERATORS ----------
@app.post("/generate/website")
async def gen_website(
    body: PromptIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    consume(user, db, WEBSITE_COST)
    try:
        zip_bytes, title = await generate_website(body.prompt)
    except Exception as e:
        user.credits += WEBSITE_COST
        db.commit()
        raise HTTPException(500, f"Generation failed: {e}")

    db.add(Project(
        user_id=user.id, kind="website",
        prompt=body.prompt, output_path=title,
    ))
    db.commit()

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="website-{title}.zip"',
            "X-Credits-Left": str(user.credits),
        },
    )


@app.post("/generate/apk")
async def gen_apk(
    body: PromptIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    consume(user, db, APK_COST)
    try:
        zip_bytes, app_name = await generate_android_project(body.prompt)
    except Exception as e:
        user.credits += APK_COST
        db.commit()
        raise HTTPException(500, f"Generation failed: {e}")

    db.add(Project(
        user_id=user.id, kind="apk",
        prompt=body.prompt, output_path=app_name,
    ))
    db.commit()

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="android-{app_name}.zip"',
            "X-Credits-Left": str(user.credits),
        },
  )
