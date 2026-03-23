"""
PawPal+ demo script — run with: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    owner = Owner(
        name="Alex",
        time_available_min=90,
        preferences=["morning walks preferred", "keep meds before meals"],
    )
    pet = Pet(name="Biscuit", species="dog", breed="Beagle", age=4)
    scheduler = Scheduler(owner, pet)

    # Tasks added out of order to exercise sort_by_time
    scheduler.add_task(Task("Evening walk",  "walk",       30, 2, start_time="17:00", frequency="daily"))
    scheduler.add_task(Task("Heartworm med", "meds",        5, 2, start_time="08:30", frequency="daily", notes="give with food"))
    scheduler.add_task(Task("Breakfast",     "feeding",    10, 1, start_time="08:00", frequency="daily"))
    scheduler.add_task(Task("Brushing",      "grooming",   20, 3, start_time="09:00", frequency="weekly"))
    scheduler.add_task(Task("Puzzle toy",    "enrichment", 30, 4, frequency="once"))
    scheduler.add_task(Task("Morning walk",  "walk",       30, 1, start_time="07:30", frequency="daily"))
    # Deliberate conflict: same start_time as Evening walk
    scheduler.add_task(Task("Vet call",      "meds",       15, 2, start_time="17:00", frequency="once"))

    print("=" * 55)
    print("SORTED BY START TIME")
    print("=" * 55)
    for t in scheduler.sort_by_time():
        time_label = t.start_time or "(no time)"
        print(f"  {time_label}  {t.name} ({t.duration_min} min, {t.frequency})")

    print()
    print("=" * 55)
    print("WALKS ONLY (filter by category)")
    print("=" * 55)
    for t in scheduler.filter_by_category("walk"):
        print(f"  {t.name}")

    print()
    print("=" * 55)
    print("CONFLICT DETECTION")
    print("=" * 55)
    for warning in scheduler.detect_conflicts():
        print(f"  ! {warning}")

    print()
    print("=" * 55)
    print("DAILY PLAN + EXPLANATION")
    print("=" * 55)
    plan = scheduler.generate_plan()
    print(scheduler.explain_plan(plan))

    print()
    print("=" * 55)
    print("RECURRING TASK DEMO")
    print("=" * 55)
    breakfast = next(t for t in scheduler.tasks if t.name == "Breakfast")
    print(f"  Before: pool size = {len(scheduler.tasks)}, due {breakfast.due_date}")
    scheduler.mark_complete(breakfast)
    new_breakfast = next((t for t in scheduler.tasks if t.name == "Breakfast"), None)
    print(f"  After:  pool size = {len(scheduler.tasks)}")
    if new_breakfast:
        print(f"  Next 'Breakfast' due: {new_breakfast.due_date}")


if __name__ == "__main__":
    main()