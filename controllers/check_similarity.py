from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app import auth, models, schemas, security
from app.db import get_db
from app.models import User, Admin
import os
from datetime import datetime
from controllers.similarity_scores import calculate_similarity_multi_source

def check_similarity_multi_table(project: schemas.checkProject, team_id: int, db: Session):
    """
    Check similarity against projects, college ideas, and team projects.
    Add to TeamProject table if similarity is acceptable.
    """
    try:
        cur_date = datetime.now()
        cur_month = cur_date.month
        cur_year = cur_date.year

        # Adjust year for academic calendar
        if cur_month in [10, 11, 12]:
            cur_year += 1
        
        # Fetch from three tables (removing preprojects dependency)
        projects = db.query(models.Project).filter(
            models.Project.year == cur_year
        ).all()
        
        college_ideas = db.query(models.CollegeIdeas).filter(
            models.CollegeIdeas.year == cur_year
        ).all()
        
        team_projects = db.query(models.TeamProject).filter(
            models.TeamProject.year == cur_year
        ).all()

        # Calculate similarities across all sources
        all_similarities = calculate_similarity_multi_source(
            project, projects, college_ideas, team_projects
        )
        
        # Find maximum similarity score
        max_similarity = 0.0
        if all_similarities:
            max_similarity = max([score for _, _, score in all_similarities])
        
        # Check for similar projects (threshold > 0.5)
        similar_projects = [
            (source, title, score) 
            for source, title, score in all_similarities 
            if score > 0.5
        ]

        if similar_projects:
            # Return similar projects found
            return schemas.ProjectIdeaResponse(
                success=False,
                message="There are projects similar to your idea due to DMU policy",
                project_id=None,
                max_similarity_score=f"{max_similarity:.2f}",
                status="rejected",
                similar_projects=[
                    {
                        "source": source, 
                        "title": title, 
                        "similarity_score": f"{score:.2f}"
                    }
                    for source, title, score in similar_projects
                ]
            )
        else:
            # Add to TeamProject table
            try:
                new_team_project = models.TeamProject(
                    team_id=team_id,
                    title=project.title,
                    description=project.description,
                    year=cur_year,
                    maxSimScore=max_similarity,
                    status=models.TeamProjectStatus.PENDING
                )
                db.add(new_team_project)
                db.commit()
                db.refresh(new_team_project)
                
                return schemas.ProjectIdeaResponse(
                    success=True,
                    message="Congratulations! Your project idea has been added successfully",
                    project_id=new_team_project.id,
                    max_similarity_score=f"{max_similarity:.2f}",
                    status="pending",
                    similar_projects=[]
                )
                
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error adding project to database: {str(e)}"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error in similarity check: {str(e)}"
        )