---
name: score-exam
description: Grade a combined exam-answer PDF using score.csv, per-question correctness flags, optional point values, and a guided coordinate-picking workflow; generate output/graded.pdf with marks and total scores.
---

# Score Exam

Use this skill when the user asks to score, grade, mark, or annotate a combined exam-answer PDF with a CSV of student answers.

## Workflow

1. Confirm the working directory contains the files needed by the user:
   - one combined answer PDF
   - `score.csv`, or the bundled `assets/score_template.csv` to create it
   - copied helper scripts from this skill, unless the repo already provides them
2. If helper files are missing from the user's working directory, copy them from this skill:

   ```bash
   cp <skill-dir>/scripts/setup_coords.py .
   cp <skill-dir>/scripts/grade.py .
   cp <skill-dir>/pyproject.toml .
   cp <skill-dir>/assets/score_template.csv .
   ```

   Resolve `<skill-dir>` to the directory containing this `SKILL.md`.

3. List available PDFs and choose the target PDF. If there are multiple plausible PDFs and the user did not specify one, ask which PDF to use.
4. Ensure `score.csv` exists.
   - If it does not exist, copy `score_template.csv` to `score.csv` and tell the user to fill in student names and `1` or `0` flags before continuing.
   - `1` means correct, `0` means incorrect.
   - A second row whose name cell is `配点`, `points`, or `点数` is treated as per-question point values.
5. Check for `config.json`.
   - If present, summarize `pages_per_student` and the number of configured questions, then ask whether to reuse it or recapture coordinates.
   - If absent, continue to coordinate setup.
6. For new coordinate setup, ask for pages per student, then run:

   ```bash
   uv run --isolated setup_coords.py --pdf <PDF> --pages <PAGES_PER_STUDENT>
   ```

   The question count is detected from `score.csv` columns named `Q1`, `Q2`, and so on. Use `--questions <N>` only when the CSV is unavailable or the user wants to override detection.

7. The coordinate tool opens a GUI. Wait for the user to finish selecting answer positions and the score position.
8. Run grading:

   ```bash
   uv run --isolated grade.py --pdf <PDF> --csv score.csv
   ```

9. Report the processed student count, average score, and output path from the command output. The default output is `output/graded.pdf`.

## CSV Format

```csv
氏名,Q1,Q2,Q3,Q4,Q5
配点,5,5,10,5,5
山田太郎,1,0,1,1,0
鈴木花子,1,1,1,0,1
```

If the point row is omitted, `config.json`'s `points_per_question` value is used; the default is 5.

## Notes

- The CSV order must match the student order in the combined PDF.
- `setup_coords.py` stores PDF coordinates, not GUI-scaled canvas coordinates.
- `config.json` is generated in the user's working directory and should normally remain task-local.
- For Japanese text insertion, set `font_path` in `config.json`. Numeric score output usually works with the default PyMuPDF font.
