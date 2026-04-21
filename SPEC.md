# store-report-pwa 報告書追加 仕様書

> 今回の作業（2026-04-21）を元に作成。この手順に沿えばスムーズに追加できる。

---

## 1. 事前確認（毎回やること）

```
ls reports/           ← フォルダ一覧
reports.json の ID一覧 ← 重複・抜け漏れチェック
```

確認ポイント：
- `reports/` フォルダがあるのに JSON 未登録のものはないか
- JSON に登録済みだが `reports/` フォルダがないものはないか

---

## 2. PDFを画像に変換する

```python
import pypdfium2 as pdfium
from pathlib import Path

pdf_path = Path("C:/Users/.../報告書.pdf")
out_dir  = Path("reports/仮フォルダ名-temp")
out_dir.mkdir(exist_ok=True)

pdf = pdfium.PdfDocument(str(pdf_path))
for i in range(len(pdf)):
    bm  = pdf[i].render(scale=2.0)
    img = bm.to_pil()
    img.save(str(out_dir / f"page_{i+1}.jpg"), "JPEG", quality=82)
pdf.close()
```

> **必ずこの方法で変換する。** pdfplumber や pdftotext は日本語PDFで文字化けする。

---

## 3. 画像を読んで内容を把握する

page_1.jpg（サマリーページ）から読み取る情報：

| フィールド | 読み取り元 |
|---|---|
| title | 報告書タイトル |
| date | 視察日（YYYY-MM-DD形式） |
| dateLabel | 視察日の表示用文字列 |
| author | 作成者名 |
| department | 部署名 |
| area | 視察エリア |
| purpose | 目的（箇条書き） |
| impression | 所感・まとめ |
| tags | キーワード抽出 |

page_2 以降を読んで「どの型か」を判断する（→ 次節）。

---

## 4. 報告書の型を判断する

### 型A：店舗別型（多店舗出張）
各ページ＝訪問した別々の店舗。住所・地図URLが異なる。

例：関東出張報告書（段野、胡谷、三分一）

```json
"stores": [
  { "name": "イトーヨーカドー松戸店", "address": "千葉県...", "page": 2 },
  { "name": "ロピア松戸店",          "address": "千葉県...", "page": 3 }
]
```

### 型B：ゾーン別型（1店舗を複数ページで詳細報告）
各ページ＝同じ店舗の異なるゾーン（青果・鮮魚・精肉…）。
住所・mapsUrl はすべて同じ店舗のものを使い回す。
`storeCount: 1` を設定して一覧カードの表示を正しくする。

例：ロピア広島パセーラ店 OPEN視察（山口）

```json
"storeCount": 1,
"stores": [
  { "name": "オープン前・共通シーリング", "address": "広島県...", "page": 2 },
  { "name": "青果ゾーン",                "address": "広島県...", "page": 3 }
]
```

### 型C：テーマ別型（多店舗を成果テーマでまとめて報告）
各ページ＝複数店舗をまたいだ「成果・発見」のテーマ。
住所は「関東（茨城・東京）」など大まかなエリア、mapsUrl は空文字。
`storeCount` に実際の訪問店舗数を設定する。

例：関東有力GMS・SM母の日視察（山口、11店舗）

```json
"storeCount": 11,
"stores": [
  { "name": "成果①② 統一カラー訴求・A6仕切り", "address": "関東（茨城・東京）", "mapsUrl": "", "page": 2 },
  { "name": "成果③④ SNS誘導POP・PB強化",       "address": "関東（千葉・東京）", "mapsUrl": "", "page": 3 }
]
```

---

## 5. JSONデータの構造（スキーマ）

```json
{
  "id":          "202604-fujimura",        // YYYYMM-名前（半角英小文字・ハイフン）
  "title":       "報告書タイトル",
  "date":        "2026-04-03",             // 視察開始日（ISO形式）
  "dateLabel":   "2026年4月3日",           // 表示用（〜があってもよい）
  "author":      "藤村 茉侑",
  "department":  "営業課",
  "area":        "広島県広島市",           // 一覧カードの大タイトルになる
  "summaryPage": 1,                        // 常に1
  "storeCount":  1,                        // 省略時は stores.length が使われる
  "purpose":     ["目的1", "目的2"],
  "impression":  "全体の所感（1〜3文）",
  "tags":        ["タグ1", "タグ2"],
  "stores": [
    {
      "id":         "store-unique-id",     // 英小文字・ハイフン・重複不可
      "name":       "店舗名 or ゾーン名",
      "address":    "住所",
      "mapsUrl":    "https://maps.google.com/?q=...",
      "time":       "10:00〜11:30",
      "note":       "OPEN日など補足（不要なら空文字）",
      "impression": "この店舗/ゾーンの印象",
      "page":       2,                     // 対応する画像ページ番号
      "tags":       ["タグ1", "タグ2"]
    }
  ]
}
```

