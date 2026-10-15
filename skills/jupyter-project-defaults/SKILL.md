---
name: jupyter-project-defaults
description: Create, edit, or review Jupyter notebooks for clear learning and reliable GitHub rendering. Use for `.ipynb` work that should pair nearby Markdown explanations with code, favor static plots, and minimize widgets. Requires `python-project-defaults` installed alongside this skill.
---

# Jupyter Project Defaults

## Python Project Foundation

Before installing dependencies, configuring the environment, or running Python and Jupyter commands, read and apply [python-project-defaults](../python-project-defaults/SKILL.md). Treat that skill as the single source of truth for dependency management and execution; do not duplicate or override its uv-first fallback policy here.

- Add Jupyter, kernels, plotting packages, and notebook dependencies through the shared Python project workflow.
- Run Jupyter and notebook execution commands using the project environment and execution workflow selected by `python-project-defaults`.
- Do not use `%pip`, `!pip`, or ad hoc installation cells inside the notebook.
- If the referenced Python defaults skill is unavailable, stop and tell the user rather than inventing a separate dependency workflow.

## Learning Flow

Interleave Markdown and code cells so every meaningful piece of code has a nearby explanation.

- Put a short Markdown cell immediately before code to explain its purpose, assumptions, and what to observe. Add a nearby Markdown interpretation after the output when the result needs discussion.
- Keep an explanation and its code adjacent or separated by no more than the directly related output. Do not place several code cells between a concept and its explanation.
- Split long, multi-concept code into smaller cells with local explanations. Avoid unexplained or orphaned code cells.
- Use headings and brief transitions to make the notebook readable from top to bottom as a lesson, not merely as a transcript of experiments.
- Explain important output, tradeoffs, and surprising results instead of expecting the reader to infer them from code alone.

## GitHub-Friendly Outputs

Design the notebook to remain useful in GitHub's static notebook preview without a live kernel.

- Avoid Jupyter widgets by default. Use a widget only when it is clearly the best way to explain the concept and its benefit outweighs the loss of interactivity on GitHub.
- Whenever a widget is necessary, include a nearby static fallback such as representative plots, tables, selected parameter examples, or screenshots plus Markdown explanation. Never make a widget the only way to understand a result.
- Prefer ordinary code parameters and several representative static outputs over interactive controls when they teach the same concept adequately.
- Execute the notebook before delivery and preserve meaningful outputs that GitHub can render. Remove accidental errors, stale outputs, noisy logs, and excessively large tabular dumps.

## Plot Frequently

Use plots often when a visual can improve understanding of data, behavior, comparisons, distributions, trends, geometry, or model results.

- Prefer static Matplotlib or Seaborn figures whose image output is embedded directly in the notebook and renders on GitHub.
- Give every instructional plot an informative title and useful axis labels; add legends, annotations, or reference lines when they clarify the lesson.
- Place a Markdown interpretation immediately before or after each nontrivial plot so the reader knows what pattern matters and why.
- If an interactive plotting library is genuinely useful, also include a static image fallback. Do not assume GitHub will render interactive JavaScript output.
- Do not add decorative plots that obscure rather than strengthen the explanation.

## Verification

Restart the kernel, then run the notebook from top to bottom using the project environment selected by `python-project-defaults`. Confirm that it completes without unintended errors, that outputs are current, that Markdown remains close to the code and figures it explains, and that every widget-dependent idea has a static GitHub-readable fallback.
