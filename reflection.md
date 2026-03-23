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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
