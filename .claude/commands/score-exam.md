# /score-exam — 採点ワークフロー

試験答案PDFの採点を、ガイド付きで実行するスキル。

---

## 実行手順

以下のステップをユーザーと対話しながら順番に進める。

### ステップ1: スクリプトのセットアップ

カレントディレクトリに `setup_coords.py` と `grade.py` が存在するか確認する。

存在しない場合は、リポジトリから取得するよう案内する:

```bash
# リポジトリをクローン済みの場合はスクリプトをコピー
cp /path/to/claude-skill-score-exam/setup_coords.py .
cp /path/to/claude-skill-score-exam/grade.py .
cp /path/to/claude-skill-score-exam/pyproject.toml .
```

または gh でリポジトリをクローンしてからコピーするよう伝える:

```bash
gh repo clone <owner>/claude-skill-score-exam /tmp/score-exam
cp /tmp/score-exam/setup_coords.py .
cp /tmp/score-exam/grade.py .
cp /tmp/score-exam/pyproject.toml .
```

`pyproject.toml` も存在しない場合は同様にコピーする。

> **日本語フォントについて**: 点数の書き込みに日本語フォントを使う場合は、採点後に `config.json` の `font_path` にフォントファイルのパスを設定する（例: `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`）。省略時は PyMuPDF の内蔵フォント（ASCII のみ）を使用。

---

### ステップ2: ファイルの確認

カレントディレクトリの PDF と CSV を `ls` で列挙し、ユーザーに使うファイルを選んでもらう。

### ステップ3: 設定ファイルの確認

`config.json` が存在するか確認する。

- **存在する場合**: `config.json` の `pages_per_student` と `questions` の件数を読んで「前回の設定（X問、1人Yページ）を使いますか？それとも座標を取り直しますか？」と聞く。
- **存在しない場合**: 新規設定として次のステップへ。

### ステップ4: 座標設定（新規または取り直しの場合のみ）

1人あたりの答案ページ数をユーザーに聞いてから、以下を実行する:

```
uv run --isolated setup_coords.py --pdf <PDFファイル> --pages <ページ数>
```

GUI が開くのでユーザーに操作してもらう。「完了しました」と言われたら次へ。

### ステップ5: 採点実行

```
uv run --isolated grade.py --pdf <PDFファイル> --csv <CSVファイル>
```

### ステップ6: 完了報告

出力された人数・平均点を伝え、`output/graded.pdf` を確認するよう案内する。
