from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal

class Node(BaseModel):
    id: str
    type: str  # 'agent', 'start', 'end' etc.
    data: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=dict)

class Edge(BaseModel):
    id: str
    source: str
    target: str

class Workflow(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class RunRequest(BaseModel):
    workflow: Workflow
    prompt: str
    context: Optional[str] = ""
