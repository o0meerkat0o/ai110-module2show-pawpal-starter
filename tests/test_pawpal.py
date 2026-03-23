"""
tests/test_pawpal.py — run with: python -m pytest
"""

import pytest
from datetime import date, timedelta
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
    assert Task("Walk", "walk", 30, 1).is_valid() is True

def test_task_invalid_duration():
    assert Task("Walk", "walk", 0, 1).is_valid() is False

def test_task_invalid_priority():
    assert Task("Walk", "walk", 30, 0).is_valid() is False

def test_task_invalid_frequency():
    t = Task("Walk", "walk", 30, 1)
    t.frequency = "hourly"
    assert t.is_valid() is False

def test_add_invalid_task_raises(scheduler):
    with pytest.raises(ValueError):
        scheduler.add_task(Task("", "walk", -5, 0))


# ---------------------------------------------------------------------------
# Pool management
# ---------------------------------------------------------------------------

def test_add_task_increases_count(scheduler):
    before = len(scheduler.tasks)
    scheduler.add_task(Task("Feed", "feeding", 10, 1))
    assert len(scheduler.tasks) == before + 1

def test_remove_task_decreases_count(scheduler):
    task = Task("Feed", "feeding", 10, 1)
    scheduler.add_task(task)
    before = len(scheduler.tasks)
    scheduler.remove_task(task)
    assert len(scheduler.tasks) == before - 1

def test_remove_missing_task_raises(scheduler):
    with pytest.raises(ValueError):
        scheduler.remove_task(Task("Ghost", "walk", 10, 1))

def test_edit_task_replaces(scheduler):
    old = Task("Short walk", "walk", 15, 2)
    new = Task("Long walk",  "walk", 45, 2)
    scheduler.add_task(old)
    scheduler.edit_task(old, new)
    assert new in scheduler.tasks
    assert old not in scheduler.tasks


# ---------------------------------------------------------------------------
# Recurring tasks
# ---------------------------------------------------------------------------

def test_mark_complete_once_removes_task(scheduler):
    task = Task("Vet visit", "meds", 30, 1, frequency="once")
    scheduler.add_task(task)
    scheduler.mark_complete(task)
    assert task not in scheduler.tasks

def test_mark_complete_daily_adds_next(scheduler):
    today = date.today()
    task = Task("Breakfast", "feeding", 10, 1, frequency="daily", due_date=today)
    scheduler.add_task(task)
    scheduler.mark_complete(task)
    next_task = next((t for t in scheduler.tasks if t.name == "Breakfast"), None)
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False

def test_mark_complete_weekly_adds_next(scheduler):
    today = date.today()
    task = Task("Brushing", "grooming", 20, 3, frequency="weekly", due_date=today)
    scheduler.add_task(task)
    scheduler.mark_complete(task)
    next_task = next((t for t in scheduler.tasks if t.name == "Brushing"), None)
    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


# ---------------------------------------------------------------------------
# Sorting and filtering
# ---------------------------------------------------------------------------

def test_sort_by_time_order(scheduler):
    scheduler.add_task(Task("Evening walk", "walk",    30, 2, start_time="17:00"))
    scheduler.add_task(Task("Breakfast",    "feeding", 10, 1, start_time="08:00"))
    scheduler.add_task(Task("Meds",         "meds",     5, 1, start_time="08:30"))
    sorted_tasks = scheduler.sort_by_time()
    times = [t.start_time for t in sorted_tasks]
    assert times == sorted(times)

def test_sort_by_time_no_time_last(scheduler):
    scheduler.add_task(Task("Unscheduled", "enrichment", 20, 3))
    scheduler.add_task(Task("Morning walk", "walk",      30, 1, start_time="07:00"))
    sorted_tasks = scheduler.sort_by_time()
    assert sorted_tasks[-1].start_time == ""

