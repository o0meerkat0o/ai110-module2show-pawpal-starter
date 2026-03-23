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
    category: str                   # e.g. "walk", "feeding", "meds", "grooming"
    duration_min: int               # how long the task takes
    priority: int                   # 1 = highest, higher numbers = lower priority
    notes: str = ""

    def is_valid(self) -> bool:
        """Return True if the task has valid duration and priority values."""
        pass


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Basic pet info — data only, no task management."""

    name: str
    species: str                    # e.g. "dog", "cat"
    breed: str = ""
    age: int = 0


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """A pet owner with time and preference constraints used by the Scheduler."""

    name: str
    time_available_min: int         # total minutes the owner has today
    preferences: list[str] = field(default_factory=list)
    # e.g. ["morning walks", "no grooming on weekends"]


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Core logic layer — takes an owner, their pet, and a list of tasks,
    then generates a prioritised daily plan that fits within the owner's
    available time, and explains the reasoning behind it.
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the pool."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a task from the pool."""
        pass

    def generate_plan(self) -> list[Task]:
        """
        Return an ordered list of tasks that fit within
        owner.time_available_min, sorted by priority.
        Higher-priority tasks are included first; tasks that would
        exceed the time budget are left out.
        """
        pass

    def explain_plan(self, plan: list[Task]) -> str:
        """
        Return a human-readable string explaining why each task was
        included or excluded from the plan.
        """
        pass