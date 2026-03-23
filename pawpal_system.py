"""
PawPal+ — logic layer
Classes: Owner, Pet, Task, Scheduler
"""

from __future__ import annotations
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single care task (walk, feeding, meds, grooming, enrichment, etc.)."""

    name: str
    category: str       # e.g. "walk", "feeding", "meds", "grooming"
    duration_min: int   # how long the task takes
    priority: int       # 1 = highest, higher numbers = lower priority
    notes: str = ""

    def is_valid(self) -> bool:
        """Return True if name is non-empty, duration > 0, and priority >= 1."""
        return bool(self.name) and self.duration_min > 0 and self.priority >= 1


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Basic pet info — data only, no task management."""

    name: str
    species: str    # e.g. "dog", "cat"
    breed: str = ""
    age: int = 0


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """A pet owner with time and preference constraints used by the Scheduler."""

    name: str
    time_available_min: int     # total minutes the owner has today
    preferences: list[str] = field(default_factory=list)
    # e.g. ["morning walks", "no grooming on weekends"]


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Core logic layer. Generates a prioritised daily plan that fits within
    the owner's available time and explains the reasoning.
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        """Initialise with an owner and pet; start with an empty task pool."""
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []
        self.excluded: list[Task] = []  # populated by generate_plan()

    def add_task(self, task: Task) -> None:
        """Add a valid task to the pool; raise ValueError if task is invalid."""
        if not task.is_valid():
            raise ValueError(f"Task '{task.name}' is invalid and cannot be added.")
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the pool; raise ValueError if not found."""
        if task not in self.tasks:
            raise ValueError(f"Task '{task.name}' not found in pool.")
        self.tasks.remove(task)

    def edit_task(self, old_task: Task, new_task: Task) -> None:
        """Replace old_task with new_task; raise ValueError if old_task not found."""
        idx = self.tasks.index(old_task) if old_task in self.tasks else -1
        if idx == -1:
            raise ValueError(f"Task '{old_task.name}' not found in pool.")
        if not new_task.is_valid():
            raise ValueError(f"Replacement task '{new_task.name}' is invalid.")
        self.tasks[idx] = new_task

    def generate_plan(self) -> list[Task]:
        """
        Sort tasks by priority, then greedily include tasks until the time
        budget is exhausted. Excluded tasks are stored in self.excluded.
        """
        sorted_tasks = sorted(self.tasks, key=lambda t: t.priority)
        plan: list[Task] = []
        self.excluded = []
        time_left = self.owner.time_available_min

        for task in sorted_tasks:
            if task.duration_min <= time_left:
                plan.append(task)
                time_left -= task.duration_min
            else:
                self.excluded.append(task)

        return plan

    def explain_plan(self, plan: list[Task]) -> str:
        """Return a plain-English summary of included and excluded tasks."""
        lines = [
            f"Daily plan for {self.pet.name} "
            f"(owner: {self.owner.name}, "
            f"budget: {self.owner.time_available_min} min)\n"
        ]

        if plan:
            lines.append("Included tasks:")
            time_used = 0
            for task in plan:
                time_used += task.duration_min
                lines.append(
                    f"  [priority {task.priority}] {task.name} "
                    f"({task.duration_min} min) — {task.category}"
                    + (f": {task.notes}" if task.notes else "")
                )
            lines.append(f"  Total time: {time_used} min")
        else:
            lines.append("No tasks fit within the available time.")

        if self.excluded:
            lines.append("\nExcluded tasks (exceeded time budget):")
            for task in self.excluded:
                lines.append(
                    f"  [priority {task.priority}] {task.name} "
                    f"({task.duration_min} min) — not enough time remaining"
                )

        if self.owner.preferences:
            lines.append("\nOwner preferences noted (not yet applied automatically):")
            for pref in self.owner.preferences:
                lines.append(f"  - {pref}")

        return "\n".join(lines)