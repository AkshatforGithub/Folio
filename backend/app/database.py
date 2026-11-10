from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, Text
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    "postgresql://flowwatch:password@db:5432/flowwatch",
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Run(Base):
    """Normalized n8n workflow run record for Flowwatch."""
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    instance = Column(String, default="n8n-local")
    execution_id = Column(String, unique=True, index=True, nullable=False)
    workflow_id = Column(String, index=True, nullable=False)
    workflow_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    duration = Column(Float)
    error_message = Column(Text)
    failing_node_name = Column(String)
    failing_node_type = Column(String)