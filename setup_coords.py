#!/usr/bin/env python3
import argparse
import io
import json
import tkinter as tk
from tkinter import messagebox, simpledialog

import fitz
from PIL import Image, ImageTk

DISPLAY_SCALE = 1.5
PHASE_QUESTIONS = "questions"
PHASE_SCORE = "score"


class CoordPicker:
    def __init__(self, pdf_path: str, config_path: str, num_questions: int, pages_per_student: int):
        self.config_path = config_path
        self.num_questions = num_questions
        self.pages_per_student = pages_per_student
        self.questions: list[dict] = []
        self.current_q = 0
        self.current_page = 0
        self.phase = PHASE_QUESTIONS

        self.pdf = fitz.open(pdf_path)
        self.config = self._load_config()
        self._build_ui()

    def _load_config(self) -> dict:
        try:
            with open(self.config_path, encoding="utf-8") as f:
                cfg = json.load(f)
        except FileNotFoundError:
            cfg = {}
        cfg["pages_per_student"] = self.pages_per_student
        cfg.setdefault("points_per_question", 5)
        cfg.setdefault("mark_radius", 12)
        cfg.setdefault("mark_width", 2)
        cfg.setdefault("font_path", None)  # config.json の font_path で日本語フォントを指定
        cfg.setdefault("score_page", 0)
        cfg.setdefault("score_x", None)
        cfg.setdefault("score_y", None)
        cfg.setdefault("score_fontsize", 24)
        return cfg

    def _render_page(self, page_idx: int):
        page = self.pdf[page_idx]
        mat = fitz.Matrix(DISPLAY_SCALE, DISPLAY_SCALE)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("ppm")))
        return ImageTk.PhotoImage(img), img.width, img.height

    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title("座標設定")

        self.info_label = tk.Label(self.root, font=("Helvetica", 13), pady=8)
        self.info_label.pack()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=8, pady=2)

        if self.pages_per_student > 1:
            tk.Button(btn_frame, text="← 前ページ", command=self._prev_page).pack(side=tk.LEFT, padx=4)
            tk.Button(btn_frame, text="次ページ →", command=self._next_page).pack(side=tk.LEFT, padx=4)

        tk.Button(btn_frame, text="1つ戻す", command=self._undo).pack(side=tk.RIGHT, padx=4)

        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        vsb = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        hsb = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.canvas = tk.Canvas(canvas_frame, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.canvas.yview)
        hsb.config(command=self.canvas.xview)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self._on_click)
        self._refresh()
        self.root.mainloop()

    def _refresh(self):
        self.canvas.delete("all")
        self.photo, w, h = self._render_page(self.current_page)
        self.canvas.config(
            width=min(w, 1000), height=min(h, 750),
            scrollregion=(0, 0, w, h),
        )
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        for q in self.questions:
            if q["page"] == self.current_page:
                self._draw_marker(q["_cx"], q["_cy"], q["id"], color="red")

        if self.phase == PHASE_QUESTIONS:
            n = self.current_q + 1
            self.info_label.config(
                text=f"Q{n} の正答位置をクリック  "
                     f"（{n}/{self.num_questions}問  "
                     f"ページ {self.current_page + 1}/{self.pages_per_student}）"
            )
        else:
            self.info_label.config(
                text=f"点数を表示する位置をクリック  "
                     f"（ページ {self.current_page + 1}/{self.pages_per_student}）"
            )

    def _draw_marker(self, cx: float, cy: float, label: str, color: str = "red"):
        r = 6
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline=color)
        self.canvas.create_text(cx + 14, cy, text=label, fill=color, anchor=tk.W,
                                font=("Helvetica", 11, "bold"))

    def _on_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        x_pdf = round(cx / DISPLAY_SCALE)
        y_pdf = round(cy / DISPLAY_SCALE)

        if self.phase == PHASE_QUESTIONS:
            if self.current_q >= self.num_questions:
                return
            q_id = f"Q{self.current_q + 1}"
            self.questions.append({
                "id": q_id,
                "page": self.current_page,
                "x": x_pdf,
                "y": y_pdf,
                "_cx": cx,
                "_cy": cy,
            })
            self._draw_marker(cx, cy, q_id, color="red")
            self.current_q += 1

            if self.current_q >= self.num_questions:
                self.phase = PHASE_SCORE
                self.current_page = 0
                self._refresh()
        else:
            self._draw_marker(cx, cy, "点数", color="blue")
            self.config["score_page"] = self.current_page
            self.config["score_x"] = x_pdf
            self.config["score_y"] = y_pdf
            self._save()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh()

    def _next_page(self):
        if self.current_page < self.pages_per_student - 1:
            self.current_page += 1
            self._refresh()

    def _undo(self):
        if self.phase == PHASE_SCORE:
            self.phase = PHASE_QUESTIONS
            self.current_q = self.num_questions - 1
            last = self.questions.pop()
            self.current_page = last["page"]
            self._refresh()
            return
        if not self.questions:
            return
        removed = self.questions.pop()
        self.current_q -= 1
        self.current_page = removed["page"]
        self._refresh()

    def _save(self):
        clean = [
            {"id": q["id"], "page": q["page"], "x": q["x"], "y": q["y"]}
            for q in self.questions
        ]
        self.config["questions"] = clean
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("完了",
            f"{len(clean)}問の座標と点数位置を {self.config_path} に保存しました。")
        self.root.destroy()


def ask_int(title: str, prompt: str, min_val: int = 1) -> int:
    root = tk.Tk()
    root.withdraw()
    while True:
        val = simpledialog.askinteger(title, prompt, parent=root, minvalue=min_val)
        if val is not None:
            root.destroy()
            return val


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--pages", type=int, default=1)
    args = parser.parse_args()

    num_questions = ask_int("問題数", "問題数を入力してください:")
    CoordPicker(args.pdf, args.config, num_questions, args.pages)


if __name__ == "__main__":
    main()
