"""
tests/test_pawpal.py — run with: python -m pytest
"""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner():
    return Owner(name="Alex", time_available_min=60)


@pytest.fixture
def pet():
    return Pet(name="Biscuit", species="dog")


@pytest.fixture
def scheduler(owner, pet):
    return Scheduler(owner, pet)


# ---------------------------------------------------------------------------
# Task validation
# ---------------------------------------------------------------------------

def test_task_is_valid():
    """A task with a name, positive duration, and priority >= 1 is valid."""
    t = Task("Walk", "walk", duration_min=30, priority=1)
    assert t.is_valid() is True


def test_task_invalid_duration():
    """A task with duration 0 is not valid."""
    t = Task("Walk", "walk", duration_min=0, priority=1)
    assert t.is_valid() is False


def test_task_invalid_priority():
    """A task with priority 0 is not valid."""
    t = Task("Walk", "walk", duration_min=30, priority=0)
    assert t.is_valid() is False


def test_add_invalid_task_raises(scheduler):
    """Adding an invalid task raises ValueError."""
    bad = Task("", "walk", duration_min=-5, priority=0)
    with pytest.raises(ValueError):
        scheduler.add_task(bad)


# ---------------------------------------------------------------------------
# Task pool management
# ---------------------------------------------------------------------------

def test_add_task_increases_count(scheduler):
    """Adding a task increases the pool size by one."""
    before = len(scheduler.tasks)
    scheduler.add_task(Task("Feed", "feeding", duration_min=10, priority=1))
    assert len(scheduler.tasks) == before + 1


def test_remove_task_decreases_count(scheduler):
    """Removing a task decreases the pool size by one."""
    task = Task("Feed", "feeding", duration_min=10, priority=1)
    scheduler.add_task(task)
    before = len(scheduler.tasks)
    scheduler.remove_task(task)
    assert len(scheduler.tasks) == before - 1


def test_remove_missing_task_raises(scheduler):
    """Removing a task not in the pool raises ValueError."""
    ghost = Task("Ghost", "walk", duration_min=10, priority=1)
    with pytest.raises(ValueError):
        scheduler.remove_task(ghost)


def test_edit_task_replaces_in_place(scheduler):
    """edit_task swaps the old task for the new one."""
    old = Task("Short walk", "walk", duration_min=15, priority=2)
    new = Task("Long walk",  "walk", duration_min=45, priority=2)
    scheduler.add_task(old)
    scheduler.edit_task(old, new)
    assert new in scheduler.tasks
    assert old not in scheduler.tasks


# ---------------------------------------------------------------------------
# Scheduling logic
# ---------------------------------------------------------------------------

def test_generate_plan_respects_budget(scheduler):
    """Total duration of the plan never exceeds the owner's time budget."""
    scheduler.add_task(Task("Walk",    "walk",     duration_min=30, priority=1))
    scheduler.add_task(Task("Feed",    "feeding",  duration_min=10, priority=1))
    scheduler.add_task(Task("Groom",   "grooming", duration_min=30, priority=3))
    plan = scheduler.generate_plan()
    assert sum(t.duration_min for t in plan) <= scheduler.owner.time_available_min


def test_generate_plan_priority_order(scheduler):
    """Higher-priority tasks (lower number) appear before lower-priority ones."""
    scheduler.add_task(Task("Low",  "enrichment", duration_min=10, priority=3))
    scheduler.add_task(Task("High", "walk",        duration_min=10, priority=1))
    scheduler.add_task(Task("Mid",  "feeding",     duration_min=10, priority=2))
    plan = scheduler.generate_plan()
    priorities = [t.priority for t in plan]
    assert priorities == sorted(priorities)


def test_excluded_tasks_logged(scheduler):
    """Tasks that do not fit are stored in scheduler.excluded."""
    scheduler.add_task(Task("Quick feed", "feeding", duration_min=10, priority=1))
    scheduler.add_task(Task("Long hike",  "walk",    duration_min=120, priority=2))
    scheduler.generate_plan()
    assert any(t.name == "Long hike" for t in scheduler.excluded)


def test_explain_plan_mentions_pet_and_owner(scheduler):
    """explain_plan output references the pet name and owner name."""
    task = Task("Walk", "walk", duration_min=20, priority=1)
    scheduler.add_task(task)
    plan = scheduler.generate_plan()
    explanation = scheduler.explain_plan(plan)
    assert scheduler.pet.name in explanation
    assert scheduler.owner.name in explanation