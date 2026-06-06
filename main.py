from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI(title="Task Manager API")

# In-memory store (students can see data reset on restart — teachable moment)
tasks_db = {}

class TaskCreate(BaseModel):
    title: str

class Task(BaseModel):
    id: str
    title: str
    done: bool = False

@app.post("/tasks", response_model=Task)
def create_task(body: TaskCreate):
    task_id = str(uuid.uuid4())[:8]
    task = Task(id=task_id, title=body.title)
    tasks_db[task_id] = task
    return task

@app.get("/tasks", response_model=List[Task])
def list_tasks():
    return list(tasks_db.values())

@app.patch("/tasks/{task_id}", response_model=Task)
def complete_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks_db[task_id].done = True
    return tasks_db[task_id]

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks_db[task_id]
    return {"deleted": task_id}