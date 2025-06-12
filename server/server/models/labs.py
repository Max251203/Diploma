from pydantic import BaseModel
from typing import Optional, Dict, List, Any


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: str  # "theory", "test", "device_interaction", "code"
    content: Dict[str, Any]
    order_index: int
    max_score: float = 10.0


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    order_index: Optional[int] = None
    max_score: Optional[float] = None


class Task(TaskBase):
    id: int
    lab_id: int
    devices: Optional[List[Dict[str, Any]]] = None


class LabBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Dict[str, Any]


class LabCreate(LabBase):
    tasks: Optional[List[TaskCreate]] = None


class LabUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class Lab(LabBase):
    id: int
    created_by: int
    created_at: str
    updated_at: str
    tasks: Optional[List[Task]] = None


class TaskResultBase(BaseModel):
    task_id: int
    answer: Optional[Dict[str, Any]] = None


class TaskResultCreate(TaskResultBase):
    pass


class TaskResultUpdate(BaseModel):
    answer: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    feedback: Optional[str] = None


class TaskResult(TaskResultBase):
    id: int
    lab_result_id: int
    score: Optional[float] = None
    feedback: Optional[str] = None


class LabResultBase(BaseModel):
    lab_id: int
    user_id: int
    status: str = "in_progress"  # "in_progress", "submitted", "reviewed"


class LabResultCreate(LabResultBase):
    task_results: Optional[List[TaskResultCreate]] = None


class LabResultUpdate(BaseModel):
    status: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None


class LabResult(LabResultBase):
    id: int
    started_at: str
    submitted_at: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[str] = None
    task_results: Optional[List[TaskResult]] = None
