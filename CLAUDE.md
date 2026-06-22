# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

Claude Code 向けの採点スキル。複数学生の答案を連結した1つのPDFと、正誤を記した1つのCSVを入力に、各問へ丸（正解）・バツ（不正解）と合計点を書き込んだ採点済みPDFを生成する。中核は2つのPythonスクリプトと、それらを対話的に実行させる Claude Code スキル（`/score-exam`）。

## 開発コマンド

スクリプトは uv で実行する（CLAUDE.md グローバル方針に従い `--isolated` を付ける）:

```bash
# 座標設定（GUI / tkinter）— 問題数は score.csv の Q列から自動取得（取得失敗時はダイアログ）
uv run --isolated setup_coords.py --pdf <PDF> --pages <1人あたりページ数>

# 採点実行 — output/graded.pdf を生成
uv run --isolated grade.py --pdf <PDF> --csv <CSV>
```

テストフレームワークやリンタは未導入。

## アーキテクチャ

3つの構成要素が `config.json` を介して連携する。`config.json` はリポジトリにはコミットされず、`setup_coords.py` が生成し `grade.py` が消費する受け渡しファイル。

1. **`setup_coords.py`** — PDFをページ画像としてレンダリングし（`DISPLAY_SCALE=1.5`）、GUI上のクリックで座標を採取する。問題数は `score.csv`（`--csv`、既定 `score.csv`）のヘッダにある `Q1`,`Q2`,... 列の最大番号を `count_questions_from_csv` で算出する。`--questions` での明示指定が最優先、次にCSV、どちらも無ければダイアログ入力にフォールバック。2フェーズ構成：まず各問の正答位置（`PHASE_QUESTIONS`）、全問終わると点数表示位置（`PHASE_SCORE`）。クリック座標は表示スケールで割ってPDF座標に変換して保存する。`questions`（`id`/`page`/`x`/`y`）と `score_*`、各種描画パラメータを `config.json` へ書き出す。

2. **`grade.py`** — `config.json` の `pages_per_student` 単位でソースPDFを区切り、CSVの各行（学生）に対応するページ群を出力PDFへ複製。各問のフラグ（`"1"`正解/`"0"`不正解、それ以外はスキップ）に応じて `draw_mark` で丸/バツを描き、正解問の配点を合算して `add_score_text` で書き込む。配点は `load_scores` がCSV2行目（氏名欄=`配点`）から問ごとに読む `points` マップを参照し、未掲載の問は `config.json` の `points_per_question` にフォールバック。CSVの学生順とPDFのページ順が一致している前提。

3. **`.claude/commands/score-exam.md`** — `/score-exam` スキル本体。上記2スクリプトのセットアップ→ファイル選択→座標設定→採点実行を対話的に進める手順書。

### 重要な前提・座標系

- **座標系の二重性**: GUIはスケール済みのキャンバス座標（`_cx`/`_cy`、保存時に破棄）、`config.json` に残すのは等倍のPDF座標（`x`/`y`）。両者を混同しないこと。
- **ページ割り当て**: 学生 `idx` のページは `idx * pages_per_student` から始まる連続範囲。問の `page` はこの範囲内の相対インデックス。
- **CSV**: UTF-8 BOM対応（`utf-8-sig`）で読む。氏名列は `氏名`→`name`→自動採番の順にフォールバック。列名は `Q1`,`Q2`,... の連番。2行目の氏名欄が `配点`（または `points`/`点数`）の行は配点行として学生リストから除外される。雛形は `score_template.csv`、実ファイルは `score.csv`。

### 日本語フォント

点数描画はデフォルトでPyMuPDF内蔵フォント（ASCIIのみ）。点数は数値なので通常は問題ないが、日本語を書き込む場合は `config.json` の `font_path` にフォントファイルのパスを設定する（生成後に手動編集）。

## config.json の主なキー

`setup_coords.py` が生成。`points_per_question`(5)、`mark_radius`(12)、`mark_width`(2)、`score_fontsize`(24)、`font_path`(null)、`pages_per_student`、`questions[]`、`score_page`/`score_x`/`score_y`。
