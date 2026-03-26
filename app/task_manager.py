"""
task_manager.py — Task CRUD logic for Quietum.
Each task is a dict: { "id": str, "text": str, "done": bool, "reminder": str|None }
"""

import uuid
from datetime import datetime


def create_task(text: str, reminder: str = None) -> dict:
    """
    Create a new task dict.

    Args:
        text: The task description.
        reminder: Optional ISO datetime string for a reminder (e.g. "2026-03-26T09:00").

    Returns:
        A task dictionary with a unique ID.
    """
    return {
        "id": str(uuid.uuid4())[:8],
        "text": text.strip(),
        "done": False,
        "reminder": reminder,
        "created_at": datetime.now().isoformat(),
    }


def toggle_task(task: dict) -> dict:
    """Toggle the done state of a task."""
    task["done"] = not task["done"]
    return task


def edit_task(task: dict, new_text: str) -> dict:
    """Update the text of a task."""
    task["text"] = new_text.strip()
    return task


def set_reminder(task: dict, reminder: str) -> dict:
    """Set or update a reminder for a task."""
    task["reminder"] = reminder
    return task


def clear_reminder(task: dict) -> dict:
    """Remove the reminder from a task."""
    task["reminder"] = None
    return task


def reorder_tasks(tasks: list, from_idx: int, to_idx: int) -> list:
    """
    Move a task from one position to another (drag-and-drop reorder).

    Args:
        tasks: The list of tasks in a section.
        from_idx: Current index of the task.
        to_idx: Target index for the task.

    Returns:
        The reordered list.
    """
    if 0 <= from_idx < len(tasks) and 0 <= to_idx < len(tasks):
        task = tasks.pop(from_idx)
        tasks.insert(to_idx, task)
    return tasks


def get_due_reminders(tasks: list) -> list:
    """
    Check all tasks for due reminders.

    Returns:
        List of tasks whose reminder time has passed and are not done.
    """
    now = datetime.now()
    due = []
    for task in tasks:
        if task.get("reminder") and not task["done"]:
            try:
                reminder_time = datetime.fromisoformat(task["reminder"])
                if reminder_time <= now:
                    due.append(task)
            except (ValueError, TypeError):
                continue
    return due
