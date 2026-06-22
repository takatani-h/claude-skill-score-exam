# codex-skill-score-exam

Codex 向け採点スキル。試験答案PDFに丸・バツと点数を書き込み、採点CSVを出力する。

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/takatani-h/claude-skill-score-exam.git

# Codex のスキルディレクトリにコピー
mkdir -p ~/.codex/skills
cp -R claude-skill-score-exam/.codex/skills/score-exam ~/.codex/skills/
```

## 使い方

採点したいディレクトリ（PDFとCSVが置いてある場所）で Codex を起動し、以下のように依頼:

```
Use $score-exam to grade this combined exam PDF with score.csv.
```

初回はスクリプト（`setup_coords.py` / `grade.py`）をカレントディレクトリにコピーするよう案内されます。

## 必要な入力ファイル

| ファイル | 説明 |
|---|---|
| `*.pdf` | 全学生の答案を連結したPDF（1人あたりNページ） |
| `score.csv` | 氏名・配点・各問の正誤フラグ |

`score.csv` が無い場合は、スキル実行時に雛形 `score_template.csv` が `score.csv` としてコピーされます。
採点時に元の `score.csv` は編集せず、同じディレクトリに `score_graded.csv` を作成して最右列に `Total` を追記します。
`--csv scores.csv` のように別名を指定した場合は、`scores_graded.csv` が作成されます。

### CSVフォーマット

```csv
Name,Q1,Q2,Q3,Q4,Q5
Points,5,5,10,5,5
Student1,1,0,1,1,0
Student2,1,1,1,0,1
```

- 1行目: ヘッダー。列名は `Q1`, `Q2`, ... （連番）
- 2行目: **配点行**。`Name` 欄を `Points` とし、各問の点数を記入する
- 3行目以降: 各学生。`1` = 正解 / それ以外 = 不正解

配点行を省略した場合は `config.json` の `points_per_question`（既定5点）が全問に適用されます。

## 設定（config.json）

座標設定後に生成される `config.json` で動作を調整できます:

| キー | デフォルト | 説明 |
|---|---|---|
| `points_per_question` | `5` | 1問あたりの既定配点（`score.csv` の配点行が優先） |
| `mark_radius` | `12` | 丸印の半径（pt） |
| `mark_width` | `2` | 線の太さ（pt） |
| `score_fontsize` | `24` | 点数のフォントサイズ |
| `font_path` | `null` | 日本語フォントのパス（省略時はASCIIフォント） |

### 日本語フォントの設定例

```json
{
  "font_path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
}
```

macOS の場合:

```json
{
  "font_path": "/Library/Fonts/Arial Unicode.ttf"
}
```

## ファイル構成

```
.
├── .codex/
│   └── skills/
│       └── score-exam/
│           ├── SKILL.md
│           ├── agents/
│           │   └── openai.yaml
│           ├── assets/
│           │   └── score_template.csv
│           ├── scripts/
│           │   ├── grade.py
│           │   └── setup_coords.py
│           └── pyproject.toml
├── setup_coords.py         # GUI で正答位置・点数位置を指定するツール
├── grade.py                # 採点・PDF書き込みツール
├── score_template.csv      # 採点表 score.csv の雛形
└── pyproject.toml          # Python 依存関係
```

## 依存ライブラリ

- [PyMuPDF](https://pymupdf.readthedocs.io/) (`pymupdf>=1.24`)
- [Pillow](https://pillow.readthedocs.io/) (`pillow>=10.0`)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)（実行環境）
