"""
AIL (Agent Instruction Language) v3.0 Parser
Handles parsing and validation of AIL S-expressions for the AgentOS Kernel.
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class AILOperation(Enum):
    """Supported AIL operations for AIL-3.1."""
    # Core AIL-3.0 operations
    QUERY = "QUERY"
    EXECUTE = "EXECUTE" 
    PLAN = "PLAN"
    COMMUNICATE = "COMMUNICATE"
    ANALYZE = "ANALYZE"               # Analysis and reasoning operation
    
    # Advanced AIL-3.1 operations
    LET = "LET"                    # Variable binding and scoping
    TRY = "TRY"                    # Error handling with recovery
    ON_FAIL = "ON-FAIL"           # Error recovery clause
    AWAIT = "AWAIT"               # Asynchronous flow control
    SANDBOXED_EXECUTE = "SANDBOXED-EXECUTE"  # Secure tool execution
    CLARIFY = "CLARIFY"           # Intent disambiguation
    EVENT = "EVENT"               # Event definition and handling


@dataclass
class Entity:
    """Represents an AIL entity with identifier and vector."""
    identifier: str
    vector: Optional[List[float]] = None
    
    def __str__(self):
        return f"[{self.identifier}:{len(self.vector) if self.vector else 0}D]"


@dataclass  
class CognitionNode:
    """Represents a parsed AIL cognition as a tree node."""
    operation: AILOperation
    arguments: List[Union['CognitionNode', Entity, Dict, str, int, float, bool, None]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        args_str = " ".join(str(arg) for arg in self.arguments)
        return f"({self.operation.value} {args_str})"


class AILParseError(Exception):
    """Exception raised for AIL parsing errors."""
    pass


class AILSecurityError(Exception):
    """Exception raised for AIL security violations."""
    pass


class AILParser:
    """
    Secure, robust parser for AIL-3.0 S-expressions.
    
    Parses AIL code into executable cognition trees while enforcing
    security constraints and validating syntax.
    """
    
    def __init__(self, max_depth: int = 10, max_tokens: int = 1000):
        """
        Initialize the AIL parser.
        
        Args:
            max_depth: Maximum nesting depth for security
            max_tokens: Maximum number of tokens for security
        """
        self.max_depth = max_depth
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)
        
        # Optimized combined regex pattern for better performance
        # Order matters: more specific patterns first
        combined_pattern = (
            r'(?P<STRING>"(?:[^"\\]|\\.)*")|'
            r'(?P<FLOAT>-?\d+\.\d+)|'
            r'(?P<INTEGER>-?\d+)|'
            r'(?P<BOOLEAN>true|false)|'
            r'(?P<NULL>null)|'
            r'(?P<OPERATION>[A-Z][A-Z0-9_-]*[A-Z0-9]|[A-Z])|'
            r'(?P<IDENTIFIER>[a-zA-Z_][a-zA-Z0-9_-]*)|'
            r'(?P<LPAREN>\()|'
            r'(?P<RPAREN>\))|'
            r'(?P<LBRACKET>\[)|'
            r'(?P<RBRACKET>\])|'
            r'(?P<LBRACE>\{)|'
            r'(?P<RBRACE>\})|'
            r'(?P<COLON>:)|'
            r'(?P<COMMA>,)|'
            r'(?P<WHITESPACE>\s+)'
        )
        
        self.tokenizer_regex = re.compile(combined_pattern)
        
        # Keep legacy patterns for fallback if needed
        self.token_patterns = [
            (r'\(', 'LPAREN'),
            (r'\)', 'RPAREN'), 
            (r'\[', 'LBRACKET'),
            (r'\]', 'RBRACKET'),
            (r'\{', 'LBRACE'),
            (r'\}', 'RBRACE'),
            (r'"(?:[^"\\]|\\.)*"', 'STRING'),
            (r'-?\d+\.\d+', 'FLOAT'),
            (r'-?\d+', 'INTEGER'),
            (r'true|false', 'BOOLEAN'),
            (r'null', 'NULL'),
            (r'[A-Z][A-Z0-9_-]*[A-Z0-9]|[A-Z]', 'OPERATION'),
            (r'[a-zA-Z_][a-zA-Z0-9_-]*', 'IDENTIFIER'),
            (r':', 'COLON'),
            (r',', 'COMMA'),
            (r'\s+', 'WHITESPACE'),
        ]
    
    def tokenize(self, ail_code: str) -> List[tuple]:
        """
        Tokenize AIL code into tokens using optimized regex.
        
        Args:
            ail_code: The AIL S-expression string
            
        Returns:
            List of (token_type, value, position) tuples
            
        Raises:
            AILParseError: If tokenization fails
            AILSecurityError: If security limits are exceeded
        """
        tokens = []
        position = 0
        line_num = 1
        col_num = 1
        
        while position < len(ail_code):
            # Use optimized combined regex first
            match = self.tokenizer_regex.match(ail_code, position)
            
            if match:
                # Find which group matched
                token_type = None
                value = None
                
                for group_name, group_value in match.groupdict().items():
                    if group_value is not None:
                        token_type = group_name
                        value = group_value
                        break
                
                if token_type and value:
                    # Skip whitespace but track position for error reporting
                    if token_type != 'WHITESPACE':
                        tokens.append((token_type, value, position, line_num, col_num))
                        
                        # Security check: token limit with context
                        if len(tokens) > self.max_tokens:
                            context = self._get_error_context(ail_code, position, line_num, col_num)
                            raise AILSecurityError(
                                f"Token limit exceeded: {len(tokens)} > {self.max_tokens}\n{context}"
                            )
                    
                    # Update position tracking
                    for char in value:
                        if char == '\n':
                            line_num += 1
                            col_num = 1
                        else:
                            col_num += 1
                    
                    position = match.end()
                else:
                    # Should not happen with our regex, but handle gracefully
                    context = self._get_error_context(ail_code, position, line_num, col_num)
                    raise AILParseError(
                        f"Regex matched but no group found at line {line_num}, col {col_num}\n{context}"
                    )
            else:
                # No match found - provide detailed error context
                context = self._get_error_context(ail_code, position, line_num, col_num)
                char = ail_code[position] if position < len(ail_code) else 'EOF'
                raise AILParseError(
                    f"Invalid character '{char}' at line {line_num}, col {col_num}\n{context}"
                )
        
        return tokens
    
    def _get_error_context(self, ail_code: str, position: int, line_num: int, col_num: int, context_size: int = 20) -> str:
        """
        Generate error context showing the problematic area in the code.
        
        Args:
            ail_code: The full AIL code
            position: Error position
            line_num: Line number of error
            col_num: Column number of error
            context_size: Number of characters to show before/after error
            
        Returns:
            Formatted error context string
        """
        start = max(0, position - context_size)
        end = min(len(ail_code), position + context_size)
        
        context_text = ail_code[start:end]
        pointer_pos = position - start
        
        # Create pointer line
        pointer_line = ' ' * pointer_pos + '^'
        
        return f"Context:\n{context_text}\n{pointer_line}\nAt line {line_num}, column {col_num}"
    
    def parse_value(self, tokens: List[tuple], index: int) -> tuple:
        """
        Parse a value (literal, entity, or metadata) starting at index.
        
        Args:
            tokens: List of tokens
            index: Current position in tokens
            
        Returns:
            (parsed_value, new_index) tuple
        """
        if index >= len(tokens):
            raise AILParseError("Unexpected end of input")
        
        token_info = tokens[index]
        token_type = token_info[0]
        value = token_info[1]
        pos = token_info[2] if len(token_info) > 2 else 0
        line_num = token_info[3] if len(token_info) > 3 else 1
        col_num = token_info[4] if len(token_info) > 4 else 1
        
        # String literal
        if token_type == 'STRING':
            # Remove quotes and handle escape sequences
            unquoted = value[1:-1]
            unescaped = unquoted.replace('\\"', '"').replace('\\\\', '\\')
            return unescaped, index + 1
        
        # Number literals
        elif token_type == 'INTEGER':
            return int(value), index + 1
        elif token_type == 'FLOAT':
            return float(value), index + 1
        
        # Boolean and null
        elif token_type == 'BOOLEAN':
            return value == 'true', index + 1
        elif token_type == 'NULL':
            return None, index + 1
        
        # Entity: [identifier:vector] or array: [value, ...]
        elif token_type == 'LBRACKET':
            # Look ahead to distinguish between entity and array
            if index + 1 < len(tokens):
                next_token_type = tokens[index + 1][0]
                
                # If next token is IDENTIFIER, check if this is an entity
                if next_token_type == 'IDENTIFIER':
                    # Look at the token after identifier to decide
                    if index + 2 < len(tokens):
                        third_token_type = tokens[index + 2][0]
                        if third_token_type in ('RBRACKET', 'COLON'):
                            # This is an entity: [identifier] or [identifier:...]
                            return self.parse_entity(tokens, index)
                
                # Otherwise, treat as array
                return self.parse_array(tokens, index)
            else:
                raise AILParseError(f"Incomplete bracket expression at line {line_num}, col {col_num}")
        
        # Metadata: {key: value, ...}
        elif token_type == 'LBRACE':
            return self.parse_metadata(tokens, index)
        
        else:
            raise AILParseError(
                f"Unexpected token: {token_type} at line {line_num}, col {col_num}"
            )
    
    def parse_entity(self, tokens: List[tuple], index: int) -> tuple:
        """Parse an entity [identifier:vector] or [identifier] (simplified)."""
        if tokens[index][0] != 'LBRACKET':
            raise AILParseError("Expected '[' for entity")
        
        index += 1  # Skip '['
        
        # Debug: Check what we have at this position
        if index >= len(tokens):
            raise AILParseError("Unexpected end of tokens in entity")
        
        # Parse identifier
        if tokens[index][0] != 'IDENTIFIER':
            # More detailed error with actual token info
            actual_token = tokens[index] if index < len(tokens) else "EOF"
            raise AILParseError(f"Expected identifier in entity, got {actual_token}")
        
        identifier = tokens[index][1]
        index += 1
        
        # Check if we have a colon (full format) or closing bracket (simplified format)
        vector = None
        if index < len(tokens) and tokens[index][0] == 'COLON':
            # Full format: [identifier:vector]
            index += 1  # Skip ':'
            
            # For now, we'll represent vectors as identifiers or skip them
            # In a full implementation, vectors would be binary data
            if index < len(tokens) and tokens[index][0] == 'IDENTIFIER':
                # Vector placeholder or reference
                vector = tokens[index][1]
                index += 1
        # If no colon, this is simplified format: [identifier]
        
        # Parse closing bracket
        if index >= len(tokens) or tokens[index][0] != 'RBRACKET':
            actual_token = tokens[index] if index < len(tokens) else "EOF"
            raise AILParseError(f"Expected ']' to close entity, got {actual_token}")
        
        index += 1
        
        return Entity(identifier=identifier, vector=vector), index
    
    def parse_array(self, tokens: List[tuple], index: int) -> tuple:
        """Parse an array [value, value, ...]."""
        if tokens[index][0] != 'LBRACKET':
            raise AILParseError("Expected '[' for array")
        
        index += 1  # Skip '['
        array = []
        
        # Handle empty array
        if index < len(tokens) and tokens[index][0] == 'RBRACKET':
            return array, index + 1
        
        while index < len(tokens):
            # Parse value
            value, index = self.parse_value(tokens, index)
            array.append(value)
            
            # Check for comma or end
            if index >= len(tokens):
                raise AILParseError("Unexpected end in array")
            
            if tokens[index][0] == 'COMMA':
                index += 1  # Skip comma and continue
            elif tokens[index][0] == 'RBRACKET':
                index += 1  # Skip ']' and finish
                break
            else:
                # No comma, check if next element starts immediately
                if tokens[index][0] in ('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'NULL', 'LBRACKET', 'LBRACE'):
                    # Continue parsing next element without comma (space-separated)
                    continue
                else:
                    raise AILParseError(f"Expected ',' or ']' in array, got {tokens[index]}")
        
        return array, index
    
    def parse_metadata(self, tokens: List[tuple], index: int) -> tuple:
        """Parse metadata object {key: value, ...}."""
        if tokens[index][0] != 'LBRACE':
            raise AILParseError("Expected '{' for metadata")
        
        index += 1  # Skip '{'
        metadata = {}
        
        # Handle empty metadata
        if index < len(tokens) and tokens[index][0] == 'RBRACE':
            return metadata, index + 1
        
        while index < len(tokens):
            # Parse key (must be string)
            if tokens[index][0] != 'STRING':
                raise AILParseError("Expected string key in metadata")
            
            key = tokens[index][1][1:-1]  # Remove quotes
            index += 1
            
            # Parse colon
            if index >= len(tokens) or tokens[index][0] != 'COLON':
                raise AILParseError("Expected ':' after metadata key")
            
            index += 1
            
            # Parse value
            value, index = self.parse_value(tokens, index)
            metadata[key] = value
            
            # Check for comma or end
            if index >= len(tokens):
                raise AILParseError("Unexpected end in metadata")
            
            if tokens[index][0] == 'COMMA':
                index += 1  # Skip comma and continue
            elif tokens[index][0] == 'RBRACE':
                index += 1  # Skip '}' and finish
                break
            else:
                raise AILParseError("Expected ',' or '}' in metadata")
        
        return metadata, index
    
    def parse_cognition(self, tokens: List[tuple], index: int, depth: int = 0) -> tuple:
        """
        Parse a cognition (operation with arguments).
        
        Args:
            tokens: List of tokens
            index: Current position
            depth: Current nesting depth for security
            
        Returns:
            (CognitionNode, new_index) tuple
        """
        # Security check: depth limit with detailed context
        if depth > self.max_depth:
            if index < len(tokens):
                token_info = tokens[index]
                line_num = token_info[3] if len(token_info) > 3 else 1
                col_num = token_info[4] if len(token_info) > 4 else 1
                raise AILSecurityError(
                    f"Nesting depth exceeded: {depth} > {self.max_depth} at line {line_num}, col {col_num}"
                )
            else:
                raise AILSecurityError(f"Nesting depth exceeded: {depth} > {self.max_depth}")
        
        # Expect opening parenthesis
        if index >= len(tokens) or tokens[index][0] != 'LPAREN':
            if index < len(tokens):
                token_info = tokens[index]
                line_num = token_info[3] if len(token_info) > 3 else 1
                col_num = token_info[4] if len(token_info) > 4 else 1
                raise AILParseError(f"Expected '(' to start cognition at line {line_num}, col {col_num}")
            else:
                raise AILParseError("Expected '(' to start cognition but reached end of input")
        
        index += 1  # Skip '('
        
        # Parse operation
        if index >= len(tokens) or tokens[index][0] != 'OPERATION':
            if index < len(tokens):
                token_info = tokens[index]
                line_num = token_info[3] if len(token_info) > 3 else 1
                col_num = token_info[4] if len(token_info) > 4 else 1
                actual_token = token_info[0]
                raise AILParseError(f"Expected operation after '(', got {actual_token} at line {line_num}, col {col_num}")
            else:
                raise AILParseError("Expected operation after '(' but reached end of input")
        
        operation_str = tokens[index][1]
        try:
            operation = AILOperation(operation_str)
        except ValueError:
            token_info = tokens[index]
            line_num = token_info[3] if len(token_info) > 3 else 1
            col_num = token_info[4] if len(token_info) > 4 else 1
            raise AILParseError(f"Unknown operation: {operation_str} at line {line_num}, col {col_num}")
        
        index += 1
        
        # Parse arguments
        arguments = []
        while index < len(tokens) and tokens[index][0] != 'RPAREN':
            # Check if next token starts a nested cognition
            if tokens[index][0] == 'LPAREN':
                arg, index = self.parse_cognition(tokens, index, depth + 1)
            else:
                arg, index = self.parse_value(tokens, index)
            
            arguments.append(arg)
        
        # Expect closing parenthesis
        if index >= len(tokens) or tokens[index][0] != 'RPAREN':
            if index < len(tokens):
                token_info = tokens[index]
                line_num = token_info[3] if len(token_info) > 3 else 1
                col_num = token_info[4] if len(token_info) > 4 else 1
                actual_token = token_info[0]
                raise AILParseError(f"Expected ')' to close cognition, got {actual_token} at line {line_num}, col {col_num}")
            else:
                raise AILParseError("Expected ')' to close cognition but reached end of input")
        
        index += 1  # Skip ')'
        
        return CognitionNode(operation=operation, arguments=arguments), index
    
    def parse(self, ail_code: str) -> CognitionNode:
        """
        Parse AIL code into a cognition tree.
        
        Args:
            ail_code: The AIL S-expression string
            
        Returns:
            Parsed CognitionNode
            
        Raises:
            AILParseError: If parsing fails
            AILSecurityError: If security constraints are violated
        """
        if not ail_code or not ail_code.strip():
            raise AILParseError("Empty AIL code")
        
        # Tokenize
        try:
            tokens = self.tokenize(ail_code.strip())
        except Exception as e:
            self.logger.error(f"Tokenization failed: {e}")
            raise
        
        if not tokens:
            raise AILParseError("No tokens found")
        
        # Parse main cognition
        try:
            cognition, final_index = self.parse_cognition(tokens, 0)
        except Exception as e:
            self.logger.error(f"Parsing failed: {e}")
            raise
        
        # Ensure all tokens were consumed
        if final_index < len(tokens):
            raise AILParseError(f"Unexpected tokens after main cognition: {tokens[final_index:]}")
        
        return cognition
    
    def validate(self, cognition: CognitionNode) -> bool:
        """
        Validate a parsed cognition for security and correctness.
        
        Args:
            cognition: The parsed cognition to validate
            
        Returns:
            True if valid
            
        Raises:
            AILSecurityError: If validation fails
        """
        # Validate operation-specific requirements
        if cognition.operation == AILOperation.QUERY:
            # QUERY must have exactly one metadata argument with 'intent'
            if len(cognition.arguments) != 1:
                raise AILSecurityError("QUERY operation requires exactly one metadata argument")
            
            if not isinstance(cognition.arguments[0], dict):
                raise AILSecurityError("QUERY argument must be metadata object")
            
            metadata = cognition.arguments[0]
            if 'intent' not in metadata:
                raise AILSecurityError("QUERY metadata must contain 'intent' field")
            
            if not isinstance(metadata['intent'], str):
                raise AILSecurityError("QUERY intent must be a string")
        
        elif cognition.operation == AILOperation.EXECUTE:
            # EXECUTE must have tool entity and parameters
            if len(cognition.arguments) < 1:
                raise AILSecurityError("EXECUTE operation requires at least tool entity")
            
            if not isinstance(cognition.arguments[0], Entity):
                raise AILSecurityError("EXECUTE first argument must be tool entity")
        
        elif cognition.operation == AILOperation.PLAN:
            # PLAN must have metadata with goal and sub-cognitions
            if len(cognition.arguments) < 1:
                raise AILSecurityError("PLAN operation requires at least metadata argument")
            
            if not isinstance(cognition.arguments[0], dict):
                raise AILSecurityError("PLAN first argument must be metadata object")
            
            metadata = cognition.arguments[0]
            if 'goal' not in metadata:
                raise AILSecurityError("PLAN metadata must contain 'goal' field")
        
        elif cognition.operation == AILOperation.COMMUNICATE:
            # COMMUNICATE must have recipient entity and cognition
            if len(cognition.arguments) < 2:
                raise AILSecurityError("COMMUNICATE operation requires recipient and cognition")
            
            if not isinstance(cognition.arguments[0], Entity):
                raise AILSecurityError("COMMUNICATE first argument must be recipient entity")
            
            if not isinstance(cognition.arguments[1], CognitionNode):
                raise AILSecurityError("COMMUNICATE second argument must be cognition")
        
        # AIL-3.1 Advanced Operation Validation
        elif cognition.operation == AILOperation.LET:
            # LET must have variable binding pairs and body cognition
            # Format: (LET [var1 value1 var2 value2 ...] body_cognition)
            if len(cognition.arguments) < 2:
                raise AILSecurityError("LET operation requires bindings array and body cognition")
            
            if not isinstance(cognition.arguments[0], list):
                raise AILSecurityError("LET first argument must be bindings array")
            
            bindings = cognition.arguments[0]
            if len(bindings) % 2 != 0:
                raise AILSecurityError("LET bindings must be even number (variable-value pairs)")
            
            if not isinstance(cognition.arguments[1], CognitionNode):
                raise AILSecurityError("LET second argument must be body cognition")
        
        elif cognition.operation == AILOperation.TRY:
            # TRY must have body cognition and optional ON-FAIL clause
            # Format: (TRY body_cognition [ON-FAIL error_var recovery_cognition])
            if len(cognition.arguments) < 1:
                raise AILSecurityError("TRY operation requires at least body cognition")
            
            if not isinstance(cognition.arguments[0], CognitionNode):
                raise AILSecurityError("TRY first argument must be body cognition")
            
            # Check for ON-FAIL as second argument
            if len(cognition.arguments) > 1:
                if isinstance(cognition.arguments[1], CognitionNode):
                    if cognition.arguments[1].operation == AILOperation.ON_FAIL:
                        # Valid ON-FAIL within TRY block
                        pass
                    else:
                        raise AILSecurityError("TRY second argument must be ON-FAIL operation if present")
        
        elif cognition.operation == AILOperation.ON_FAIL:
            # ON-FAIL is valid here if we're in validation context - actual usage validation happens in TRY
            # Format: (ON-FAIL error_var recovery_cognition)
            if len(cognition.arguments) < 2:
                raise AILSecurityError("ON-FAIL requires error variable and recovery cognition")
            
            if not isinstance(cognition.arguments[0], str):
                raise AILSecurityError("ON-FAIL first argument must be error variable name")
            
            if not isinstance(cognition.arguments[1], CognitionNode):
                raise AILSecurityError("ON-FAIL second argument must be recovery cognition")
        
        elif cognition.operation == AILOperation.AWAIT:
            # AWAIT must have async operation and optional timeout
            # Format: (AWAIT operation_cognition {"timeout": 5000})
            if len(cognition.arguments) < 1:
                raise AILSecurityError("AWAIT operation requires at least operation cognition")
            
            if not isinstance(cognition.arguments[0], CognitionNode):
                raise AILSecurityError("AWAIT first argument must be operation cognition")
        
        elif cognition.operation == AILOperation.SANDBOXED_EXECUTE:
            # SANDBOXED-EXECUTE must have sandbox config and operation
            # Format: (SANDBOXED-EXECUTE {"memory_limit": 100, "timeout": 5000} operation_cognition)
            if len(cognition.arguments) < 2:
                raise AILSecurityError("SANDBOXED-EXECUTE requires sandbox config and operation")
            
            if not isinstance(cognition.arguments[0], dict):
                raise AILSecurityError("SANDBOXED-EXECUTE first argument must be sandbox config")
            
            if not isinstance(cognition.arguments[1], CognitionNode):
                raise AILSecurityError("SANDBOXED-EXECUTE second argument must be operation cognition")
        
        elif cognition.operation == AILOperation.CLARIFY:
            # CLARIFY must have ambiguous query and clarification options
            # Format: (CLARIFY "ambiguous query" ["option1" "option2" "option3"])
            if len(cognition.arguments) < 2:
                raise AILSecurityError("CLARIFY operation requires query and options")
            
            if not isinstance(cognition.arguments[0], str):
                raise AILSecurityError("CLARIFY first argument must be query string")
            
            if not isinstance(cognition.arguments[1], list):
                raise AILSecurityError("CLARIFY second argument must be options array")
        
        elif cognition.operation == AILOperation.EVENT:
            # EVENT must have event name and handler cognition
            # Format: (EVENT "event_name" trigger_condition handler_cognition)
            if len(cognition.arguments) < 3:
                raise AILSecurityError("EVENT operation requires name, condition, and handler")
            
            if not isinstance(cognition.arguments[0], str):
                raise AILSecurityError("EVENT first argument must be event name")
            
            if not isinstance(cognition.arguments[2], CognitionNode):
                raise AILSecurityError("EVENT third argument must be handler cognition")
        
        # Recursively validate nested cognitions
        for arg in cognition.arguments:
            if isinstance(arg, CognitionNode):
                self.validate(arg)
        
        return True


@dataclass
class Variable:
    """Represents a variable binding in LET operations."""
    name: str
    value: Any
    scope_level: int = 0
    
    def __str__(self):
        return f"${self.name}"


@dataclass
class VariableContext:
    """Manages variable scoping for LET operations."""
    variables: Dict[str, Variable]
    scope_level: int = 0
    parent_context: Optional['VariableContext'] = None
    
    def get_variable(self, name: str) -> Optional[Variable]:
        """Get a variable, checking parent scopes if needed."""
        if name in self.variables:
            return self.variables[name]
        elif self.parent_context:
            return self.parent_context.get_variable(name)
        return None
    
    def set_variable(self, name: str, value: Any) -> Variable:
        """Set a variable in the current scope."""
        variable = Variable(name, value, self.scope_level)
        self.variables[name] = variable
        return variable


@dataclass
class TryBlock:
    """Represents a TRY/ON-FAIL error handling block."""
    try_cognition: 'CognitionNode'
    on_fail_cognition: Optional['CognitionNode'] = None
    error_variable: Optional[str] = None  # Variable to bind caught errors


@dataclass
class AwaitOperation:
    """Represents an AWAIT asynchronous operation."""
    operation_id: str
    timeout_ms: Optional[int] = None
    on_timeout: Optional['CognitionNode'] = None


@dataclass
class EventDefinition:
    """Represents an EVENT definition."""
    event_name: str
    trigger_condition: str
    handler_cognition: 'CognitionNode'
    metadata: Dict[str, Any] = None


@dataclass
class SandboxConfig:
    """Configuration for SANDBOXED-EXECUTE operations."""
    memory_limit_mb: Optional[int] = None
    cpu_limit_ms: Optional[int] = None
    network_access: bool = False
    file_access: bool = False
    allowed_operations: List[str] = None


def create_ail_parser() -> AILParser:
    """Create a configured AIL parser instance."""
    return AILParser(max_depth=10, max_tokens=1000)


def create_variable_context(parent: Optional[VariableContext] = None) -> VariableContext:
    """Create a new variable context for LET operation scoping."""
    scope_level = parent.scope_level + 1 if parent else 0
    return VariableContext(
        variables={},
        scope_level=scope_level,
        parent_context=parent
    )


def create_try_block(try_cognition: CognitionNode, 
                    on_fail_cognition: Optional[CognitionNode] = None,
                    error_variable: Optional[str] = None) -> TryBlock:
    """Create a TRY/ON-FAIL error handling block."""
    return TryBlock(
        try_cognition=try_cognition,
        on_fail_cognition=on_fail_cognition,
        error_variable=error_variable
    )


def create_await_operation(operation_id: str,
                          timeout_ms: Optional[int] = None,
                          on_timeout: Optional[CognitionNode] = None) -> AwaitOperation:
    """Create an AWAIT asynchronous operation."""
    return AwaitOperation(
        operation_id=operation_id,
        timeout_ms=timeout_ms,
        on_timeout=on_timeout
    )


def create_event_definition(event_name: str,
                           trigger_condition: str,
                           handler_cognition: CognitionNode,
                           metadata: Optional[Dict[str, Any]] = None) -> EventDefinition:
    """Create an EVENT definition."""
    return EventDefinition(
        event_name=event_name,
        trigger_condition=trigger_condition,
        handler_cognition=handler_cognition,
        metadata=metadata or {}
    )


def create_sandbox_config(memory_limit_mb: Optional[int] = None,
                         cpu_limit_ms: Optional[int] = None,
                         network_access: bool = False,
                         file_access: bool = False,
                         allowed_operations: Optional[List[str]] = None) -> SandboxConfig:
    """Create a sandbox configuration for SANDBOXED-EXECUTE."""
    return SandboxConfig(
        memory_limit_mb=memory_limit_mb,
        cpu_limit_ms=cpu_limit_ms,
        network_access=network_access,
        file_access=file_access,
        allowed_operations=allowed_operations or []
    )


# Parser module complete - test harness moved to tests/test_ail_parser.py
