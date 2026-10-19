
import os

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    ForeignKey,
    Integer,
    DateTime,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./atlas.db",
)

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


class ReportDB(Base):
    __tablename__ = "reports"

    report_id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    access = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)


class ReportPermissionDB(Base):
    __tablename__ = "report_permissions"

    client_id = Column(String(50), primary_key=True)
    report_id = Column(
        String(50),
        ForeignKey("reports.report_id", ondelete="CASCADE"),
        primary_key=True,
    )


class EscalationDB(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(50), nullable=False, index=True)
    question = Column(Text, nullable=False)
    reason = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False, default="open")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )


def init_db():
    Base.metadata.create_all(bind=engine)
