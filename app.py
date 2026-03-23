"""
PawPal+ Streamlit UI — run with: streamlit run app.py
"""

import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, VALID_FREQUENCIES

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

for key in ("owner", "pet", "scheduler", "last_plan", "last_explanation"):
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾")
st.title("🐾 PawPal+")
st.caption("A daily care planner for your pet.")

# ---------------------------------------------------------------------------
# Setup screen
# ---------------------------------------------------------------------------

if st.session_state.owner is None or st.session_state.pet is None:
    st.header("Set up your profile")

    with st.form("setup_form"):
        st.subheader("Owner info")
        owner_name       = st.text_input("Your name")
        time_available   = st.number_input("Time available today (minutes)", min_value=1, value=60, step=5)
        preferences_raw  = st.text_input("Preferences (comma-separated, optional)",
                                          placeholder="morning walks, meds before meals")

        st.subheader("Pet info")
        pet_name = st.text_input("Pet name")
        species  = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        breed    = st.text_input("Breed (optional)")
        age      = st.number_input("Age (years)", min_value=0, value=1, step=1)

        submitted = st.form_submit_button("Save profile")

    if submitted:
        if not owner_name or not pet_name:
            st.error("Please fill in both your name and your pet's name.")
        else:
            prefs = [p.strip() for p in preferences_raw.split(",") if p.strip()]
            st.session_state.owner     = Owner(owner_name, int(time_available), prefs)
            st.session_state.pet       = Pet(pet_name, species, breed, int(age))
            st.session_state.scheduler = Scheduler(st.session_state.owner, st.session_state.pet)
            st.rerun()

    st.stop()

# ---------------------------------------------------------------------------
# Convenience references
# ---------------------------------------------------------------------------

owner: Owner         = st.session_state.owner
pet: Pet             = st.session_state.pet
scheduler: Scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Profile")
    st.write(f"**Owner:** {owner.name}")
    breed_str = f", {pet.breed}" if pet.breed else ""
    st.write(f"**Pet:** {pet.name} ({pet.species}{breed_str})")
    st.write(f"**Time budget:** {owner.time_available_min} min")
    if owner.preferences:
        st.write("**Preferences:**")
        for p in owner.preferences:
            st.write(f"- {p}")
    st.divider()
    if st.button("Reset / start over"):
        for k in ("owner", "pet", "scheduler", "last_plan", "last_explanation"):
            st.session_state[k] = None
        st.rerun()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_tasks, tab_sorted, tab_plan = st.tabs(["Manage tasks", "View & filter", "Today's plan"])

# ---------------------------------------------------------------------------
# Tab 1: Add / remove / complete tasks
# ---------------------------------------------------------------------------

with tab_tasks:
    st.subheader(f"Tasks for {pet.name}")

    # Conflict banner — show at top of task tab so owner sees it immediately
    conflicts = scheduler.detect_conflicts()
    for w in conflicts:
        st.warning(f"Time conflict: {w}")

    with st.form("add_task_form", clear_on_submit=True):
        st.write("**Add a task**")
        col1, col2 = st.columns(2)
        with col1:
            task_name  = st.text_input("Task name", placeholder="Morning walk")
            category   = st.selectbox("Category",
                             ["walk", "feeding", "meds", "grooming", "enrichment", "other"])
            start_time = st.text_input("Start time (HH:MM, optional)", placeholder="08:00")
        with col2:
            duration   = st.number_input("Duration (min)", min_value=1, value=15, step=5)
            priority   = st.number_input("Priority (1 = highest)", min_value=1, value=2, step=1)
            frequency  = st.selectbox("Frequency", list(VALID_FREQUENCIES))
        notes = st.text_input("Notes (optional)", placeholder="Give with food")
        add_submitted = st.form_submit_button("Add task")

    if add_submitted:
        try:
            scheduler.add_task(Task(
                name=task_name, category=category,
                duration_min=int(duration), priority=int(priority),
                start_time=start_time.strip(), frequency=frequency, notes=notes,
            ))
            st.success(f"Added: {task_name}")
            # Re-check conflicts after adding
            new_conflicts = scheduler.detect_conflicts()
            for w in new_conflicts:
                st.warning(f"Time conflict detected: {w}")
        except ValueError as e:
            st.error(str(e))

    if not scheduler.tasks:
        st.info("No tasks yet. Add one above.")
    else:
        st.write(f"**{len(scheduler.tasks)} task(s):**")
        for i, task in enumerate(scheduler.tasks):
            col_info, col_done, col_rm = st.columns([5, 1, 1])
            with col_info:
                badge = "~~" if task.completed else ""
                time_str = f" @ {task.start_time}" if task.start_time else ""
                st.write(
                    f"{badge}**{task.name}**{badge}{time_str} | {task.category} | "
                    f"{task.duration_min} min | priority {task.priority} | {task.frequency}"
                    + (f" | _{task.notes}_" if task.notes else "")
                )
            with col_done:
                if not task.completed and st.button("Done", key=f"done_{i}"):
                    try:
                        scheduler.mark_complete(task)
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            with col_rm:
                if st.button("Remove", key=f"remove_{i}"):
                    try:
                        scheduler.remove_task(task)
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

