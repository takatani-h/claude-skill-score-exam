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
cp /path/to/claude-skill-score-exam/score_template.csv .
```

または git でリポジトリをクローンしてからコピーするよう伝える:

```bash
git clone https://github.com/takatani-h/claude-skill-score-exam.git /tmp/score-exam
cp /tmp/score-exam/setup_coords.py .
cp /tmp/score-exam/grade.py .
cp /tmp/score-exam/pyproject.toml .
cp /tmp/score-exam/score_template.csv .
```

`pyproject.toml` も存在しない場合は同様にコピーする。

> **日本語フォントについて**: 点数の書き込みに日本語フォントを使う場合は、採点後に `config.json` の `font_path` にフォントファイルのパスを設定する（例: `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`）。省略時は PyMuPDF の内蔵フォント（ASCII のみ）を使用。

---

### ステップ2: ファイルの確認

カレントディレクトリの PDF を `ls` で列挙し、ユーザーに使うファイルを選んでもらう。

採点表 `score.csv` の有無を確認する:

- **存在しない場合**: 雛形 `score_template.csv` を `score.csv` としてコピーし、ユーザーに「`score.csv` を生成しました。Name と各問の正誤（1=正解 / それ以外=不正解）を記入してから次へ進んでください」と案内する。

  ```bash
  cp score_template.csv score.csv
  ```

  `score_template.csv` が無ければステップ1のコピーを案内する。

- **存在する場合**: そのまま使う。

> **配点について**: `score.csv` の2行目（`Name` 欄が `Points` の行）に各問の配点を記入する。`grade.py` はこの行を読んで問ごとに加点する（例: `Points,5,5,10,5,5`）。配点行が無い場合は `config.json` の `points_per_question`（既定5点）が全問に適用される。

### ステップ3: 設定ファイルの確認

`config.json` が存在するか確認する。

- **存在する場合**: `config.json` の `pages_per_student` と `questions` の件数を読んで「前回の設定（X問、1人Yページ）を使いますか？それとも座標を取り直しますか？」と聞く。
- **存在しない場合**: 新規設定として次のステップへ。

### ステップ4: 座標設定（新規または取り直しの場合のみ）

1人あたりの答案ページ数をユーザーに聞いてから、以下を実行する:

```
uv run --isolated setup_coords.py --pdf <PDFファイル> --pages <ページ数>
```

問題数は `score.csv` の `Q1`,`Q2`,... 列から自動で取得される（`--csv` で別ファイルを指定可）。CSV が無い・Q列が見つからない場合は GUI のダイアログで問題数を尋ねる。明示したいときは `--questions <数>` を付ける。

GUI が開くのでユーザーに操作してもらう。「完了しました」と言われたら次へ。

### ステップ5: 採点実行

```
uv run --isolated grade.py --pdf <PDFファイル> --csv score.csv
```

### ステップ6: 完了報告

出力された人数・平均点を伝え、`output/graded.pdf` と `score_graded.csv` を確認するよう案内する。元の `score.csv` は編集されず、採点CSVには最右列 `Total` が追加される。
