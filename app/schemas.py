import email
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime
from app.models import reqStatus
from controllers import similarity_scores

class Supervisor(BaseModel):
    username: str
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    university: str
    department: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v

    @validator('firstName', 'lastName')
    def name_valid(cls, v):
        if not v.replace(' ', '').isalpha():
            raise ValueError(f'Name {v} must contain only letters and spaces')
        if len(v) < 2:
            raise ValueError(f'Name {v} must be at least 2 characters long')
        return v

class SupervisorDBBase(BaseModel):
    id: int
    username: str
    email: EmailStr
    firstName: str
    lastName: str
    university: str
    department: str

    class Config:
        from_attributes = True

class SupervisorDB(SupervisorDBBase):
    hashed_password: str

class SupervisorResponse(BaseModel):
    id: int
    firstName: str
    lastName: str
    username: str
    email: EmailStr
    university: str
    department: str

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: EmailStr
    firstName: str
    lastName: str
    skills: Optional[List[str]] = []
    title: Optional[str] = None

    @validator('firstName', 'lastName')
    def name_valid(cls, v):
        if not v.replace(' ', '').isalpha():
            raise ValueError(f'Name {v} must contain only letters and spaces')
        if len(v) < 2:
            raise ValueError(f'Name {v} must be at least 2 characters long')
        return v

class User(UserBase):
    password: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v


class Admin(BaseModel):
    username: str
    email: EmailStr
    password: str
    degree: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v

    @validator('degree')
    def degree_valid(cls, v):
        if v not in ['A', 'B']:
            raise ValueError('Degree must be A or B')
        return v

class UserDBBase(UserBase):
    id: int
    class Config:
        from_attributes = True

class AdminDBBase(BaseModel):
    id: int
    username: str
    email: EmailStr
    degree: str
    class Config:
        from_attributes = True

class UserDB(UserDBBase):
    hashed_password: str

class AdminDB(AdminDBBase):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Modify this in schemas.py
class TeamMemberBase(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: EmailStr
    role: Optional[str] = None
    is_leader: Optional[bool] = False

class ProjectBase(BaseModel):
    title: str
    supervisor: str
    description: str
    tools: List[str]
    year: int
    team_members: List[TeamMemberBase] = []

    @validator('title')
    def title_valid(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v) > 255:
            raise ValueError('Title must be at most 255 characters')
        return v

    @validator('year')
    def year_valid(cls, v):
        current_year = datetime.now().year
        if v < 2023 or v > current_year:
            raise ValueError(f'Year must be between 2023 and {current_year}')
        return v

class ProjectResponse(BaseModel):
    id: int
    title: str
    supervisor: str
    description: str
    tools: List[str]
    year: int
    team_members: List[TeamMemberBase]

    class Config:
        from_attributes = True

class AdminResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    degree: str
    added_by: str

    class Config:
        from_attributes = True

class ProjectsResponse(BaseModel):
    id: int
    title: str
    supervisor: str
    description: str
    tools: List[str]
    year: int
    team_members: List[TeamMemberBase]

    class Config:
        from_attributes = True

class CollegeIdeaBase(BaseModel):
    title: str
    description: str
    year: int

    @validator('title')
    def title_valid(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v) > 100:
            raise ValueError('Title must be at most 100 characters')
        return v

    @validator('year')
    def year_valid(cls, v):
        current_year = datetime.now().year
        if v < 2023 or v > current_year:
            raise ValueError(f'Year must be between 2023 and {current_year}')
        return v

class CollegeIdeaResponse(BaseModel):
    title: str
    description: str
    year: int
    supervisor_info: SupervisorResponse
    status: str

    class Config:
        from_attributes = True

class CollegeIdeaRequestBase(BaseModel):
    college_idea_title: str

    @validator('college_idea_title')
    def title_valid(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('College idea title cannot be empty')
        if len(v) > 100:
            raise ValueError('College idea title must be at most 100 characters')
        return v

class CollegeIdeaRequestResponse(BaseModel):
    id: int
    status: reqStatus
    team_id: int
    college_idea_title: str
    supervisor_username: str

    class Config:
        from_attributes = True

class TeamMemberDetailed(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    title: Optional[str]
    is_leader: bool
    joined_at: datetime

    class Config:
        from_attributes = True

class TeamProjectsResponse(BaseModel):
    team_project_id: int
    title: str
    status: str

    class Config:
        from_attributes = True


class TeamProjectResponse(BaseModel):
    team_id: int
    team_name: str
    project: dict  # Contains id, title, description, year, maxSimScore, status, created_at
    supervisor_info: Optional[SupervisorResponse] = None  # Make this optional
    team_members: List[TeamMemberDetailed]

    class Config:
        from_attributes = True


class RecommendedTeam(BaseModel):
    team_id: int
    name: str
    description: str
    skills: List[str]
    similarity_score: float

    class Config:
        from_attributes = True

class RecommendedTeams(BaseModel):
    matches: List[RecommendedTeam]
    total_teams: int

    class Config:
        from_attributes = True

class RecommendedUser(BaseModel):
    user_id: int
    username: str
    firstName: str
    lastName: str
    title: str
    skills: List[str]
    similarity_score: float

    class Config:
        from_attributes = True

class RecommendedUsers(BaseModel):
    matches: List[RecommendedUser]
    total_users: int

    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    username: str
    email: EmailStr
    role: Optional[str]
    is_leader: bool
    joined_at: datetime

    class Config:
        from_attributes = True

class TeamResponse(BaseModel):
    id: int
    name: str
    description: str
    created_by: str
    created_at: datetime
    members: List[TeamMemberResponse]

    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    name: str
    description: str
    members: List[TeamMemberBase] = []
    expec_tools: Optional[List[str]] = []

    @validator('name')
    def name_valid(cls, v):
        if not v.strip():
            raise ValueError('Team name cannot be empty')
        if len(v) > 100:
            raise ValueError('Team name must be at most 100 characters')
        return v

    @validator('description')
    def description_valid(cls, v):
        if len(v) > 65535:
            raise ValueError('Description must be at most 65535 characters')
        return v


class SimilarProjectDetail(BaseModel):
    title: str
    source: str  # 'projects', 'collegeIdeas', or 'teamProject'
    similarity_score: str

    class Config:
        from_attributes = True

class ProjectSimilarityDetail(BaseModel):
    title: str
    source: str
    similarity_score: str

    class Config:
        from_attributes = True

class AddProjectIdeaResponse(BaseModel):
    message: str
    status: str  # 'added', 'rejected'
    max_similarity: str
    project_id: Optional[int] = None
    similar_projects: Optional[List[SimilarProjectDetail]] = []
    all_similarities: Optional[List[ProjectSimilarityDetail]] = []
    similarity_check: Optional[str] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True

# The existing checkProject schema remains the same
class checkProject(BaseModel):
    title: str
    description: str

class SimilarProject(BaseModel):
    source: str
    title: str
    similarity_score: str

class ProjectIdeaResponse(BaseModel):
    success: bool
    message: str
    project_id: Optional[int] = None
    max_similarity_score: str
    status: str
    similar_projects: List[SimilarProject] = []

    class Config:
        from_attributes = True