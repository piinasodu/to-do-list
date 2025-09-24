# FastAPI To-Do List Backend
# Session-based in-memory storage

# ============ IMPORTS ============
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List
import uvicorn

# ============ APP INITIALIZATION ============
app = FastAPI(
    title="Session To-Do List API",
    description="A simple in-memory To-Do List API with session-based storage",
    version="1.0.0"
)

# Serve static files (frontend) at /static
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ DATA STORAGE ============
# In-memory storage (cleared on server restart)
tasks_storage: List[dict] = []
next_task_id: int = 1

# ============ PYDANTIC MODELS ============
class TaskCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=200, description="Task description")

class TaskResponse(BaseModel):
    id: int = Field(..., description="Unique task identifier")
    text: str = Field(..., description="Task description")

class TaskListResponse(BaseModel):
    tasks: List[TaskResponse] = Field(default=[], description="List of tasks")

# ============ HELPER FUNCTIONS ============
def find_task_by_id(task_id: int) -> dict:
    """Find a task by its ID in the storage."""
    for task in tasks_storage:
        if task["id"] == task_id:
            return task
    return None

def create_task_object(task_text: str) -> dict:
    """Create a new task object with unique ID."""
    global next_task_id
    task = {
        "id": next_task_id,
        "text": task_text.strip()
    }
    next_task_id += 1
    return task

# ============ API ROUTES ============

@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Session To-Do List API",
        "version": "1.0.0",
        "endpoints": {
            "GET /tasks": "Get all tasks",
            "POST /tasks": "Create a new task",
            "DELETE /tasks/{id}": "Delete a task by ID"
        },
        "total_tasks": len(tasks_storage)
    }

@app.get("/tasks", 
         response_model=List[TaskResponse], 
         summary="Get all tasks",
         description="Retrieve all tasks from in-memory storage")
async def get_tasks():
    """
    Get all tasks.
    
    Returns:
        List[TaskResponse]: List of all tasks with id and text
    """
    return [TaskResponse(id=task["id"], text=task["text"]) for task in tasks_storage]

@app.post("/tasks", 
          response_model=TaskResponse, 
          status_code=status.HTTP_201_CREATED,
          summary="Create a new task",
          description="Create a new task with auto-generated unique ID")
async def create_task(task_data: TaskCreate):
    """
    Create a new task.
    
    Args:
        task_data (TaskCreate): Task data containing text
        
    Returns:
        TaskResponse: Created task with unique ID
    """
    # Create new task with unique ID
    new_task = create_task_object(task_data.text)
    
    # Add to storage
    tasks_storage.append(new_task)
    
    # Return created task
    return TaskResponse(id=new_task["id"], text=new_task["text"])

@app.delete("/tasks/{task_id}", 
            status_code=status.HTTP_200_OK,
            summary="Delete a task",
            description="Delete a task by its unique ID")
async def delete_task(task_id: int):
    """
    Delete a task by ID.
    
    Args:
        task_id (int): Unique identifier of the task to delete
        
    Returns:
        dict: Confirmation message
        
    Raises:
        HTTPException: 404 if task not found
    """
    # Find task by ID
    task_to_delete = find_task_by_id(task_id)
    
    if not task_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    # Remove task from storage
    tasks_storage.remove(task_to_delete)
    
    return {
        "message": f"Task with id {task_id} deleted successfully",
        "deleted_task": {
            "id": task_to_delete["id"],
            "text": task_to_delete["text"]
        }
    }

# ============ HEALTH CHECK ============
@app.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "tasks_count": len(tasks_storage),
        "next_id": next_task_id
    }

# ============ RUN SERVER ============
if __name__ == "__main__":
    print("🚀 Starting Session To-Do List API...")
    print("📝 In-memory storage - tasks will be cleared on restart")
    print("🌐 CORS enabled for frontend connection")
    print("📚 API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",  # Change "main" to your filename if different
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )