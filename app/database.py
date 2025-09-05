from sqlalchemy import create_engine, Integer, String, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from dotenv import load_dotenv
from datetime import datetime

from sqlalchemy.sql.schema import Column, ForeignKey

load_dotenv()
DATABASE_URL =os.getenv("DATABASE_URL")

engine =create_engine(DATABASE_URL,echo=False,pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(200))
    is_verified = Column(Boolean, default=False)
    role = Column(String(20), default="user", nullable=False)


    regional_disparity_logs = relationship("RegionalDisparityAnalysis", back_populates="user")
    formulary_detail_logs = relationship("FormularyDetailAnalysis", back_populates="user")
    therapeutic_equivalent_logs = relationship("TherapeuticEquivalentLog", back_populates="user")

    @property
    def is_superuser(self):
        return self.role == "superuser"


class RegionalDisparityAnalysis(Base):
    __tablename__ = "regional_disparity_analyses_result"

    id = Column(Integer, primary_key=True, index=True)
    input_rxcui = Column(String(50), index=True)
    rxcui = Column(String(50), index=True)
    status = Column(String(50))
    total_plans_covering_drug = Column(Integer, nullable=True)
    states_with_coverage = Column(String(50), nullable=True)
    coverage_gap_percentage = Column(String(50), nullable=True)
    drug_tier = Column(String(50), nullable=True)
    prior_auth_required = Column(String(10), nullable=True)
    step_therapy_required = Column(String(10), nullable=True)
    missing_states = Column(String(1000), nullable=True)
    disparity_message = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="regional_disparity_logs")


class FormularyDetailAnalysis(Base):
    __tablename__ = "formulary_detail_analyses_result"

    id = Column(Integer, primary_key=True, index=True)
    drug_rxcui = Column(String(50), index=True)
    status = Column(String(50))
    plan_name = Column(String(255))
    tier = Column(String(50))
    restrictions = Column(String(500))
    indications = Column(String(1000))
    preferred_cost = Column(String(50))
    non_preferred_cost = Column(String(50))
    state = Column(String(100))
    county_code = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="formulary_detail_logs")


class TherapeuticEquivalentLog(Base):
    __tablename__ = "therapeutic_equivalent_logs"

    id = Column(Integer, primary_key=True, index=True)
    input_rxcui = Column(Integer, index=True)
    input_cost = Column(Float)
    input_ingredient = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="therapeutic_equivalent_logs")
    alternatives = relationship("TherapeuticEquivalentAlternative", back_populates="log_entry", cascade="all, delete-orphan")


class TherapeuticEquivalentAlternative(Base):
    __tablename__ = "therapeutic_equivalent_alternatives"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("therapeutic_equivalent_logs.id"))

    ingredient = Column(String(255))
    alternative_rxcui = Column(Integer)
    alternative_cost = Column(Float)
    cost_difference = Column(Float)
    percentage_reduction = Column(String(20))

    log_entry   = relationship("TherapeuticEquivalentLog", back_populates="alternatives")

