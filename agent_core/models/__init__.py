"""
Data models and schemas for LANS system.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Status of a task in the generation pipeline."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class AgentType(str, Enum):
    """Types of agents in the system."""
    PLANNING = "planning"
    CODING = "coding"
    COORDINATOR = "coordinator"
    CREATIVE_AGENT = "creative_agent"


class Task(BaseModel):
    """Individual task in the project generation pipeline."""
    id: str = Field(description="Unique task identifier")
    description: str = Field(description="Human-readable task description")
    dependencies: List[str] = Field(default=[], description="List of task IDs this depends on")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    assigned_agent: Optional[AgentType] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default={})


class ProjectSpec(BaseModel):
    """Specification for a software project to be generated."""
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    project_type: str = Field(default="general", description="Type of project (web, cli, api, desktop, etc.)")
    language: str = Field(default="python", description="Primary programming language")
    framework: Optional[str] = Field(default=None, description="Framework to use (fastapi, flask, react, etc.)")
    dependencies: List[str] = Field(default=[], description="Package dependencies")
    features: List[str] = Field(default=[], description="List of features to implement")
    structure: Dict[str, Any] = Field(default={}, description="Project structure specifications")
    configuration: Dict[str, Any] = Field(default={}, description="Project configuration")
    metadata: Dict[str, Any] = Field(default={}, description="Additional project metadata")


class GenerationRequest(BaseModel):
    """Request to generate a software project."""
    user_prompt: str = Field(description="Natural language description of desired project")
    output_directory: str = Field(description="Where to generate the project")
    project_spec: Optional[ProjectSpec] = None
    preferences: Dict[str, Any] = Field(default={})


class AgentMessage(BaseModel):
    """Message passed between agents."""
    sender: AgentType
    recipient: Optional[AgentType] = None
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class BuildResult(BaseModel):
    """Result of building a project."""
    success: bool
    output: str = Field(description="Build command output")
    errors: List[str] = Field(default=[])
    warnings: List[str] = Field(default=[])
    build_time: float = Field(description="Build time in seconds")


class ValidationResult(BaseModel):
    """Result of validating generated code."""
    passed: bool
    test_results: List[Dict[str, Any]] = Field(default=[])
    errors: List[str] = Field(default=[])
    coverage: Optional[float] = None


class ProjectState(BaseModel):
    """Overall state of the project generation."""
    request: GenerationRequest
    tasks: List[Task] = Field(default=[])
    current_task_id: Optional[str] = None
    project_spec: Optional[ProjectSpec] = None
    generated_files: List[str] = Field(default=[])
    build_results: List[BuildResult] = Field(default=[])
    validation_results: List[ValidationResult] = Field(default=[])
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
