/**
 * PawPal+ UML class diagram
 * Renders a Mermaid.js classDiagram into a target DOM element.
 *
 * Usage:
 *   1. Add a container to your HTML:  <div id="pawpal-diagram"></div>
 *   2. Load Mermaid:  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
 *   3. Import and call:  import { renderDiagram } from './pawpal_diagram.js';
 *                        renderDiagram('#pawpal-diagram');
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
    +str notes
    +is_valid() bool
  }
  class Scheduler {
    +Owner owner
    +Pet pet
    +list tasks
    +add_task(task) None
    +remove_task(task) None
    +generate_plan() list
    +explain_plan(plan) str
  }
  Owner "1" --> "1" Pet : owns
  Scheduler "1" --> "1" Owner : uses
  Scheduler "1" --> "1" Pet : uses
  Scheduler "1" --> "0..*" Task : schedules
`;

/**
 * Initialise Mermaid and render the PawPal+ class diagram.
 *
 * @param {string} selector  CSS selector for the target container element.
 * @param {object} options   Optional Mermaid config overrides.
 */
export async function renderDiagram(selector = '#pawpal-diagram', options = {}) {
  if (typeof mermaid === 'undefined') {
    throw new Error(
      'Mermaid is not loaded. Add the Mermaid CDN script before calling renderDiagram().'
    );
  }

  mermaid.initialize({
    startOnLoad: false,
    theme: 'base',
    fontFamily: 'sans-serif',
    ...options,
  });

  const container = document.querySelector(selector);
  if (!container) {
    throw new Error(`No element found for selector "${selector}".`);
  }

  const { svg } = await mermaid.render('pawpal-diagram-svg', PAWPAL_DIAGRAM);
  container.innerHTML = svg;
}
