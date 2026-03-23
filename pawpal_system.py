"""
PawPal+ — logic layer
Classes: Owner, Pet, Task, Scheduler
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

VALID_FREQUENCIES = ("once", "daily", "weekly")


@dataclass
class Task:
    """A single care task (walk, feeding, meds, grooming, enrichment, etc.)."""

    name: str
    category: str           # e.g. "walk", "feeding", "meds", "grooming"
    duration_min: int       # how long the task takes
    priority: int           # 1 = highest, higher numbers = lower priority
    start_time: str = ""    # optional scheduled start in "HH:MM" format
    frequency: str = "once" # "once", "daily", or "weekly"
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    notes: str = ""

    def is_valid(self) -> bool:
        """Return True if name, duration, priority, and frequency are all valid."""
        return (
            bool(self.name)
            and self.duration_min > 0
            and self.priority >= 1
            and self.frequency in VALID_FREQUENCIES
        )

    def mark_complete(self) -> Task | None:
        """
        Mark this task done. For recurring tasks, return a new Task due on
        the next occurrence; for one-off tasks return None.
        """
        self.completed = True
        if self.frequency == "daily":
            return Task(
                name=self.name,
                category=self.category,
                duration_min=self.duration_min,
                priority=self.priority,
                start_time=self.start_time,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(days=1),
                notes=self.notes,
            )
        if self.frequency == "weekly":
            return Task(
                name=self.name,
                category=self.category,
                duration_min=self.duration_min,
                priority=self.priority,
                start_time=self.start_time,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(weeks=1),
                notes=self.notes,
            )
        return None


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
    Core logic layer. Generates a prioritised daily plan, handles recurring
    tasks, sorts/filters the task pool, and detects scheduling conflicts.
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        """Initialise with an owner and pet; start with an empty task pool."""
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []
        self.excluded: list[Task] = []  # populated by generate_plan()

    # ------------------------------------------------------------------
    # Pool management
    # ------------------------------------------------------------------

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

    def mark_complete(self, task: Task) -> None:
        """
        Mark a task complete. If it is recurring, automatically add the next
        occurrence to the pool before removing the completed one.
        """
        if task not in self.tasks:
            raise ValueError(f"Task '{task.name}' not found in pool.")
        next_task = task.mark_complete()
        if next_task is not None:
            self.tasks.append(next_task)
        self.tasks.remove(task)

    # ------------------------------------------------------------------
    # Sorting and filtering
    # ------------------------------------------------------------------

    def sort_by_time(self) -> list[Task]:
        """
        Return tasks sorted by start_time (HH:MM). Tasks with no start_time
        are placed at the end.
        """
        return sorted(self.tasks, key=lambda t: t.start_time if t.start_time else "99:99")

    def filter_by_category(self, category: str) -> list[Task]:
        """Return all tasks whose category matches the given string (case-insensitive)."""
        return [t for t in self.tasks if t.category.lower() == category.lower()]

    def filter_incomplete(self) -> list[Task]:
        """Return only tasks that have not been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def filter_by_date(self, target: date) -> list[Task]:
        """Return all incomplete tasks whose due_date matches target."""
        return [t for t in self.tasks if not t.completed and t.due_date == target]

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> list[str]:
        """
        Check for time conflicts among tasks that have a start_time set.
        Two tasks conflict if they share the same start_time string. Returns
        a list of warning strings (empty if no conflicts).

        Note: this is an exact-match check on start_time, not a duration-overlap
        check. See reflection.md 2b for the tradeoff discussion.
        """
        timed = [t for t in self.tasks if t.start_time]
        seen: dict[str, Task] = {}
        warnings: list[str] = []

        for task in timed:
            if task.start_time in seen:
                other = seen[task.start_time]
                warnings.append(
                    f"Conflict at {task.start_time}: "
                    f"'{task.name}' and '{other.name}' are both scheduled at this time."
                )
            else:
                seen[task.start_time] = task

        return warnings

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    def generate_plan(self) -> list[Task]:
        """
        From incomplete tasks, sort by priority, then greedily include tasks
        until the time budget is exhausted. Excluded tasks go in self.excluded.
        """
        candidates = sorted(self.filter_incomplete(), key=lambda t: t.priority)
        plan: list[Task] = []
        self.excluded = []
        time_left = self.owner.time_available_min

        for task in candidates:
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
                time_label = f" @ {task.start_time}" if task.start_time else ""
                lines.append(
                    f"  [priority {task.priority}] {task.name}"
                    f"{time_label} ({task.duration_min} min, {task.frequency})"
                    + (f": {task.notes}" if task.notes else "")
                )
            lines.append(f"  Total time: {time_used} min")
        else:
            lines.append("No tasks fit within the available time.")

        if self.excluded:
            lines.append("\nExcluded (exceeded budget):")
            for task in self.excluded:
                lines.append(
                    f"  [priority {task.priority}] {task.name} "
                    f"({task.duration_min} min)"
                )

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("\nConflict warnings:")
            for w in conflicts:
                lines.append(f"  ! {w}")

        if self.owner.preferences:
            lines.append("\nOwner preferences (not yet auto-applied):")
            for pref in self.owner.preferences:
                lines.append(f"  - {pref}")

        return "\n".join(lines)