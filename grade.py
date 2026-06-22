#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

import fitz


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _name_of(row: dict) -> str:
    for key in ("氏名", "name", "Name", "NAME"):
        if key in row:
            return (row.get(key) or "").strip()
    return ""


def load_scores(path: str) -> tuple[dict, list[dict], list[str], list[dict], list[int]]:
    """CSVを読み、(配点マップ, 学生行リスト, ヘッダー, 全行, 学生行番号) を返す。

    2行目（最初のデータ行）の氏名欄が「配点」の場合、その行を各問の
    配点として扱い、学生行から除外する。無ければ配点マップは空。
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    points = {}
    student_start = 0
    if rows and _name_of(rows[0]).casefold() in ("配点", "points", "点数"):
        points_row = rows[0]
        student_start = 1
        for key, val in points_row.items():
            if key in ("氏名", "name", "Name", "NAME"):
                continue
            val = (val or "").strip()
            if val:
                try:
                    points[key] = int(val)
                except ValueError:
                    pass

    students = rows[student_start:]
    student_row_indices = list(range(student_start, len(rows)))
    return points, students, fieldnames, rows, student_row_indices


def graded_csv_path(path: str) -> Path:
    src = Path(path)
    return src.with_name(f"{src.stem}_graded{src.suffix}")


def write_graded_scores(
    path: str,
    fieldnames: list[str],
    rows: list[dict],
    row_scores: dict[int, int],
) -> Path:
    out_path = graded_csv_path(path)
    output_fields = [name for name in fieldnames if name != "Total"] + ["Total"]

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields, extrasaction="ignore")
        writer.writeheader()
        for idx, row in enumerate(rows):
            out_row = dict(row)
            out_row["Total"] = row_scores.get(idx, "")
            writer.writerow(out_row)

    return out_path


def draw_mark(page: fitz.Page, x: float, y: float, correct: bool, cfg: dict):
    r = cfg.get("mark_radius", 12)
    w = cfg.get("mark_width", 2)
    pt = fitz.Point(x, y)

    if correct:
        page.draw_circle(pt, r, color=(0.0, 0.55, 0.0), width=w)
    else:
        d = r * 0.65
        page.draw_line(fitz.Point(x - d, y - d), fitz.Point(x + d, y + d),
                       color=(0.85, 0.0, 0.0), width=w)
        page.draw_line(fitz.Point(x + d, y - d), fitz.Point(x - d, y + d),
                       color=(0.85, 0.0, 0.0), width=w)


def add_score_text(page: fitz.Page, score: int, cfg: dict):
    rect = page.rect
    sx = cfg.get("score_x") or (rect.width - 70)
    sy = cfg.get("score_y") or 40
    fs = cfg.get("score_fontsize", 24)
    font_path = cfg.get("font_path")
    page.insert_text(
        fitz.Point(sx, sy),
        str(score),
        fontsize=fs,
        fontfile=font_path,
        color=(0.8, 0.0, 0.0),
    )


def process_student(
    src: fitz.Document,
    out: fitz.Document,
    idx: int,
    cfg: dict,
    row: dict,
    points: dict,
) -> tuple[str, int]:
    pps = cfg["pages_per_student"]
    default_pts = cfg.get("points_per_question", 5)
    questions = cfg["questions"]

    start = idx * pps
    out.insert_pdf(src, from_page=start, to_page=start + pps - 1)
    base = out.page_count - pps

    total = 0
    for q in questions:
        mark = row.get(q["id"], "").strip()
        is_correct = mark == "1"
        if is_correct:
            total += points.get(q["id"], default_pts)
        page_idx = q["page"]
        if page_idx < pps:
            draw_mark(out[base + page_idx], q["x"], q["y"], is_correct, cfg)

    score_page = cfg.get("score_page", 0)
    add_score_text(out[base + score_page], total, cfg)

    name = _name_of(row) or f"student_{idx + 1:03d}"
    return name, total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--output", default="output/graded.pdf")
    args = parser.parse_args()

    cfg = load_config(args.config)
    points, students, fieldnames, csv_rows, student_row_indices = load_scores(args.csv)
    out_path = Path(args.output)
    out_path.parent.mkdir(exist_ok=True)

    src = fitz.open(args.pdf)
    pps = cfg["pages_per_student"]

    if src.page_count < len(students) * pps:
        print(f"警告: PDFページ数({src.page_count}) < 学生数×ページ数({len(students) * pps})")

    print(f"{len(students)}名分を処理中...")
    out = fitz.open()
    results = []
    row_scores = {}
    for i, row in enumerate(students):
        if (i + 1) * pps > src.page_count:
            print(f"  [{i + 1}] ページ不足のためスキップ")
            continue
        name, score = process_student(src, out, i, cfg, row, points)
        results.append((name, score))
        row_scores[student_row_indices[i]] = score
        print(f"  [{i + 1:3d}] {name}: {score}点")

    out.save(out_path, garbage=4, deflate=True)
    out.close()
    src.close()

    avg = sum(s for _, s in results) / len(results) if results else 0
    graded_scores_path = write_graded_scores(args.csv, fieldnames, csv_rows, row_scores)
    print(f"\n完了: {len(results)}名  平均点: {avg:.1f}点")
    print(f"出力先: {out_path}")
    print(f"採点CSV: {graded_scores_path}")


if __name__ == "__main__":
    main()
