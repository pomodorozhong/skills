---
name: python-project-defaults
description: Apply uv-first dependency management and execution defaults when creating, configuring, installing, locking, or running Python projects and tools. Use Homebrew only when uv is not an option, then stop and consult the user if neither can satisfy the need.
---

# Python Project Defaults

Use `uv` as the first choice for Python project setup, dependency management, tool installation, and execution unless the user explicitly requires another workflow.

- For a new Python project, use `pyproject.toml` and `uv.lock`; use `uv init` when initialization is useful.
- Manage dependencies with `uv add`, `uv remove`, `uv sync`, and `uv lock` instead of invoking `pip` directly.
- Run project commands, modules, scripts, tests, and registered entry points with `uv run`.
- Use `uvx` or `uv tool run` for disposable third-party Python command-line tools when they do not belong in project dependencies.
- Prefer direct `uv run <command>` entry points over shell wrappers that only activate an environment or forward arguments.
- Keep `.venv/` and uv caches out of version control; normally commit both `pyproject.toml` and `uv.lock` for applications.
- Do not add `uv.toml` merely to accommodate Codex's sandbox or cache permissions. Set `UV_CACHE_DIR` only for the affected tool invocation when needed.

Use this fallback order for dependencies and required tooling:

1. Always try `uv` first.
2. If `uv` genuinely cannot satisfy the requirement, check whether Homebrew can provide the dependency or tool and prefer Homebrew next.
3. If neither `uv` nor Homebrew is a viable option, stop before using `pip`, Poetry, Conda, Hatch, pyenv, manual installers, curl-based installers, or another package manager, and consult the user.

Do not mix dependency managers or lockfiles. Preserve an established non-uv workflow when changing it is outside the requested scope; if that workflow requires installing or changing dependencies, pause and consult the user before proceeding with a non-uv manager.
