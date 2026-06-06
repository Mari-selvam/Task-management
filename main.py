from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
import sqlite3
import uuid
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

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
    logger.info("Database initialised")


init_db()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000)
    logger.info("%s %s %s %dms", request.method, request.url.path, response.status_code, duration_ms)
    return response


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
    logger.info("Created task %s: %s", task_id, body.title)
    return Task(id=task_id, title=body.title, done=False)


@app.get("/tasks", response_model=List[Task])
def list_tasks():
    conn = get_db()
    rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
    conn.close()
    logger.info("Listed %d tasks", len(rows))
    return [Task(id=row["id"], title=row["title"], done=bool(row["done"])) for row in rows]


@app.patch("/tasks/{task_id}", response_model=Task)
def complete_task(task_id: str):
    conn = get_db()
    row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        logger.warning("complete_task: task %s not found", task_id)
        raise HTTPException(status_code=404, detail="Task not found")
    conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    logger.info("Completed task %s", task_id)
    return Task(id=row["id"], title=row["title"], done=True)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    conn = get_db()
    row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        logger.warning("delete_task: task %s not found", task_id)
        raise HTTPException(status_code=404, detail="Task not found")
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    logger.info("Deleted task %s", task_id)
    return {"deleted": task_id}
