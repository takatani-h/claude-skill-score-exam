# claude-skill-score-exam

Claude Code 向け採点スキル。試験答案PDFに丸・バツと点数を書き込む。

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/takatani-h/claude-skill-score-exam.git

# スキルファイルを Claude Code のコマンドディレクトリにコピー
cp claude-skill-score-exam/.claude/commands/score-exam.md ~/.claude/commands/
```

## 使い方

採点したいディレクトリ（PDFとCSVが置いてある場所）で Claude Code を起動し、以下を実行:

```
/score-exam
```

初回はスクリプト（`setup_coords.py` / `grade.py`）をカレントディレクトリにコピーするよう案内されます。

## 必要な入力ファイル

| ファイル | 説明 |
|---|---|
| `*.pdf` | 全学生の答案を連結したPDF（1人あたりNページ） |
| `*.csv` | 氏名と各問の正誤フラグ |

### CSVフォーマット

```csv
氏名,Q1,Q2,Q3,Q4,Q5
山田太郎,1,0,1,1,0
鈴木花子,1,1,1,0,1
```

- `1` = 正解 / `0` = 不正解
- 列名は `Q1`, `Q2`, ... （連番）

## 設定（config.json）

座標設定後に生成される `config.json` で動作を調整できます:

| キー | デフォルト | 説明 |
|---|---|---|
| `points_per_question` | `5` | 1問あたりの配点 |
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
├── .claude/
│   └── commands/
│       └── score-exam.md   # Claude Code スキルファイル
├── setup_coords.py         # GUI で正答位置・点数位置を指定するツール
├── grade.py                # 採点・PDF書き込みツール
└── pyproject.toml          # Python 依存関係
```

## 依存ライブラリ

- [PyMuPDF](https://pymupdf.readthedocs.io/) (`pymupdf>=1.24`)
- [Pillow](https://pillow.readthedocs.io/) (`pillow>=10.0`)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)（実行環境）
