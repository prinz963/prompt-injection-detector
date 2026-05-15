import pandas as pd

# ── 1. Load the dataset ──────────────────────────────────────────
df = pd.read_csv("dataset.csv")
print("✅ Dataset loaded!")
print(f"   Total rows: {len(df)}\n")

# ── 2. Check for missing values ──────────────────────────────────
missing = df.isnull().sum()
if missing.any():
    print("⚠️  Missing values found:")
    print(missing)
else:
    print("✅ No missing values found!\n")

# ── 3. Show label distribution ───────────────────────────────────
print("📊 Label distribution:")
counts = df["label"].value_counts()
print(f"   Safe prompts (0):      {counts.get(0, 0)}")
print(f"   Malicious prompts (1): {counts.get(1, 0)}\n")

# ── 4. Show category breakdown ───────────────────────────────────
print("📂 Category breakdown:")
for cat, count in df["category"].value_counts().items():
    print(f"   {cat}: {count}")

# ── 5. Preview first 5 rows ──────────────────────────────────────
print("\n🔍 Sample prompts:")
print(df[["prompt", "label", "category"]].head())

# ── 6. Save a clean copy ─────────────────────────────────────────
df.to_csv("dataset_clean.csv", index=False)
print("\n✅ Clean dataset saved as dataset_clean.csv")