def test_filter_by_category(scheduler):
    scheduler.add_task(Task("Walk",      "walk",    30, 1))
    scheduler.add_task(Task("Feed",      "feeding", 10, 1))
    scheduler.add_task(Task("Long walk", "walk",    45, 2))
    walks = scheduler.filter_by_category("walk")
    assert len(walks) == 2
    assert all(t.category == "walk" for t in walks)

def test_filter_incomplete(scheduler):
    t1 = Task("Walk", "walk", 30, 1, frequency="once")
    t2 = Task("Feed", "feeding", 10, 1, frequency="once")
    scheduler.add_task(t1)
    scheduler.add_task(t2)
    scheduler.mark_complete(t1)
    incomplete = scheduler.filter_incomplete()
    assert t1 not in incomplete
    assert t2 in incomplete


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_found(scheduler):
    scheduler.add_task(Task("Walk",     "walk", 30, 1, start_time="08:00"))
    scheduler.add_task(Task("Vet call", "meds", 15, 2, start_time="08:00"))
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "08:00" in warnings[0]

def test_detect_conflicts_none(scheduler):
    scheduler.add_task(Task("Walk", "walk",    30, 1, start_time="07:30"))
    scheduler.add_task(Task("Feed", "feeding", 10, 1, start_time="08:00"))
    assert scheduler.detect_conflicts() == []

def test_no_conflict_without_start_time(scheduler):
    scheduler.add_task(Task("Walk", "walk",    30, 1))
    scheduler.add_task(Task("Feed", "feeding", 10, 1))
    assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------

def test_generate_plan_respects_budget(scheduler):
    scheduler.add_task(Task("Walk",  "walk",     30, 1))
    scheduler.add_task(Task("Feed",  "feeding",  10, 1))
    scheduler.add_task(Task("Groom", "grooming", 30, 3))
    plan = scheduler.generate_plan()
    assert sum(t.duration_min for t in plan) <= scheduler.owner.time_available_min

def test_generate_plan_priority_order(scheduler):
    scheduler.add_task(Task("Low",  "enrichment", 10, 3))
    scheduler.add_task(Task("High", "walk",        10, 1))
    scheduler.add_task(Task("Mid",  "feeding",     10, 2))
    plan = scheduler.generate_plan()
    assert [t.priority for t in plan] == sorted(t.priority for t in plan)

def test_excluded_tasks_logged(scheduler):
    scheduler.add_task(Task("Quick feed", "feeding", 10,  1))
    scheduler.add_task(Task("Long hike",  "walk",    120, 2))
    scheduler.generate_plan()
    assert any(t.name == "Long hike" for t in scheduler.excluded)

def test_generate_plan_skips_completed(scheduler):
    done = Task("Old task", "walk", 10, 1, frequency="once")
    scheduler.add_task(done)
    scheduler.mark_complete(done)
    plan = scheduler.generate_plan()
    assert done not in plan


# ---------------------------------------------------------------------------
# Edge cases: empty pool
# ---------------------------------------------------------------------------

def test_generate_plan_empty_pool_returns_empty(scheduler):
    """generate_plan on an empty pool returns an empty list, no crash."""
    assert scheduler.generate_plan() == []

def test_sort_by_time_empty_pool(scheduler):
    """sort_by_time on an empty pool returns an empty list."""
    assert scheduler.sort_by_time() == []

def test_filter_incomplete_empty_pool(scheduler):
    """filter_incomplete on an empty pool returns an empty list."""
    assert scheduler.filter_incomplete() == []

def test_detect_conflicts_empty_pool(scheduler):
    """detect_conflicts on an empty pool returns no warnings."""
    assert scheduler.detect_conflicts() == []

def test_explain_plan_empty_plan(scheduler):
    """explain_plan with an empty plan mentions no tasks fitting."""
    explanation = scheduler.explain_plan([])
    assert "No tasks fit" in explanation


