"""Inspect the Facebook dataset CSV — Phase 1 helper.

Usage:
    python scripts/inspect_dataset.py dataset_facebook.csv
"""
import sys
import pandas as pd

def inspect(path):
    print(f"\n📂 File: {path}\n")
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")

    print(f"📊 Total rows (incl. multiline expanded): {len(df)}")
    print(f"📊 Total columns: {len(df.columns)}\n")

    print("📋 Columns:")
    for i, c in enumerate(df.columns, 1):
        print(f"  {i:>3}. {c}")

    print("\n🔎 Null/empty per column (top 20):")
    empty = (df == "").sum()
    empty = empty[empty > 0].sort_values(ascending=False).head(20)
    for col, n in empty.items():
        print(f"  {col}: {n}")

    print("\n🔍 Duplicate rows:", df.duplicated().sum())

    if "id" in df.columns:
        print("🔍 Duplicate 'id':", df["id"].duplicated().sum())
    if "text" in df.columns:
        texts = df["text"][df["text"] != ""]
        print(f"\n💬 Records with non-empty 'text': {len(texts)}")
        print(f"💬 Records with empty 'text': {len(df) - len(texts)}")
        if len(texts):
            print("\n📝 Sample texts:")
            for t in texts.head(3):
                print(f"  - {t[:120]}")

    if "date" in df.columns:
        try:
            dates = pd.to_datetime(df["date"], errors="coerce")
            print(f"\n📅 Date range: {dates.min()} → {dates.max()}")
        except Exception as e:
            print(f"⚠️ Date parse warning: {e}")

    print("\n✅ Inspection complete.\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_dataset.py <csv>")
        sys.exit(1)
    inspect(sys.argv[1])