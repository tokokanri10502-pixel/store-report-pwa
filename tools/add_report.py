#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================
  店舗視察レポート追加スクリプト
  使い方:
    python tools/add_report.py <PDFファイルパス>
  例:
    python tools/add_report.py "C:/Users/xxx/Downloads/202603出張報告書.pdf"
=====================================================
"""

import sys
import os
import json
import re
import shutil
from pathlib import Path
from datetime import datetime

# ─── PyPDFium2 check ───────────────────────────────
try:
    import pypdfium2 as pdfium
except ImportError:
    print("エラー: pypdfium2 がインストールされていません。")
    print("インストール方法: pip install pypdfium2")
    sys.exit(1)

# ─── Paths ────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_JS      = PROJECT_ROOT / "data" / "reports_data.js"
DATA_JSON    = PROJECT_ROOT / "data" / "reports.json"
REPORTS_DIR  = PROJECT_ROOT / "reports"

def load_reports():
    """reports.json を読み込む（なければ空リスト）"""
    if DATA_JSON.exists():
        with open(DATA_JSON, encoding="utf-8") as f:
            return json.load(f)
    # reports_data.js から抽出を試みる
    if DATA_JS.exists():
        text = DATA_JS.read_text(encoding="utf-8")
        m = re.search(r'window\.REPORTS_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except:
                pass
    return []

def save_reports(reports):
    """reports.json と reports_data.js を両方更新する"""
    # reports.json
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

    # reports_data.js（index.html が読み込む）
    js_content = (
        "// ============================================================\n"
        "// 報告書データ - add_report.py により自動生成\n"
        "// 最終更新: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n"
        "// ============================================================\n"
        "window.REPORTS_DATA = "
        + json.dumps(reports, ensure_ascii=False, indent=2)
        + ";\n"
    )
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

def extract_pages(pdf_path, out_dir, scale=2.0, quality=82):
    """PDF を 1ページずつ JPG に変換"""
    pdf = pdfium.PdfDocument(str(pdf_path))
    n = len(pdf)
    print(f"  → {n} ページ検出")
    for i in range(n):
        page = pdf[i]
        bm   = page.render(scale=scale)
        img  = bm.to_pil()
        out  = out_dir / f"page_{i+1}.jpg"
        img.save(str(out), "JPEG", quality=quality)
        print(f"  → page_{i+1}.jpg を保存（{img.width}×{img.height}）")
    pdf.close()
    return n

def ask(prompt, default=None):
    """入力受付（デフォルト付き）"""
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()

def ask_stores(report_id, n_pages):
    """店舗情報を対話的に入力"""
    stores = []
    print(f"\n  ── 店舗情報の入力（{n_pages-1} 店舗分のページがあります）──")
    print("  ページ 1 はサマリーページ、2ページ目以降が各店舗です。")

    store_count = int(ask("  店舗数", str(n_pages - 1)))
    for i in range(store_count):
        print(f"\n  ── 店舗 {i+1} / {store_count} ──")
        name    = ask("  店舗名（例: イオン広島店）")
        address = ask("  住所（例: 広島県広島市西区）")
        time_   = ask("  視察時間（例: 10:00〜11:00）")
        note    = ask("  備考（オープン日など、不要なら空欄）", "")
        imp     = ask("  印象・メモ（1〜2行）")
        page    = ask(f"  対応PDFページ番号（通常 {i+2}）", str(i+2))
        tags_raw = ask("  タグ（カンマ区切り、例: 節分,POP,新店）", "")
        tags    = [t.strip() for t in tags_raw.split(",") if t.strip()]
        safe_id = re.sub(r'[^a-z0-9\-]', '', name.lower().replace(' ', '-'))[:20] or f"store{i+1}"

        stores.append({
            "id":       safe_id,
            "name":     name,
            "address":  address,
            "mapsUrl":  f"https://maps.google.com/?q={name}+{address}",
            "time":     time_,
            "note":     note,
            "impression": imp,
            "page":     int(page),
            "tags":     tags
        })
    return stores

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("使い方: python tools/add_report.py <PDFファイルパス>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"エラー: ファイルが見つかりません: {pdf_path}")
        sys.exit(1)

    print("=" * 55)
    print("  店舗視察レポート 追加ツール")
    print("=" * 55)
    print(f"\n  PDF: {pdf_path.name}\n")

    # ── 基本情報入力 ─────────────────────────────────
    print("── 報告書の基本情報を入力してください ──\n")
    date_str   = ask("  視察日（例: 2026-03-15）")
    author     = ask("  作成者名（例: 山田太郎）")
    dept       = ask("  部署名（例: 企画課）")
    area       = ask("  エリア・タイトル（例: 関東（千葉・東京）出張報告書）")
    date_label = ask("  表示用の日付（例: 2026年3月15日）", date_str)
    purpose_raw= ask("  視察目的（カンマ区切り、例: 節分売り場の視察,カタログ入手）")
    purpose    = [p.strip() for p in purpose_raw.split(",") if p.strip()]
    impression = ask("  所感・まとめ（1〜3行）")
    tags_raw   = ask("  報告書タグ（カンマ区切り、例: 節分,POP,バレンタイン）", "")
    tags       = [t.strip() for t in tags_raw.split(",") if t.strip()]

    # ── ID 生成 ──────────────────────────────────────
    ym = re.sub(r'\D', '', date_str)[:6]
    safe_author = re.sub(r'[^\u3040-\u30ff\u4e00-\u9fff\w]', '', author)[:6]
    suggested_id = f"{ym}-{safe_author}"
    report_id = ask(f"  報告書ID（ファイル名に使用）", suggested_id)
    report_id = re.sub(r'[^a-zA-Z0-9\u3040-\u30ff\u4e00-\u9fff\-]', '', report_id)

    # ── 出力フォルダ ─────────────────────────────────
    out_dir = REPORTS_DIR / report_id
    if out_dir.exists():
        overwrite = ask(f"\n  警告: {out_dir} は既に存在します。上書きしますか？(y/n)", "n")
        if overwrite.lower() != 'y':
            print("  中止しました。")
            sys.exit(0)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── PDF → 画像 ────────────────────────────────────
    print(f"\n  ── PDFを画像に変換中 ──")
    n_pages = extract_pages(pdf_path, out_dir)

    # ── 店舗情報入力 ──────────────────────────────────
    stores = ask_stores(report_id, n_pages)

    # ── データ更新 ────────────────────────────────────
    new_report = {
        "id":          report_id,
        "title":       area,
        "date":        date_str,
        "dateLabel":   date_label,
        "author":      author,
        "department":  dept,
        "area":        area,
        "summaryPage": 1,
        "purpose":     purpose,
        "impression":  impression,
        "tags":        tags,
        "stores":      stores
    }

    reports = load_reports()
    # 同じ ID があれば更新、なければ先頭に追加（日付降順を維持）
    idx = next((i for i, r in enumerate(reports) if r["id"] == report_id), None)
    if idx is not None:
        reports[idx] = new_report
        print(f"\n  既存レポート '{report_id}' を更新しました。")
    else:
        reports.insert(0, new_report)
        print(f"\n  新しいレポート '{report_id}' を追加しました。")

    # 日付降順ソート
    reports.sort(key=lambda r: r["date"], reverse=True)
    save_reports(reports)

    print("\n" + "=" * 55)
    print(f"  ✅ 完了！")
    print(f"  画像フォルダ : reports/{report_id}/")
    print(f"  データファイル: data/reports_data.js を更新")
    print(f"  合計 {len(reports)} 件の報告書が登録されています。")
    print("=" * 55)
    print("\n  次のステップ:")
    print("  1. index.html をブラウザで開いて確認")
    print("  2. GitHub にプッシュして Netlify に反映")
    print("=" * 55)

if __name__ == "__main__":
    main()
