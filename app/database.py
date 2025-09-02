from sqlalchemy import create_engine, Integer, String, Boolean, DateTime
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
    is_verified = Column(Boolean , default=False)
    analyses = relationship("RegionalDisparityAnalysis", back_populates="user")
    formulary_analyses = relationship("FormularyDetailAnalysis", back_populates="user")
    therapeutic_equivalence_analyses = relationship("RecommendationLogDB", back_populates="user")


class RegionalDisparityAnalysis(Base):
    __tablename__ = "regional_disparity_analyses_result" # Corrected table name

    id = Column(Integer, primary_key=True, index=True)
    # MODIFIED: Added lengths to all String columns
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


    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="analyses")


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

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="formulary_analyses")

class RecommendationLogDB(Base):
    __tablename__ = "recommendation_logs"
    id = Column(Integer, primary_key=True, index=True)
    rxcui = Column(Integer, index=True, nullable=False)
    recommended_ingredients = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    # CORRECTED: Pointed back to the correct relationship name
    user = relationship("User", back_populates="therapeutic_equivalence_analyses")


