from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from typing import Optional, Union, List
import httpx
from datetime import datetime
from app import auth, models, schemas, security
from app.db import get_db
from app.models import User, Admin, Supervisors, reqStatus, TeamProject, CollegeIdeas, Team, TeamMember
from controllers.check_similarity import check_similarity_multi_table

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/v1/add-project-idea", response_model=schemas.ProjectIdeaResponse)
async def add_project_idea(
    project: schemas.checkProject, 
    cur_user: schemas.UserDB = Depends(auth.getCurrentUser), 
    db: Session = Depends(get_db)
):
    """
    Add a new project idea for a team leader.
    Performs similarity check against existing projects, college ideas, and team projects.
    """
    try:
        # Verify user is team leader
        team_member = db.query(models.TeamMember).filter(
            models.TeamMember.user_email == cur_user.email
        ).first()
        
        if not team_member:
            raise HTTPException(
                status_code=400, 
                detail="You are not a member of any team"
            )
        
        if not team_member.is_leader:
            raise HTTPException(
                status_code=403, 
                detail="Only team leaders can add project ideas"
            )
        
        # Check if team already has a project
        existing_project = db.query(models.TeamProject).filter(
            models.TeamProject.team_id == team_member.team_id
        ).first()
        
        if existing_project:
            raise HTTPException(
                status_code=400, 
                detail="Your team already has a project"
            )
        
        # Call the similarity check function
        return check_similarity_multi_table(project, team_member.team_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in add_project_idea: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@router.get('/v1/student/recommef-for-me', response_model=schemas.RecommendedTeams)
async def recommend_teams(cur_user: schemas.UserDB = Depends(auth.getCurrentUser), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == cur_user.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    dbteams = db.query(models.Team).all()

    teams = [
        {
            "id": str(team.id),
            "title": team.name,
            "skills": ", ".join(team.expec_tools) if team.expec_tools else ""
        }
        for team in dbteams
    ]

    student_info = {
        "id": str(user.id),
        "jobtitle": user.title,
        "skills": ", ".join(user.skills) if user.skills else ""
    }


    payload = {
        "student": student_info,
        "projects": teams
    }

    external_api_url = 'https://recommendation-system-production-390d.up.railway.app/v1/match/student-to-projects'
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(external_api_url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()  # Raise exception for 4xx/5xx responses
            api_response = response.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to external API: {str(e)}")
        raise HTTPException(status_code=503, detail="External recommendation service unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"External API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"External API error: {e.response.status_code}")
    except ValueError as e:
        logger.error(f"Invalid response from external API: {str(e)}")
        raise HTTPException(status_code=500, detail="Invalid response from external API")

    matches = api_response.get("matches", [])
    
    recommended_team_ids = [int(match["project_id"]) for match in matches]
    
    recommended_team_from_db = db.query(models.Team).filter(
        models.Team.id.in_(recommended_team_ids)
    ).all()
    
    team_map = {team.id: team for team in recommended_team_from_db}
    
    recommended_teams = []
    for match in matches:
        team_id = int(match["project_id"])
        if team_id in team_map:
            team = team_map[team_id]
            recommended_teams.append(
                schemas.RecommendedTeam(
                    team_id=team.id,
                    name=team.name,
                    description=team.description,
                    skills = team.expec_tools,
                    similarity_score=match["similarity_score"]
                )
            )

    return schemas.RecommendedTeams(
        matches=recommended_teams,
        total_teams=len(recommended_teams)
    )




@router.get('/v1/team/recommend-for-us', response_model=schemas.RecommendedUsers)
async def recommend_users(cur_user: schemas.UserDB = Depends(auth.getCurrentUser), db: Session = Depends(get_db)):
    leader = db.query(models.TeamMember).filter(models.TeamMember.user_email == cur_user.email).first()
    if leader is None:
        raise HTTPException(status_code=400, detail="You are not a member of any team")
    
    if not leader.is_leader:
        raise HTTPException(status_code=400, detail="You are not the leader of your team")

    # Get team information
    team = db.query(models.Team).filter(models.Team.id == leader.team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get all team member emails for the current team
    team_member_emails = db.query(models.TeamMember.user_email).filter(
        models.TeamMember.team_id == leader.team_id
    ).all()
    team_member_email_list = [email[0] for email in team_member_emails]

    # Get all users EXCLUDING current team members
    users = db.query(models.User).filter(
        ~models.User.email.in_(team_member_email_list)
    ).all()

    # Prepare data for external API (only non-team members)
    students = [
        {
            "id": str(user.id),
            "jobtitle": user.title if user.title else "developer", 
            "skills": ", ".join(user.skills) if user.skills else ""
        }
        for user in users
    ]

    team_info = {
        "id": str(team.id),
        "title": team.name,
        "skills": ", ".join(team.expec_tools) if team.expec_tools else ""
    }

    payload = {
        "project": team_info,
        "students": students
    }

    external_api_url = 'https://recommendation-system-production-390d.up.railway.app/v1/match/projects-to-students'
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(external_api_url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()  # Raise exception for 4xx/5xx responses
            api_response = response.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to external API: {str(e)}")
        raise HTTPException(status_code=503, detail="External recommendation service unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"External API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"External API error: {e.response.status_code}")
    except ValueError as e:
        logger.error(f"Invalid response from external API: {str(e)}")
        raise HTTPException(status_code=500, detail="Invalid response from external API")

    matches = api_response.get("matches", [])
    
    # Extract recommended user IDs from the API response
    recommended_user_ids = [int(match["student_id"]) for match in matches]
    
    # Fetch all recommended users in one query (they should already be excluded, but double-check)
    recommended_users_from_db = db.query(models.User).filter(
        models.User.id.in_(recommended_user_ids),
        ~models.User.email.in_(team_member_email_list)  # Double-check exclusion
    ).all()
    
    # Create a mapping for quick lookup
    user_map = {user.id: user for user in recommended_users_from_db}
    
    # Build the response with actual user data from database
    recommended_users = []
    for match in matches:
        student_id = int(match["student_id"])
        if student_id in user_map:
            user = user_map[student_id]
            recommended_users.append(
                schemas.RecommendedUser(
                    user_id=user.id,
                    username=user.username,
                    firstName=user.firstName,
                    lastName=user.lastName,
                    skills=user.skills if user.skills else [],
                    similarity_score=match["similarity_score"]
                )
            )

    return schemas.RecommendedUsers(
        matches=recommended_users,
        total_users=len(recommended_users)
    )


    

@router.post("/v1/admin/upload-project")
async def upload_projects(data: schemas.ProjectBase, cur_admin: schemas.AdminDB = Depends(auth.getCurrentAdmin), db: Session = Depends(get_db)):
    tools_str = " ".join(data.tools)

    # Check if project title already exists
    if db.query(models.Project).filter(models.Project.title == data.title).first():
        raise HTTPException(status_code=400, detail=f"Project title already exists")

    # Validate unique emails in team members
    emails = [member.email for member in data.team_members]
    if len(emails) != len(set(emails)):
        raise HTTPException(status_code=400, detail="Team members must have unique emails")

    # Create project
    try:
        proj = models.Project(
            title=data.title,
            description=data.description,
            tools=tools_str,
            supervisor=data.supervisor,
            year=data.year,
            uploader=cur_admin.email  # This should be the email string
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)

        # Add team members to project_team_members table
        for member in data.team_members:
            team_member = models.ProjectTeamMember(
                project_id=proj.id,
                firstName=member.firstName,
                lastName=member.lastName,
                email=member.email,
                role=member.role,
                is_leader=member.is_leader
            )
            db.add(team_member)
        
        db.commit()
        return {"message": "Project uploaded successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload project: {str(e)}")

@router.post("/v1/register", response_model=schemas.UserDBBase)
async def register(user: schemas.User, db: Session = Depends(get_db)):
    existing_user = auth.getUser(db, email=user.email)
    existing_admin = auth.getAdmin(db, email=user.email)
    existing_supervisor = auth.getSupervisor(db, email=user.email)
    if existing_user or existing_admin or existing_supervisor:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = security.getHashedPassword(user.password)
    db_user = models.User(
        **user.dict(exclude={'password'}),
        hashed_password=hashed_password
        )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="User creation failed due to duplicate username or email")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")

@router.post("/v1/token", response_model=schemas.Token)
async def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = auth.getUser(db, email=login_data.email)
    is_admin = False
    is_supervisor = False
    
    if not user:
        user = auth.getAdmin(db, email=login_data.email)
        if user:
            is_admin = True
        else:
            user = auth.getSupervisor(db, email=login_data.email)
            if user:
                is_supervisor = True
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    
    if not security.pwd_context.verify(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(
        data={"sub": user.email},
        is_admin=is_admin,
        is_supervisor=is_supervisor
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/v1/add-supervisor", response_model=schemas.SupervisorDBBase)
async def add_supervisor(supervisor_data: schemas.Supervisor, cur_admin: schemas.AdminDB = Depends(auth.getCurrentAdmin), db: Session = Depends(get_db)):
    if cur_admin.degree != 'A':
        raise HTTPException(status_code=403, detail="Only admins with degree A can add supervisors")
    
    existing_user = auth.getUser(db, email=supervisor_data.email)
    existing_admin = auth.getAdmin(db, email=supervisor_data.email)
    existing_supervisor = auth.getSupervisor(db, email=supervisor_data.email)
    if existing_user or existing_admin or existing_supervisor:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = security.getHashedPassword(supervisor_data.password)
    
    new_supervisor = models.Supervisors(
        username=supervisor_data.email,
        email=supervisor_data.email,
        hashed_password=hashed_password,
        firstName=supervisor_data.firstName,
        lastName=supervisor_data.lastName,
        university=supervisor_data.university,
        department=supervisor_data.department
    )
    
    try:
        db.add(new_supervisor)
        db.commit()
        db.refresh(new_supervisor)
        return new_supervisor
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Supervisor creation failed due to duplicate username or email")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add supervisor: {str(e)}")


@router.post("/v1/master/add-admin", response_model=schemas.AdminDBBase)
async def add_admin(admin_data: schemas.Admin, db: Session = Depends(get_db)):
    
    existing_user = auth.getUser(db, email=admin_data.email)
    existing_admin = auth.getAdmin(db, email=admin_data.email)
    existing_supervisor = auth.getSupervisor(db, email=admin_data.email)
    if existing_user or existing_admin or existing_supervisor:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = security.getHashedPassword(admin_data.password)
    
    new_admin = models.Admin(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=hashed_password,
        degree='A',
        added_by='System'
    )
    
    try:
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        return new_admin
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Admin creation failed due to duplicate username or email")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add admin: {str(e)}")

#################################################################
####################################################################

# @router.post("/v1/master/add-admin", response_model=schemas.AdminDBBase)
# async def add_admin(admin_data: schemas.Admin, cur_admin: schemas.AdminDB = Depends(auth.getCurrentAdmin), db: Session = Depends(get_db)):
#     if cur_admin.degree != 'A':
#         raise HTTPException(status_code=403, detail="Only admins with degree A can add other admins")
    
#     existing_user = auth.getUser(db, email=admin_data.email)
#     existing_admin = auth.getAdmin(db, email=admin_data.email)
#     existing_supervisor = auth.getSupervisor(db, email=admin_data.email)
#     if existing_user or existing_admin or existing_supervisor:
#         raise HTTPException(status_code=400, detail="Email already exists")
    
#     hashed_password = security.getHashedPassword(admin_data.password)
    
#     new_admin = models.Admin(
#         username=admin_data.email,
#         email=admin_data.email,
#         hashed_password=hashed_password,
#         degree=admin_data.degree,
#         added_by=cur_admin.username
#     )
    
#     try:
#         db.add(new_admin)
#         db.commit()
#         db.refresh(new_admin)
#         return new_admin
#     except IntegrityError as e:
#         db.rollback()
#         logger.error(f"Database integrity error: {str(e)}")
#         raise HTTPException(status_code=400, detail="Admin creation failed due to duplicate username or email")
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Unexpected error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to add admin: {str(e)}")


# @router.get("/v1/master/admins/{degree}", response_model=list[schemas.AdminResponse])
# @router.get("/v1/master/admins/", response_model=list[schemas.AdminResponse])
# async def get_admins(degree: Optional[str] = None, cur_admin: schemas.AdminDB = Depends(auth.getCurrentAdmin), db: Session = Depends(get_db)):
#     if cur_admin.degree != 'A':
#         raise HTTPException(status_code=403, detail="Only admins with degree A can view other admins")
#     try: 
#         query = db.query(
#             models.Admin.id,
#             models.Admin.username,
#             models.Admin.email,
#             models.Admin.degree,
#             models.Admin.added_by,
#             models.Admin.created_at
#         )
#         if degree is None:
#             admins = query.all()
#         else:
#             admins = query.filter(models.Admin.degree == degree).all()
#         return admins
#     except IntegrityError as e:
#         logger.error(f"Database integrity error: {str(e)}")
#         raise HTTPException(status_code=400, detail="Failed to get admins due to database constraint")
#     except Exception as e:
#         logger.error(f"Unexpected error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to get admins: {str(e)}")

@router.get("/v1/team-ideas", response_model=List[schemas.TeamProjectsResponse])
async def get_teams(
    db: Session = Depends(get_db)
):
    try:
        team_projects = db.query(models.TeamProject).all()
        
        if not team_projects:
            return []
        
        response = []
        
        for team_project in team_projects:
            team = db.query(models.Team).filter(
                models.Team.id == team_project.team_id
            ).first()
            if not team:
                continue  # Skip if team not found rather than raising error
                
            response.append(
                schemas.TeamProjectsResponse(
                    team_project_id=team_project.id,  # Use team_project.id instead of team.id
                    title=team_project.title,
                    status=team_project.status,
                )
            )
            
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in get_team_project_by_title: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve team project: {str(e)}"
        )


@router.get("/v1/team-ideas/{title}", response_model=schemas.TeamProjectResponse)
async def get_team_project_by_title(
    title: str,
    db: Session = Depends(get_db)
):
    try:
        # First, find the team project
        team_project = db.query(models.TeamProject).filter(
            models.TeamProject.title == title
        ).first()
        
        if not team_project:
            raise HTTPException(
                status_code=404, 
                detail=f"Team project with title '{title}' not found"
            )
        
        # Get team information
        team = db.query(models.Team).filter(
            models.Team.id == team_project.team_id
        ).first()
        
        if not team:
            raise HTTPException(
                status_code=404, 
                detail="Team associated with this project not found"
            )
        
        # Get supervisor information through college ideas requests
        # supervisor_info = None
        # college_request = db.query(models.CollegeIdeasRequests).filter(
        #     models.CollegeIdeasRequests.team_id == team.id,
        #     models.CollegeIdeasRequests.status != reqStatus.REJECTED
        # ).first()
        
        # if college_request:
        #     supervisor_info = db.query(models.Supervisors).filter(
        #         models.Supervisors.email == college_request.supervisor_email
        #     ).first()
        
        # Get team members with their user details
        team_members_query = db.query(
            models.TeamMember,
            models.User
        ).join(
            models.User,
            models.TeamMember.user_email == models.User.email
        ).filter(
            models.TeamMember.team_id == team.id
        ).all()
        
        # Build team members list
        team_members = []
        for team_member, user in team_members_query:
            team_members.append(
                schemas.TeamMemberResponse(
                    firstName=user.firstName,
                    lastName=user.lastName,
                    email=user.email,
                    role=team_member.role,
                    is_leader=team_member.is_leader,
                    joined_at=team_member.joined_at
                )
            )
        
        # Build project details
        project_details = {
            "id": team_project.id,
            "title": team_project.title,
            "description": team_project.description,
            "year": team_project.year,
            "maxSimScore": team_project.maxSimScore,
            "status": team_project.status.value if team_project.status else None,
            "created_at": team_project.created_at
        }
        
        # # Build supervisor response if available
        # supervisor_response = None
        # if supervisor_info:
        #     supervisor_response = schemas.SupervisorResponse(
        #         id=supervisor_info.id,
        #         firstName=supervisor_info.firstName,
        #         lastName=supervisor_info.lastName,
        #         username=supervisor_info.username,
        #         email=supervisor_info.email,
        #         university=supervisor_info.university,
        #         department=supervisor_info.department
        #     )
        
        # Build final response
        response = schemas.TeamProjectResponse(
            team_id=team.id,
            team_name=team.name,
            project=project_details,
            team_members=team_members
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_team_project_by_title: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve team project: {str(e)}"
        )



@router.get("/v1/archive/{title}", response_model=schemas.ProjectsResponse)
@router.get("/v1/archive", response_model=list[schemas.ProjectsResponse])
async def get_projects(title: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(
            models.Project.id,
            models.Project.title,
            models.Project.description,
            models.Project.tools,
            models.Project.supervisor,
            models.Project.year,
            models.ProjectTeamMember.firstName,
            models.ProjectTeamMember.lastName,
            models.ProjectTeamMember.email,
            models.ProjectTeamMember.role,
            models.ProjectTeamMember.is_leader
        ).outerjoin(
            models.ProjectTeamMember,
            models.ProjectTeamMember.project_id == models.Project.id
        )

        if title is None:
            projects = query.all()
            result = {}
            for proj in projects:
                proj_id = proj.id
                if proj_id not in result:
                    result[proj_id] = {
                        "id": proj_id,
                        "title": proj.title,
                        "description": proj.description,
                        "tools": proj.tools.split(),
                        "supervisor": proj.supervisor,
                        "year": proj.year,
                        "team_members": []
                    }
                if proj.email:
                    result[proj_id]["team_members"].append(
                        schemas.TeamMemberBase(
                            firstName=proj.firstName,
                            lastName=proj.lastName,
                            email=proj.email,
                            role=proj.role,
                            is_leader=proj.is_leader
                        )
                    )
            return list(result.values())
        else:
            projects = query.filter(models.Project.title == title).all()
            if not projects:
                raise HTTPException(status_code=404, detail=f"Project with title '{title}' not found")
            result = {
                "id": projects[0].id,
                "title": projects[0].title,
                "description": projects[0].description,
                "tools": projects[0].tools.split(),
                "supervisor": projects[0].supervisor,
                "year": projects[0].year,
                "team_members": [
                    schemas.TeamMemberBase(
                        firstName=proj.firstName,
                        lastName=proj.lastName,
                        email=proj.email,
                        role=proj.role,
                        is_leader=proj.is_leader
                    )
                    for proj in projects if proj.email
                ]
            }
            return result
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")

@router.post("/v1/student/create-team", response_model=schemas.TeamResponse)
async def create_team(team: schemas.TeamBase, cur_user: schemas.UserDB = Depends(auth.getCurrentUser), db: Session = Depends(get_db)):
    try:
        # Check for duplicate team name
        if db.query(models.Team).filter(models.Team.name == team.name).first():
            raise HTTPException(status_code=400, detail=f"Team with name '{team.name}' already exists")

        # Validate unique emails and check if users exist
        emails = [member.email for member in team.members]
        if len(emails) != len(set(emails)):
            raise HTTPException(status_code=400, detail="Team members must have unique emails")
        
        # Check if current user is already in a team
        if db.query(models.TeamMember).filter(models.TeamMember.user_email == cur_user.email).first():
            raise HTTPException(status_code=400, detail="You are already a member of another team")

        # Create team
        db_team = models.Team(
            name=team.name,
            description=team.description,
            expec_tools=team.expec_tools or [],
            created_by=cur_user.email
        )
        db.add(db_team)
        db.flush()  # Get the team ID

        # Add current user as leader
        db_member = models.TeamMember(
            user_email=cur_user.email,
            team_id=db_team.id,
            role="Leader",
            is_leader=True
        )
        db.add(db_member)

        # Add other members
        for member in team.members:
            # Skip if it's the current user (already added as leader)
            if member.email == cur_user.email:
                continue
                
            user = db.query(models.User).filter(models.User.email == member.email).first()
            if not user:
                raise HTTPException(status_code=404, detail=f"User with email '{member.email}' does not exist")
            
            # Check if user is already in another team
            if db.query(models.TeamMember).filter(models.TeamMember.user_email == member.email).first():
                raise HTTPException(status_code=400, detail=f"User '{member.email}' is already a member of another team")
            
            db_member = models.TeamMember(
                user_email=member.email,
                team_id=db_team.id,
                role="Member",  # Default role
                is_leader=False
            )
            db.add(db_member)

        db.commit()
        db.refresh(db_team)
        
        # Return team with members
        team_members = db.query(models.TeamMember).filter(models.TeamMember.team_id == db_team.id).all()
        return {
            "id": db_team.id,
            "name": db_team.name,
            "description": db_team.description,
            "created_by": db_team.created_by,
            "created_at": db_team.created_at,
            "members": [
                {
                    "username": tm.user.username if tm.user else "",
                    "email": tm.user_email,
                    "role": tm.role,
                    "is_leader": tm.is_leader,
                    "joined_at": tm.joined_at
                }
                for tm in team_members
            ]
        }

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Team creation failed due to duplicate name or other constraint")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")


@router.get("/v1/college-ideas/{title}", response_model=schemas.CollegeIdeaResponse)
@router.get("/v1/college-ideas", response_model=list[schemas.CollegeIdeaResponse])
async def college_idea(title: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(
            models.CollegeIdeas.title,
            models.CollegeIdeas.description,
            models.CollegeIdeas.year,
            models.CollegeIdeas.status,
            models.Supervisors.id,
            models.Supervisors.firstName,
            models.Supervisors.lastName,
            models.Supervisors.username,
            models.Supervisors.email,
            models.Supervisors.university,
            models.Supervisors.department
        ).join(
            models.Supervisors,
            models.CollegeIdeas.supervisor_email == models.Supervisors.email
        )

        def map_idea(idea):
            return {
                "title": idea.title,
                "description": idea.description,
                "year": idea.year,
                "status": idea.status,
                "supervisor_info": {
                    "id": idea.id,
                    "firstName": idea.firstName,
                    "lastName": idea.lastName,
                    "username": idea.username,
                    "email": idea.email,
                    "university": idea.university,
                    "department": idea.department
                }
            }

        if title is None:
            ideas = query.all()
            return [map_idea(idea) for idea in ideas]
        else:
            idea = query.filter(models.CollegeIdeas.title == title).first()
            if idea is None:
                raise HTTPException(status_code=404, detail=f"College idea with title '{title}' not found")
            return map_idea(idea)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve college ideas: {str(e)}")

@router.post("/v1/student/college-idea-request", response_model=schemas.CollegeIdeaRequestResponse)
async def create_college_idea_request(
    request: schemas.CollegeIdeaRequestBase,
    cur_user: schemas.UserDB = Depends(auth.getCurrentUser),
    db: Session = Depends(get_db)
):
    try:
        # Authenticate user and check if they are a team leader
        team_member = db.query(models.TeamMember).filter(models.TeamMember.user_email == cur_user.email).first()
        if not team_member:
            raise HTTPException(status_code=403, detail="User is not a member of any team")
        if not team_member.is_leader:
            raise HTTPException(status_code=403, detail="Only team leaders can request college ideas")

        # Fetch college idea
        college_idea = db.query(models.CollegeIdeas).filter(models.CollegeIdeas.title == request.college_idea_title).first()
        if not college_idea:
            raise HTTPException(status_code=404, detail=f"College idea with title '{request.college_idea_title}' not found")

        # Validate supervisor existence
        supervisor = db.query(models.Supervisors).filter(models.Supervisors.email == college_idea.supervisor_email).first()
        if not supervisor:
            raise HTTPException(status_code=400, detail="Supervisor associated with the college idea does not exist")

        # Check for existing requests
        existing_request = db.query(models.CollegeIdeasRequests).filter(
            models.CollegeIdeasRequests.team_id == team_member.team_id,
            models.CollegeIdeasRequests.college_idea_title == request.college_idea_title
        ).first()
        if existing_request:
            if existing_request.status == reqStatus.PENDING:
                raise HTTPException(status_code=400, detail="Team has already requested this idea")
            elif existing_request.status == reqStatus.ACCEPTED:
                raise HTTPException(status_code=400, detail="Team has already been accepted for this idea")

        # Create request
        req = models.CollegeIdeasRequests(
            team_id=team_member.team_id,
            college_idea_title=request.college_idea_title,
            status=reqStatus.PENDING,
            supervisor_email=college_idea.supervisor_email
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        res=models.CollegeIdeasRequests(
            team_id=team_member.team_id,
            college_idea_title=request.college_idea_title,
            status=reqStatus.PENDING,
            supervisor_username=supervisor.username
        )
        return res

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(status_code=400, detail="Request creation failed due to database constraint")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create request: {str(e)}")