### storeCount の使い分け

| 状況 | storeCount |
|---|---|
| 型A（通常の多店舗） | 省略（自動で stores.length を使用） |
| 型B（1店舗をゾーン別に分割） | `1` を明示 |
| 型C（テーマ別、実際の訪問店舗数と乖離） | 実訪問店舗数を明示 |

---

## 6. ID 命名規則

```
YYYYMM-名前
```

| パターン | 例 |
|---|---|
| 標準 | `202601-kotani` |
| 同じ人が同月に複数 | `202604-yamaguchi`、`202604-yamaguchi2` |
| 複数人の連名 | `202504-sanbuichi`（代表者名） |

> ID はフォルダ名と一致させる（`reports/202601-kotani/`）

---

## 7. 画像ファイルの命名規則

```
reports/
  {id}/
    page_1.jpg   ← サマリーページ（必須）
    page_2.jpg   ← 店舗1 or ゾーン1 or 成果①②
    page_3.jpg   ← 店舗2 or ゾーン2 or 成果③④
    ...
```

- 形式: JPEG、quality=82、scale=2.0（解像度 約1191×1684px）
- 連番は1始まりで途切れなく

---

## 8. データファイルの更新

`reports.json` と `reports_data.js` は**必ず両方**更新する。

```python
import json
from datetime import datetime
from pathlib import Path

DATA_JSON = Path("data/reports.json")
DATA_JS   = Path("data/reports_data.js")

with open(DATA_JSON, encoding="utf-8") as f:
    reports = json.load(f)

# 既存IDなら更新、新規なら先頭に追加
idx = next((i for i, r in enumerate(reports) if r["id"] == new_entry["id"]), None)
if idx is not None:
    reports[idx] = new_entry
else:
    reports.insert(0, new_entry)

# 日付降順を維持
reports.sort(key=lambda r: r["date"], reverse=True)

# JSON保存
with open(DATA_JSON, "w", encoding="utf-8") as f:
    json.dump(reports, f, ensure_ascii=False, indent=2)

# JS保存（index.html が読み込む）
js = (
    "// 最終更新: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n"
    "window.REPORTS_DATA = "
    + json.dumps(reports, ensure_ascii=False, indent=2)
    + ";\n"
)
with open(DATA_JS, "w", encoding="utf-8") as f:
    f.write(js)
```

---

## 9. GitHub への反映

このプロジェクトは**2箇所**ある（要注意）：

| 場所 | 用途 |
|---|---|
| `Desktop/Development/store-report-pwa/` | 作業場所（Claude が編集する） |
| `Documents/GitHub/store-report-pwa/` | GitHub Desktop が見るフォルダ |

作業後は必ず以下をコピーしてからプッシュ：

```bash
SRC="C:/Users/seisaku00/Desktop/Development/store-report-pwa"
DST="C:/Users/seisaku00/Documents/GitHub/store-report-pwa"

cp "$SRC/data/reports.json"    "$DST/data/reports.json"
cp "$SRC/data/reports_data.js" "$DST/data/reports_data.js"
cp "$SRC/index.html"           "$DST/index.html"          # HTML変更時のみ
mkdir -p "$DST/reports/{id}"
cp "$SRC/reports/{id}/"*.jpg   "$DST/reports/{id}/"
```

その後 GitHub Desktop で Commit → Push → Netlify に自動反映。

---

## 10. 確認チェックリスト

- [ ] `reports/{id}/page_1.jpg` ～ `page_N.jpg` が存在する
- [ ] `reports.json` に新しいエントリが追加されている
- [ ] `reports_data.js` も更新されている
- [ ] 一覧カードに正しい店舗数が表示されている（storeCount 確認）
- [ ] `Documents/GitHub/` 側にコピーした
- [ ] GitHub Desktop でコミット・プッシュした
