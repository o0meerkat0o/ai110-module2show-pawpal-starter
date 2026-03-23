"""
PawPal+ demo script — run with: python main.py
Verifies the core scheduling logic in the terminal before touching the UI.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    owner = Owner(
        name="Alex",
        time_available_min=90,
        preferences=["morning walks preferred", "keep meds before meals"],
    )
    pet = Pet(name="Biscuit", species="dog", breed="Beagle", age=4)

    scheduler = Scheduler(owner, pet)

    scheduler.add_task(Task("Morning walk",   "walk",     duration_min=30, priority=1))
    scheduler.add_task(Task("Breakfast",      "feeding",  duration_min=10, priority=1))
    scheduler.add_task(Task("Heartworm med",  "meds",     duration_min=5,  priority=2,
                            notes="give with food"))
    scheduler.add_task(Task("Brushing",       "grooming", duration_min=20, priority=3))
    scheduler.add_task(Task("Puzzle toy",     "enrichment",duration_min=30,priority=4))
    scheduler.add_task(Task("Evening walk",   "walk",     duration_min=30, priority=2))

    plan = scheduler.generate_plan()

    print("=" * 50)
    print(scheduler.explain_plan(plan))
    print("=" * 50)


if __name__ == "__main__":
    main()