# ---------------------------------------------------------------------------
# Tab 2: Sorted / filtered view
# ---------------------------------------------------------------------------

with tab_sorted:
    st.subheader("View and filter tasks")

    if not scheduler.tasks:
        st.info("No tasks yet.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            show_filter = st.selectbox("Filter by category",
                ["All"] + ["walk", "feeding", "meds", "grooming", "enrichment", "other"])
        with col_b:
            show_incomplete_only = st.checkbox("Incomplete only", value=True)
        show_today = st.checkbox("Due today only", value=False)

        # Build the view
        tasks_view = scheduler.sort_by_time()

        if show_filter != "All":
            tasks_view = [t for t in tasks_view if t.category == show_filter]
        if show_incomplete_only:
            tasks_view = [t for t in tasks_view if not t.completed]
        if show_today:
            today = date.today()
            tasks_view = [t for t in tasks_view if t.due_date == today]

        if not tasks_view:
            st.info("No tasks match the current filters.")
        else:
            rows = []
            for t in tasks_view:
                rows.append({
                    "Name":        t.name,
                    "Start":       t.start_time or "(none)",
                    "Category":    t.category,
                    "Duration":    f"{t.duration_min} min",
                    "Priority":    t.priority,
                    "Frequency":   t.frequency,
                    "Due":         str(t.due_date),
                    "Done":        "Yes" if t.completed else "No",
                    "Notes":       t.notes,
                })
            st.dataframe(rows, use_container_width=True)

        # Conflict summary in this tab too
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.divider()
            st.write("**Conflict warnings**")
            for w in conflicts:
                st.warning(w)
        else:
            st.success("No time conflicts detected.")

# ---------------------------------------------------------------------------
# Tab 3: Daily plan
# ---------------------------------------------------------------------------

with tab_plan:
    st.subheader("Today's plan")

    incomplete = scheduler.filter_incomplete()
    if not incomplete:
        st.info("No incomplete tasks to schedule. Add some in the Manage tasks tab.")
    else:
        if st.button("Generate plan"):
            plan = scheduler.generate_plan()
            st.session_state["last_plan"]        = plan
            st.session_state["last_explanation"] = scheduler.explain_plan(plan)

    if st.session_state["last_plan"] is not None:
        plan        = st.session_state["last_plan"]
        explanation = st.session_state["last_explanation"]

        # Conflict warnings at the top of the plan
        conflicts = scheduler.detect_conflicts()
        for w in conflicts:
            st.warning(f"Heads up: {w}")

        time_used = sum(t.duration_min for t in plan)
        remaining = owner.time_available_min - time_used
        c1, c2, c3 = st.columns(3)
        c1.metric("Tasks scheduled", len(plan))
        c2.metric("Time used",        f"{time_used} min")
        c3.metric("Time remaining",   f"{remaining} min")

        if plan:
            st.write("**Scheduled tasks (sorted by priority):**")
            for rank, task in enumerate(plan, start=1):
                time_str = f" @ {task.start_time}" if task.start_time else ""
                label = (
                    f"{rank}. **{task.name}**{time_str} — "
                    f"{task.duration_min} min ({task.category}, {task.frequency})"
                    + (f" — _{task.notes}_" if task.notes else "")
                )
                st.success(label)
        else:
            st.error("No tasks fit within your available time.")

        if scheduler.excluded:
            with st.expander(f"Excluded tasks ({len(scheduler.excluded)}) — did not fit"):
                for task in scheduler.excluded:
                    st.write(f"- **{task.name}** ({task.duration_min} min, priority {task.priority})")

        with st.expander("Full explanation"):
            st.text(explanation)