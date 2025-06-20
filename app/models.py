from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey, DateTime, Enum, Float, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
import enum
from datetime import datetime

class reqStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class TeamProjectStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    firstName = Column(String(255), nullable=False)
    lastName = Column(String(255), nullable=False)
    skills = Column(JSON, nullable=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Fixed relationship
    team_memberships = relationship("TeamMember", back_populates="user")
    
    __table_args__ = (
        UniqueConstraint('username', name='uq_user_username'),
        UniqueConstraint('email', name='uq_user_email'),
    )


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    degree = Column(String(1), nullable=False)
    added_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    projects = relationship("Project", back_populates="uploader_admin")

class Supervisors(Base):
    __tablename__ = "supervisors"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    firstName = Column(String(255), nullable=False)
    lastName = Column(String(255), nullable=False)
    university = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    college_ideas = relationship("CollegeIdeas", back_populates="supervisor")
    college_ideas_requests = relationship("CollegeIdeasRequests", back_populates="supervisor")
    __table_args__ = (
        UniqueConstraint('username', name='uq_supervisor_username'),
        UniqueConstraint('email', name='uq_supervisor_email'),
    )

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    tools = Column(Text, nullable=False)
    uploader = Column(String(255), ForeignKey("admins.email"), nullable=False)  # This should match the Admin email
    supervisor = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploader_admin = relationship("Admin", back_populates="projects")
    team_members = relationship("ProjectTeamMember", back_populates="project")

class ProjectTeamMember(Base):
    __tablename__ = "project_team_members"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    firstName = Column(String(255), nullable=False)
    lastName = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    is_leader = Column(Boolean, default=False, nullable=False)
    project = relationship("Project", back_populates="team_members")
    __table_args__ = (
        UniqueConstraint('project_id', 'email', name='uq_project_team_member'),
        Index('idx_project_team_member_email', 'email'),
    )

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    created_by = Column(String(255), ForeignKey("users.email"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("TeamMember", back_populates="team")
    projects = relationship("TeamProject", back_populates="team")
    expec_tools = Column(JSON, nullable=True)
    college_ideas_requests = relationship("CollegeIdeasRequests", back_populates="team")
    __table_args__ = (
        UniqueConstraint('name', name='uq_team_name'),
    )

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    role = Column(String(255), nullable=True)
    is_leader = Column(Boolean, default=False, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Fixed relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    
    __table_args__ = (
        UniqueConstraint('team_id', 'user_email', name='uq_team_member'),
        UniqueConstraint('user_email', name='uq_user_team'),
    )

class TeamProject(Base):
    __tablename__ = "team_projects"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    title = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    maxSimScore = Column(Float, nullable=True)
    status = Column(Enum(TeamProjectStatus), default=TeamProjectStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    team = relationship("Team", back_populates="projects")
    __table_args__ = (
        UniqueConstraint('team_id', name='uq_team_project_team_id'),
        UniqueConstraint('title', name='uq_team_project_title'),
    )

class CollegeIdeas(Base):
    __tablename__ = "college_ideas"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    supervisor_email = Column(String(255), ForeignKey("supervisors.email"), nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    supervisor = relationship("Supervisors", back_populates="college_ideas")
    requests = relationship("CollegeIdeasRequests", back_populates="college_idea")
    __table_args__ = (
        UniqueConstraint('title', name='uq_college_idea_title'),
    )

class CollegeIdeasRequests(Base):
    __tablename__ = "college_ideas_requests"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    college_idea_title = Column(String(255), ForeignKey("college_ideas.title"), nullable=False)
    status = Column(Enum(reqStatus), default=reqStatus.PENDING, nullable=False)
    supervisor_email = Column(String(255), ForeignKey("supervisors.email"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    team = relationship("Team", back_populates="college_ideas_requests")
    college_idea = relationship("CollegeIdeas", back_populates="requests")
    supervisor = relationship("Supervisors", back_populates="college_ideas_requests")
    __table_args__ = (
        UniqueConstraint('team_id', 'college_idea_title', name='uq_team_college_idea_request'),
    )

    