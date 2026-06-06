from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
import uuid

app = FastAPI(title="Task Manager API")

DB_PATH = "tasks.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


init_db()


class TaskCreate(BaseModel):
    title: str


class Task(BaseModel):
    id: str
    title: str
    done: bool = False


@app.post("/tasks", response_model=Task)
def create_task(body: TaskCreate):
    task_id = str(uuid.uuid4())[:8]
    conn = get_db()
    conn.execute("INSERT INTO tasks (id, title, done) VALUES (?, ?, 0)", (task_id, body.title))
    conn.commit()
    conn.close()
    return Task(id=task_id, title=body.title, done=False)


@app.get("/tasks", response_model=List[Task])
def list_tasks():
    conn = get_db()
    rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
    conn.close()
    return [Task(id=row["id"], title=row["title"], done=bool(row["done"])) for row in rows]


@app.patch("/tasks/{task_id}", response_model=Task)
def complete_task(task_id: str):
    conn = get_db()
    row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return Task(id=row["id"], title=row["title"], done=True)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    conn = get_db()
    row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"deleted": task_id}
