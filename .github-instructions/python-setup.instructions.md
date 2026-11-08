---
name: Python Environment Rules
description: Instructions for managing python environments in this project.
applyTo: "**/*.py"
---
# Environment Instructions
- Always use `uv` for package management and virtual environments.
- The virtual environment is located at `./.euv_scrap_recipes`.
- Before running any python script, ensure the environment is activated using `source .euv_scrap_recipes/bin/activate`.