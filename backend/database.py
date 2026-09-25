import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Neon gives you TWO strings:
#   - Direct:  postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/db
#   - Pooled:  postgresql://user:pass@ep-xxx-pooler.us-east-2.aws.neon.tech/db
# USE THE POOLED ONE for Vercel[reference:11].
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
