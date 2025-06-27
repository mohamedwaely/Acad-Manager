# Acad-Manager
The Project Management API is a component of a comprehensive Graduation Project Management System designed to streamline the process of managing graduation projects in colleges. This system facilitates collaboration among three user types—Admins, Supervisors, and Students—from team creation to project submission. The API provides core functionalities such as user authentication, project and team management, similarity checks for project ideas, and recommendation systems for team and student matching.

## Badges
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0-blue.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-blue.svg)](https://www.mysql.com/)
[![Git](https://img.shields.io/badge/Git-2.33+-blue.svg)](https://git-scm.com/)
[![JWT](https://img.shields.io/badge/JWT-Auth-blue.svg)](https://jwt.io/)
[![bcrypt](https://img.shields.io/badge/bcrypt-3.2.0-blue.svg)](https://pypi.org/project/bcrypt/)
[![TF-IDF](https://img.shields.io/badge/TF--IDF-Similarity-blue.svg)](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)

## video demo
[video](https://drive.google.com/file/d/1lLzJWSNxQpqYcVwbgBHjs13liTdWQ4Q9/view?pli=1)

## screenshots
![login](./imgs/login.png)
![dashboard](./imgs/dashboard.png)
![dashboard](./imgs/dashboard-2.png)
![archive](./imgs/archive.png)
![supervisors-ideas](./imgs/supervisors_ideas.png)
![team-ideas](./imgs/team-ideas.png)
![create-team](./imgs/create-team.png)
![teams](./imgs/teams.png)
![tasks](./imgs/tasks.png)
![chat](./imgs/chat.png)
![chat-response](./imgs/chat-response.png)
![recommend-for-student](./imgs/recommend-for-student.png)
![recomend-for-team](./imgs/recommend-for-team.png)

## Features
### User Authentication:
JWT-based authentication for Students, Supervisors, and Admins.
Role-based access control for different user types.
Secure password hashing using bcrypt.

### Team Management:
Students can create teams and invite members.
Team leaders can propose project ideas and request college ideas from supervisors.
Integration with an external recommendation system to suggest teams for students and students for teams based on skills and project requirements.

### Project Management:
Admins can upload projects with associated team members.
Team leaders can submit project ideas, which are checked for similarity against existing projects, college ideas, and team projects.
Similarity checks use TF-IDF and cosine similarity to ensure originality.

### College Ideas:
Supervisors can propose college ideas for student teams to adopt.
Students can request to work on these ideas, with status tracking (Pending, Accepted, Rejected).

### Recommendation System:
Matches students to teams and teams to students based on skills and project requirements using an external API.
Returns similarity scores to guide decision-making.

### Database Integration:
MySQL database with SQLAlchemy ORM for managing users, teams, projects, and college ideas.
Robust schema design with relationships and constraints for data integrity.

### Task Management
Supervisor can upload, delete the tasks
Students can upload, delete the task answers

### Chatbot
This will be a support for students to help them manage the project.
Also will recommend Project Ideas for the teams


### Tech/Frameworks Used
Python
FastAPI
Flask
Scikit-learn
MySQL with SQLAlchemy ORM
JWT
React.js
JavaScript
Flutter
Dart
PHP
Laravel
Git
Postman

## Contributers
@AhmedAbdelhadyISmail
@mansour3432
@mohamedwaely
@AmiraAbdEl-Rahman
@MostafaHikal
@MohamedKandil
@BasmalaAbu-zaid
@AbdelrahmaAreef
@FathySaid
