from fastapi import FastAPI
import uvicorn
from app import models
from app.db import engine
from app.routes import router
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Project Management API",
    description="FastAPI application for project management and AI chat",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check first (before DB operations)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {
        "message": "Project Management API is running!",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Create tables if they don't exist
try:
    models.Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Database table creation warning: {e}")


# Include routers
app.include_router(router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app=app, host="0.0.0.0", port=port)
    # uvicorn.run(app=app, host="127.0.0.1", port=port)

