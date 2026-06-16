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
    return row.get("氏名", row.get("name", "")).strip()


def load_scores(path: str) -> tuple[dict, list[dict]]:
    """CSVを読み、(配点マップ, 学生行リスト) を返す。

    2行目（最初のデータ行）の氏名欄が「配点」の場合、その行を各問の
    配点として扱い、学生行から除外する。無ければ配点マップは空。
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    points = {}
    if rows and _name_of(rows[0]) in ("配点", "points", "点数"):
        points_row = rows.pop(0)
        for key, val in points_row.items():
            if key in ("氏名", "name"):
                continue
            val = (val or "").strip()
            if val:
                try:
                    points[key] = int(val)
                except ValueError:
                    pass
    return points, rows


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
        if mark not in ("1", "0"):
            continue
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
    points, students = load_scores(args.csv)
    out_path = Path(args.output)
    out_path.parent.mkdir(exist_ok=True)

    src = fitz.open(args.pdf)
    pps = cfg["pages_per_student"]

    if src.page_count < len(students) * pps:
        print(f"警告: PDFページ数({src.page_count}) < 学生数×ページ数({len(students) * pps})")

    print(f"{len(students)}名分を処理中...")
    out = fitz.open()
    results = []
    for i, row in enumerate(students):
        if (i + 1) * pps > src.page_count:
            print(f"  [{i + 1}] ページ不足のためスキップ")
            continue
        name, score = process_student(src, out, i, cfg, row, points)
        results.append((name, score))
        print(f"  [{i + 1:3d}] {name}: {score}点")

    out.save(out_path, garbage=4, deflate=True)
    out.close()
    src.close()

    avg = sum(s for _, s in results) / len(results) if results else 0
    print(f"\n完了: {len(results)}名  平均点: {avg:.1f}点")
    print(f"出力先: {out_path}")


if __name__ == "__main__":
    main()
