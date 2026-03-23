/**
 * PawPal+ UML class diagram (final)
 * Reflects the full implementation including sorting, filtering,
 * recurring tasks, and conflict detection.
 *
 * Usage:
 *   1. <div id="pawpal-diagram"></div>
 *   2. <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
 *   3. import { renderDiagram } from './pawpal_diagram.js';
 *      renderDiagram('#pawpal-diagram');
 */

export const PAWPAL_DIAGRAM = `
classDiagram
  class Owner {
    +str name
    +int time_available_min
    +list preferences
  }
  class Pet {
    +str name
    +str species
    +str breed
    +int age
  }
  class Task {
    +str name
    +str category
    +int duration_min
    +int priority
    +str start_time
    +str frequency
    +date due_date
    +bool completed
    +str notes
    +is_valid() bool
    +mark_complete() Task
  }
  class Scheduler {
    +Owner owner
    +Pet pet
    +list tasks
    +list excluded
    +add_task(task) None
    +remove_task(task) None
    +edit_task(old, new) None
    +mark_complete(task) None
    +sort_by_time() list
    +filter_by_category(cat) list
    +filter_incomplete() list
    +filter_by_date(date) list
    +detect_conflicts() list
    +generate_plan() list
    +explain_plan(plan) str
  }
  Owner "1" --> "1" Pet : owns
  Scheduler "1" --> "1" Owner : uses
  Scheduler "1" --> "1" Pet : uses
  Scheduler "1" --> "0..*" Task : manages
  Task "1" ..> "0..1" Task : creates next occurrence
`;

/**
 * Initialise Mermaid and render the PawPal+ class diagram.
 * @param {string} selector  CSS selector for the target element.
 * @param {object} options   Optional Mermaid config overrides.
 */
export async function renderDiagram(selector = '#pawpal-diagram', options = {}) {
  if (typeof mermaid === 'undefined') {
    throw new Error('Mermaid is not loaded.');
  }
  mermaid.initialize({ startOnLoad: false, theme: 'base', fontFamily: 'sans-serif', ...options });
  const container = document.querySelector(selector);
  if (!container) throw new Error(`No element found for "${selector}".`);
  const { svg } = await mermaid.render('pawpal-diagram-svg', PAWPAL_DIAGRAM);
  container.innerHTML = svg;
}
