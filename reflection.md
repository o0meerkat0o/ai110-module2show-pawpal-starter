# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The design uses four classes: Task, Pet, Owner, and Scheduler.
Task is a dataclass for one unit of pet care (walk, feeding, grooming, etc.). It stores name, category, duration in minutes, priority (1 = highest), and an is_valid() method to catch bad input.
Pet is a pure data dataclass with name, species, breed, and age. It has no methods since the app centers on one owner/pet pair and the pet itself does not manage tasks.
Owner stores the user's constraints: time_available_min and a preferences list. These are the inputs the Scheduler needs to build a plan.
Scheduler is a regular class (not a dataclass) because its value is in behavior, not data. It holds one Owner, one Pet, and a task pool. Its two core methods are generate_plan() and explain_plan().

**b. Design changes**

Copilot review of #file:pawpal_system.py flagged two issues.
First, explain_plan() only received the included tasks, so it could not explain why tasks were dropped. The fix was adding a self.excluded list that generate_plan() populates, giving explain_plan() access to both sides.
Second, there was no way to edit a task without deleting and re-adding it. Since the README requires add/edit support, an edit_task() stub was added to Scheduler.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two constraints: total time available (time_available_min) and task priority. Priority is the primary sort key; the time budget acts as a hard cutoff. Owner preferences are stored but not yet applied automatically.
Priority was chosen as the main constraint because it is the most direct signal of what the owner actually cares about. Time is a hard physical limit, so it serves as the budget after priority ordering is done.

**b. Tradeoffs**

Conflict detection uses exact start_time string matching rather than checking whether two tasks' time windows overlap (start_time + duration_min). Two tasks at "08:00" are flagged; a 30-minute task at "08:00" and a 10-minute task at "08:20" are not, even though they overlap.
This is reasonable for the current scope because most users will not assign overlapping but non-identical start times, and duration-based overlap detection would require parsing HH:MM strings into integers and comparing ranges, adding complexity for a case that is rare in practice. The warning message is informational, not a hard block, so a false negative here is acceptable.

---

## 3. AI Collaboration

**a. How you used AI**

- Copilot generated the initial Mermaid class diagram from a verbal description, which was faster than writing Mermaid syntax by hand. Inline chat then helped flesh out method stubs for generate_plan() and explain_plan() once the structure was already decided. In the testing phase it suggested edge cases (empty pool, zero budget, three-way conflict) that were not in the original test plan.
- The most useful prompt pattern was a specific file reference plus a concrete question. Asking "does #file:pawpal_system.py have any missing relationships?" produced actionable output. Open-ended questions like "how should I build a scheduler?" did not.

**b. Judgment and verification**

- Copilot suggested putting task management methods (add_task, remove_task, get_tasks) on the Pet class. This was rejected because it would have split scheduling logic across two classes and made Scheduler a thin wrapper with no real responsibility.
- The suggestion was evaluated by tracing a "mark task complete" flow under both designs. With task management on Pet, completing a recurring task would require Pet to call back into Scheduler, creating a circular dependency. With it on Scheduler the flow is linear and there is one place to look when a bug surfaces.

---

## 4. Testing and Verification

**a. What you tested**

- The suite covers five categories: task validation, pool management, recurring logic, sorting and filtering, and scheduling. Validation checks that is_valid() rejects empty names, zero durations, bad priorities, and unrecognised frequency strings. Pool management verifies that add_task, remove_task, and edit_task raise ValueError on bad input. Recurring logic confirms next-day and next-week due dates, that notes carry forward, and that new tasks start incomplete. Scheduling tests verify the plan never exceeds the budget, priority ordering is respected, excluded tasks are logged, and completed tasks are never re-scheduled.
- These behaviors were prioritised because they are the core contract the UI depends on. If generate_plan silently exceeded the budget the UI would show incorrect metrics. If recurring tasks did not create next occurrences the app would silently lose tasks after one day.

**b. Confidence**

- Confidence is high for the happy paths and the edge cases currently covered.
- The main gap is duration-based conflict detection. The current check flags exact start-time matches only, so a 30-minute task at 08:00 and a 10-minute task at 08:20 would not be flagged even though they overlap. Testing overlap properly would require parsing HH:MM into integers and checking interval ranges. That would be the first expansion given more time.

---

## 5. Reflection

**a. What went well**

- Building and testing the logic layer before writing the UI. Because pawpal_system.py had a clean tested interface by the time app.py was written, every UI button mapped directly to an existing method call with no last-minute backend redesign. Debugging was also straightforward: if something looked wrong in the app the first question was whether the backend method had a test covering that case, which usually pointed to the bug immediately.

**b. What you would improve**

- Conflict detection would be the first redesign target. The fix would be to store start times as integers (minutes since midnight) and check whether any two tasks' intervals overlap, then update is_valid() to enforce the format.
- A second improvement would be applying owner.preferences automatically. For example, a preference string "morning walks" could bias walk tasks toward earlier start times during plan generation rather than just printing the preferences at the bottom of the explanation.

**c. Key takeaway**

- AI is most useful when the human has already decided what the system should do. Copilot generated useful code for generate_plan() once the method signature, the role of self.excluded, and the greedy-by-priority strategy were already defined. When the design was vague the suggestions were generic and needed significant revision. The UML and skeleton phases were not just documentation; they gave the AI enough context to produce output that could actually be used.