# ---------------------------------------------------------------------------
# Edge cases: zero time budget
# ---------------------------------------------------------------------------

def test_generate_plan_zero_budget():
    """No tasks are scheduled when the owner has zero minutes available."""
    owner = Owner(name="Alex", time_available_min=0)
    pet = Pet(name="Biscuit", species="dog")
    s = Scheduler(owner, pet)
    s.add_task(Task("Walk", "walk", 30, 1))
    plan = s.generate_plan()
    assert plan == []
    assert len(s.excluded) == 1

def test_generate_plan_exact_budget_fit(scheduler):
    """A task whose duration exactly equals the budget is included."""
    scheduler.add_task(Task("Long walk", "walk", 60, 1))
    plan = scheduler.generate_plan()
    assert len(plan) == 1


# ---------------------------------------------------------------------------
# Edge cases: sorting
# ---------------------------------------------------------------------------

def test_sort_by_time_all_no_start_time(scheduler):
    """Tasks with no start_time all sort to the end; order among them is stable."""
    scheduler.add_task(Task("A", "walk",    30, 1))
    scheduler.add_task(Task("B", "feeding", 10, 2))
    sorted_tasks = scheduler.sort_by_time()
    assert all(t.start_time == "" for t in sorted_tasks)

def test_sort_by_time_mixed(scheduler):
    """Timed tasks come before untimed tasks."""
    scheduler.add_task(Task("Unscheduled", "enrichment", 20, 3))
    scheduler.add_task(Task("Early walk",  "walk",       30, 1, start_time="06:00"))
    sorted_tasks = scheduler.sort_by_time()
    assert sorted_tasks[0].start_time == "06:00"
    assert sorted_tasks[-1].start_time == ""


# ---------------------------------------------------------------------------
# Edge cases: conflicts
# ---------------------------------------------------------------------------

def test_three_way_conflict(scheduler):
    """Three tasks at the same time produce two conflict warnings."""
    scheduler.add_task(Task("A", "walk",    10, 1, start_time="09:00"))
    scheduler.add_task(Task("B", "feeding", 10, 2, start_time="09:00"))
    scheduler.add_task(Task("C", "meds",    10, 3, start_time="09:00"))
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 2

def test_conflict_only_for_timed_tasks(scheduler):
    """Two tasks with no start_time do not trigger a conflict."""
    scheduler.add_task(Task("A", "walk",    30, 1))
    scheduler.add_task(Task("B", "feeding", 10, 1))
    assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Edge cases: recurring tasks
# ---------------------------------------------------------------------------

def test_mark_complete_once_leaves_pool_empty(scheduler):
    """Completing the only once-off task leaves an empty pool."""
    task = Task("Vet visit", "meds", 30, 1, frequency="once")
    scheduler.add_task(task)
    scheduler.mark_complete(task)
    assert scheduler.tasks == []

def test_recurring_task_inherits_notes(scheduler):
    """The next occurrence of a recurring task keeps the original notes."""
    today = date.today()
    task = Task("Meds", "meds", 5, 1, frequency="daily",
                due_date=today, notes="give with food")
    scheduler.add_task(task)
    scheduler.mark_complete(task)
    next_task = next(t for t in scheduler.tasks if t.name == "Meds")
    assert next_task.notes == "give with food"

def test_recurring_task_not_marked_complete(scheduler):
    """The newly created recurring task starts as incomplete."""
    today = date.today()
    task = Task("Walk", "walk", 30, 1, frequency="daily", due_date=today)
    scheduler.add_task(task)
    scheduler.mark_complete(task)
    next_task = next(t for t in scheduler.tasks if t.name == "Walk")
    assert next_task.completed is False

def test_mark_complete_unknown_task_raises(scheduler):
    """mark_complete on a task not in the pool raises ValueError."""
    ghost = Task("Ghost", "walk", 10, 1)
    with pytest.raises(ValueError):
        scheduler.mark_complete(ghost)