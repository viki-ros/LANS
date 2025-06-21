"""
LANS Result Types
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

@dataclass
class LANSResult:
    """Result of a LANS operation"""
    
    success: bool = False
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    # Files and directories created/modified
    files_created: List[Path] = field(default_factory=list)
    files_modified: List[Path] = field(default_factory=list)
    directories_created: List[Path] = field(default_factory=list)
    
    # Commands executed
    commands_executed: List[str] = field(default_factory=list)
    command_outputs: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    execution_time: Optional[float] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate the result object structure."""
        try:
            # Basic validation rules
            if self.success and self.error:
                return False  # Can't be successful and have error
            
            if not self.success and not self.error and not self.message:
                return False  # Failed results should have error or message
            
            # Validate data structure if present
            if self.data is not None and not isinstance(self.data, dict):
                return False
            
            return True
        except Exception:
            return False
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_file_created(self, file_path: Path):
        """Add a created file to the result"""
        self.files_created.append(file_path)
    
    def add_file_modified(self, file_path: Path):
        """Add a modified file to the result"""
        self.files_modified.append(file_path)
    
    def add_directory_created(self, dir_path: Path):
        """Add a created directory to the result"""
        self.directories_created.append(dir_path)
    
    def add_command_executed(self, command: str, output: str = ""):
        """Add an executed command to the result"""
        self.commands_executed.append(command)
        if output:
            self.command_outputs[command] = output
    
    def set_error(self, error_message: str):
        """Set error state"""
        self.success = False
        self.error = error_message
    
    def set_success(self, message: str = "Operation completed successfully"):
        """Set success state"""
        self.success = True
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "success": self.success,
            "message": self.message,
            "error": self.error,
            "files_created": [str(f) for f in self.files_created],
            "files_modified": [str(f) for f in self.files_modified],
            "directories_created": [str(d) for d in self.directories_created],
            "commands_executed": self.commands_executed,
            "command_outputs": self.command_outputs,
            "execution_time": self.execution_time,
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
            "metadata": self.metadata,
        }