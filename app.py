"""
PawPal+ Streamlit UI — run with: streamlit run app.py
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Session state initialisation
# st.session_state persists across reruns for the lifetime of the browser tab.
# We check before creating so we never overwrite existing data on rerun.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

if "pet" not in st.session_state:
    st.session_state.pet = None

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾")
st.title("🐾 PawPal+")
st.caption("A daily care planner for your pet.")

# ---------------------------------------------------------------------------
# Step 1: Owner + Pet setup
# Only shown until both are created.
# ---------------------------------------------------------------------------

if st.session_state.owner is None or st.session_state.pet is None:
    st.header("Set up your profile")

    with st.form("setup_form"):
        st.subheader("Owner info")
        owner_name = st.text_input("Your name")
        time_available = st.number_input(
            "Time available today (minutes)", min_value=1, value=60, step=5
        )
        preferences_raw = st.text_input(
            "Preferences (comma-separated, optional)",
            placeholder="morning walks, meds before meals",
        )

        st.subheader("Pet info")
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        breed = st.text_input("Breed (optional)")
        age = st.number_input("Age (years)", min_value=0, value=1, step=1)

        submitted = st.form_submit_button("Save profile")

    if submitted:
        if not owner_name or not pet_name:
            st.error("Please fill in both your name and your pet's name.")
        else:
            prefs = [p.strip() for p in preferences_raw.split(",") if p.strip()]
            st.session_state.owner = Owner(
                name=owner_name,
                time_available_min=int(time_available),
                preferences=prefs,
            )
            st.session_state.pet = Pet(
                name=pet_name, species=species, breed=breed, age=int(age)
            )
            st.session_state.scheduler = Scheduler(
                st.session_state.owner, st.session_state.pet
            )
            st.rerun()

    st.stop()  # nothing else renders until setup is complete

# ---------------------------------------------------------------------------
# Convenience references (session state is set from here down)
# ---------------------------------------------------------------------------

owner: Owner = st.session_state.owner
pet: Pet = st.session_state.pet
scheduler: Scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
# Sidebar: profile summary + reset
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Profile")
    st.write(f"**Owner:** {owner.name}")
    st.write(f"**Pet:** {pet.name} ({pet.species}{',' if pet.breed else ''} {pet.breed})")
    st.write(f"**Time budget:** {owner.time_available_min} min")
    if owner.preferences:
        st.write("**Preferences:**")
        for p in owner.preferences:
            st.write(f"- {p}")

    st.divider()
    if st.button("Reset / start over"):
        for key in ["owner", "pet", "scheduler"]:
            st.session_state[key] = None
        st.rerun()

# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------

tab_tasks, tab_plan = st.tabs(["Manage tasks", "Today's plan"])

# ---------------------------------------------------------------------------
# Tab 1: Add / remove tasks
# ---------------------------------------------------------------------------

with tab_tasks:
    st.subheader(f"Tasks for {pet.name}")

    with st.form("add_task_form", clear_on_submit=True):
        st.write("**Add a task**")
        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input("Task name", placeholder="Morning walk")
            category = st.selectbox(
                "Category", ["walk", "feeding", "meds", "grooming", "enrichment", "other"]
            )
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, value=15, step=5)
            priority = st.number_input("Priority (1 = highest)", min_value=1, value=2, step=1)
        notes = st.text_input("Notes (optional)", placeholder="Give with food")
        add_submitted = st.form_submit_button("Add task")

    if add_submitted:
        new_task = Task(
            name=task_name,
            category=category,
            duration_min=int(duration),
            priority=int(priority),
            notes=notes,
        )
        try:
            scheduler.add_task(new_task)
            st.success(f"Added: {task_name}")
        except ValueError as e:
            st.error(str(e))

    # Task list with remove buttons
    if not scheduler.tasks:
        st.info("No tasks yet. Add one above.")
    else:
        st.write(f"**{len(scheduler.tasks)} task(s) in pool:**")
        for i, task in enumerate(scheduler.tasks):
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.write(
                    f"**{task.name}** | {task.category} | "
                    f"{task.duration_min} min | priority {task.priority}"
                    + (f" | _{task.notes}_" if task.notes else "")
                )
            with col_btn:
                if st.button("Remove", key=f"remove_{i}"):
                    try:
                        scheduler.remove_task(task)
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

# ---------------------------------------------------------------------------
# Tab 2: Generate and display the daily plan
# ---------------------------------------------------------------------------

with tab_plan:
    st.subheader("Today's plan")

    if not scheduler.tasks:
        st.info("Add some tasks first, then generate a plan.")
    else:
        if st.button("Generate plan"):
            plan = scheduler.generate_plan()
            st.session_state["last_plan"] = plan
            st.session_state["last_explanation"] = scheduler.explain_plan(plan)

    if "last_plan" in st.session_state and st.session_state["last_plan"] is not None:
        plan = st.session_state["last_plan"]
        explanation = st.session_state["last_explanation"]

        time_used = sum(t.duration_min for t in plan)
        st.metric("Tasks scheduled", len(plan))
        st.metric("Time used", f"{time_used} min", delta=f"{owner.time_available_min - time_used} min remaining")

        if plan:
            st.write("**Scheduled tasks (in order):**")
            for rank, task in enumerate(plan, start=1):
                st.write(
                    f"{rank}. **{task.name}** — {task.duration_min} min "
                    f"({task.category}, priority {task.priority})"
                    + (f" — _{task.notes}_" if task.notes else "")
                )

        if scheduler.excluded:
            with st.expander(f"Excluded tasks ({len(scheduler.excluded)})"):
                for task in scheduler.excluded:
                    st.write(
                        f"- **{task.name}** ({task.duration_min} min) "
                        f"— did not fit in remaining time"
                    )

        with st.expander("Full explanation"):
            st.text(explanation)