import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel

# Todo status enum
class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

# Todo model with coding project specific fields
class Todo(BaseModel):
    id: str
    title: str
    description: str
    status: TodoStatus = TodoStatus.PENDING
    created_at: datetime = datetime.now()
    updated_at: Optional[datetime] = None
    project: Optional[str] = None
    priority: int = 1  # 1 (lowest) to 5 (highest)
    tags: List[str] = []

# Store todos in memory
todos: Dict[str, Todo] = {}

# Create an MCP server using FastMCP
mcp = FastMCP("coding-todo-server")

# Resource to list all todos
@mcp.resource("todo://list")
def get_todo_list() -> str:
    """List of all coding project todos"""
    if not todos:
        return "No todos found."
    
    result = "# Coding Project Todos\n\n"
    for todo_id, todo in todos.items():
        status_marker = "[ ]" if todo.status != TodoStatus.COMPLETED else "[x]"
        result += f"{status_marker} **{todo.title}** (ID: {todo_id}, Priority: {todo.priority})\n"
        if todo.tags:
            result += f"   Tags: {', '.join(todo.tags)}\n"
    return result

# Resource to view a specific todo
@mcp.resource("todo://item/{todo_id}")
def get_todo_item(todo_id: str) -> str:
    """Get details of a specific todo item"""
    if todo_id not in todos:
        raise ValueError(f"Todo not found: {todo_id}")
    
    todo = todos[todo_id]
    result = f"# Todo: {todo.title}\n\n"
    result += f"**Status:** {todo.status.value}\n"
    result += f"**Priority:** {todo.priority}/5\n"
    result += f"**Created:** {todo.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    if todo.updated_at:
        result += f"**Updated:** {todo.updated_at.strftime('%Y-%m-%d %H:%M')}\n"
    if todo.project:
        result += f"**Project:** {todo.project}\n"
    if todo.tags:
        result += f"**Tags:** {', '.join(todo.tags)}\n"
    result += f"\n**Description:**\n{todo.description}\n"
    return result

# Prompt to summarize todos
@mcp.prompt()
def summarize_todos(status: str = "pending", project: str = None) -> str:
    """Creates a summary of todos with optional filtering
    
    Args:
        status: Filter by status (pending/in_progress/completed/all)
        project: Filter by project name
    """
    filtered_todos = list(todos.values())
    if status != "all":
        filtered_todos = [t for t in filtered_todos if t.status.value == status]
    if project:
        filtered_todos = [t for t in filtered_todos if t.project == project]
    
    status_text = f"{status} " if status != "all" else ""
    project_text = f"for project {project} " if project else ""
    
    return f"""Here are the current {status_text}todos {project_text}to summarize:

{chr(10).join(f"- {t.title} (Priority: {t.priority}): {t.description}" for t in filtered_todos)}

Please provide a concise summary of these todos and suggest an approach to tackle them efficiently."""

# Prompt to suggest which todo to tackle next
@mcp.prompt()
def suggest_next_todo() -> str:
    """Suggests which todo to tackle next based on priority and status"""
    pending_todos = [t for t in todos.values() if t.status != TodoStatus.COMPLETED]
    
    if not pending_todos:
        return "There are no pending todos. Would you like suggestions for new coding tasks to add?"
    
    # Sort by priority (highest first)
    sorted_todos = sorted(pending_todos, key=lambda t: (-t.priority, t.created_at))
    
    return f"""Here are the current pending todos in order of priority:

{chr(10).join(f"- {t.title} (Priority: {t.priority}, Status: {t.status.value}): {t.description}" for t in sorted_todos)}

Based on these todos, which one should I tackle next and why? Please provide a brief recommendation."""

# Tool to add a new todo
@mcp.tool()
def add_todo(title: str, description: str, project: str = None, priority: int = 1, tags: List[str] = None) -> str:
    """Add a new todo item
    
    Args:
        title: Title of the todo item
        description: Detailed description of the todo item
        project: Project name (optional)
        priority: Priority from 1 (lowest) to 5 (highest)
        tags: List of tags related to the todo
    """
    # Generate a new todo ID
    todo_id = f"todo{len(todos) + 1}"
    
    new_todo = Todo(
        id=todo_id,
        title=title,
        description=description,
        project=project,
        priority=priority,
        tags=tags or [],
    )
    
    todos[todo_id] = new_todo
    
    return f"Added todo '{title}' with ID: {todo_id}"

# Tool to update the status of a todo
@mcp.tool()
def update_todo_status(id: str, status: str) -> str:
    """Update the status of a todo item
    
    Args:
        id: The ID of the todo item
        status: New status (pending/in_progress/completed)
    """
    if id not in todos:
        raise ValueError(f"Todo not found: {id}")
    
    try:
        todos[id].status = TodoStatus(status)
        todos[id].updated_at = datetime.now()
    except ValueError:
        raise ValueError(f"Invalid status: {status}. Must be one of: pending, in_progress, completed")
    
    return f"Updated todo '{todos[id].title}' status to {status}"

# Tool to delete a todo
@mcp.tool()
def delete_todo(id: str) -> str:
    """Delete a todo item
    
    Args:
        id: The ID of the todo item to delete
    """
    if id not in todos:
        raise ValueError(f"Todo not found: {id}")
    
    title = todos[id].title
    del todos[id]
    
    return f"Deleted todo '{title}' (ID: {id})"

# Tool to update a todo's details
@mcp.tool()
def update_todo(id: str, title: str = None, description: str = None, project: str = None, 
               priority: int = None, tags: List[str] = None) -> str:
    """Update a todo item's details
    
    Args:
        id: The ID of the todo item
        title: New title (optional)
        description: New description (optional)
        project: New project name (optional)
        priority: New priority from 1 (lowest) to 5 (highest) (optional)
        tags: New list of tags (optional)
    """
    if id not in todos:
        raise ValueError(f"Todo not found: {id}")
    
    todo = todos[id]
    
    if title is not None:
        todo.title = title
    
    if description is not None:
        todo.description = description
    
    if project is not None:
        todo.project = project
    
    if priority is not None:
        if not 1 <= priority <= 5:
            raise ValueError("Priority must be between 1 and 5")
        todo.priority = priority
    
    if tags is not None:
        todo.tags = tags
    
    # Update the timestamp
    todo.updated_at = datetime.now()
    
    return f"Updated todo '{todo.title}' (ID: {id})"

# Initialize with example todos
def initialize_example_todos():
    example_todos = [
        Todo(
            id="todo1",
            title="Implement user authentication",
            description="Add JWT-based authentication to the API endpoints",
            priority=4,
            project="Backend API",
            tags=["backend", "security"],
        ),
        Todo(
            id="todo2",
            title="Fix CSS responsiveness",
            description="The dashboard layout breaks on mobile devices",
            priority=3,
            project="Frontend UI",
            tags=["frontend", "css", "bugfix"],
        ),
        Todo(
            id="todo3",
            title="Write unit tests",
            description="Create tests for the new data processing module",
            priority=2,
            project="Backend API",
            tags=["testing", "quality"],
        ),
    ]
    
    for todo in example_todos:
        todos[todo.id] = todo

# Initialize and run server
if __name__ == "__main__":
    initialize_example_todos()
    mcp.run()