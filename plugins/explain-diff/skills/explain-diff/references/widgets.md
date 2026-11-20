# Widget patterns for explain-diff

Read this only after a candidate passed the three-part gate in SKILL.md (causal, hard to see statically, faithful).

## Patterns that usually earn their place

| Change type | Widget | Input the reader moves | Output the reader watches |
|---|---|---|---|
| Coordinate transform / projection | Draggable object on a grid, two views side by side | object position | source coords, transformed coords, draw/depth order |
| Ordering / sorting / z-index | Small scene with N items, drag to reorder or move | item position or key | resulting order list, which item paints over which |
| Retry, backoff, rate limit, timeout | Timeline | attempt count, base delay, jitter, failure pattern | when each attempt fires, total wait, cap hits |
| Caching / eviction | Step-through of a request sequence | next request key | cache contents, hit/miss, which entry is evicted |
| State machine / reducer change | Clickable event buttons | event to dispatch | current state, highlighted transition, old vs new path |
| Numeric formula (pricing, scoring, layout math) | Sliders for the real parameters | parameter values | result, plus old-formula result for comparison |
| Concurrency / ordering of async work | Step button over a lane diagram | "next tick" | which task runs, what is awaited, where the race was |
| Refactor that changes behavior on edge inputs (guard, trim, new default) | Old-vs-new runner: a row of sample inputs (normal + edge cases from the edge-case pass) | which sample to run, or a small editable input | old output, new output, and a "changed" marker |

The strongest widgets show **old vs. new behavior on the same input**. The reader then sees exactly what the diff changed.

## Patterns that do not earn their place

- Animations that play by themselves with no input.
- A slider whose value only changes a label.
- Re-skinning a static diagram with hover effects.
- Anything for a pure rename, refactor-without-behavior-change, config move, or dependency bump. Use prose and, if needed, a static diagram. (If the refactor *does* change behavior on some inputs, the old-vs-new runner above fits.)

## Implementation rules

- Vanilla JS and inline SVG or `<canvas>` in the same HTML file. No build step. No network.
- Port the real logic: copy the function from the diff into a `<script>` block, translated to JS if needed, with the same constants and names. Put a comment and the `.mirrors` caption naming the source function and file.
- Show numbers, not just shapes: a `.readout` with the live values of inputs and outputs, using the same variable names as the code.
- Support mouse and touch (pointer events). Keep keyboard access for sliders (`<input type="range">`).
- Respect the theme: read colors from the CSS variables (`getComputedStyle(document.documentElement).getPropertyValue('--accent')`).
- Always add a `.static-fallback` (a small static SVG or a table of 3–5 example inputs → outputs). It prints, and it helps readers who skim.
- Keep it small: one idea per widget, usually under ~150 lines of JS. Two focused widgets beat one dashboard.
- Introduce each widget with one sentence that tells the reader what to try ("Drag the stone toward the bottom-left and watch its depth key pass the lantern's.") and close with what they should have noticed.
