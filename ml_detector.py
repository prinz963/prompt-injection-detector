import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import pickle

# ── 1. Load dataset ──────────────────────────────────────────────
df = pd.read_csv("dataset_clean.csv")
X = df["prompt"]
y = df["label"]

# ── 2. Split into train and test sets ───────────────────────────
# 80% training, 20% testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"✅ Data split — Train: {len(X_train)} | Test: {len(X_test)}\n")

# ── 3. Convert text to numbers using TF-IDF ──────────────────────
# TF-IDF turns each prompt into a vector of numbers
# so the ML model can understand it
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=500)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec  = vectorizer.transform(X_test)

# ── 4. Train two models and compare ─────────────────────────────
models = {
    "Naive Bayes":       MultinomialNB(),
    "Logistic Regression": LogisticRegression(max_iter=1000)
}

best_model = None
best_f1    = 0
best_name  = ""

for name, model in models.items():
    model.fit(X_train_vec, y_train)
    preds = model.predict(X_test_vec)

    acc  = accuracy_score(y_test, preds)  * 100
    prec = precision_score(y_test, preds) * 100
    rec  = recall_score(y_test, preds)    * 100
    f1   = f1_score(y_test, preds)        * 100

    print(f"📊 {name}")
    print(f"   Accuracy  : {acc:.1f}%")
    print(f"   Precision : {prec:.1f}%")
    print(f"   Recall    : {rec:.1f}%")
    print(f"   F1 Score  : {f1:.1f}%\n")

    if f1 > best_f1:
        best_f1    = f1
        best_model = model
        best_name  = name

print(f"🏆 Best model: {best_name} (F1: {best_f1:.1f}%)\n")

# ── 5. Detailed report for best model ───────────────────────────
best_preds = best_model.predict(X_test_vec)
print("📋 Detailed classification report:")
print(classification_report(y_test, best_preds,
      target_names=["Safe", "Malicious"]))

# ── 6. Save the model and vectorizer ────────────────────────────
with open("ml_model.pkl", "wb") as f:
    pickle.dump(best_model, f)
with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)
print("✅ Model saved as ml_model.pkl")
print("✅ Vectorizer saved as vectorizer.pkl\n")

# ── 7. Live tester ───────────────────────────────────────────────
def live_test():
    print("🔍 Live Prompt Tester (type 'quit' to exit)")
    print("-" * 50)
    while True:
        prompt = input("\nEnter a prompt: ").strip()
        if prompt.lower() == "quit":
            break
        vec    = vectorizer.transform([prompt])
        pred   = best_model.predict(vec)[0]
        prob   = best_model.predict_proba(vec)[0]
        conf   = max(prob) * 100
        if pred == 1:
            print(f"🚨 MALICIOUS  (confidence: {conf:.1f}%)")
        else:
            print(f"✅ SAFE       (confidence: {conf:.1f}%)")

live_test()