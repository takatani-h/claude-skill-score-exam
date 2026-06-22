# AGENTS.md

This repository contains a Codex skill for grading combined exam-answer PDFs.

## Development Commands

Run the scripts with uv:

```bash
uv run --isolated setup_coords.py --pdf <PDF> --pages <pages-per-student>
uv run --isolated grade.py --pdf <PDF> --csv <CSV>
```

There is no test framework or linter configured.

## Architecture

The root scripts are the development copy. The installable Codex skill lives at `.codex/skills/score-exam/` and bundles copies of the scripts plus `score_template.csv`.

- `setup_coords.py`: Opens a tkinter GUI, renders PDF pages, and records per-question mark positions plus the total-score position into `config.json`.
- `grade.py`: Reads `config.json` and `score.csv`, copies each student's page range, draws correct/incorrect marks, and writes the total score.
- `.codex/skills/score-exam/SKILL.md`: Codex workflow instructions for guided grading.

Keep root script behavior and bundled skill scripts in sync when changing functionality.

## Data Assumptions

- `score.csv` uses `Q1`, `Q2`, ... columns.
- The optional first data row named `配点`, `points`, or `点数` defines per-question point values.
- Student order in the CSV must match page order in the combined PDF.
- `config.json` stores unscaled PDF coordinates.
