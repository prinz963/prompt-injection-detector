from transformers import pipeline
import pandas as pd

# ── 1. Load zero-shot classifier ─────────────────────────────────
# This uses a pre-trained model from HuggingFace
# No training needed — it understands language out of the box
print("⏳ Loading transformer model... (first time may take 1-2 mins)")
classifier = pipeline("zero-shot-classification",
                      model="facebook/bart-large-mnli")
print("✅ Model loaded!\n")

# ── 2. Labels we want to classify into ──────────────────────────
LABELS = ["safe prompt", "malicious prompt injection attack"]

# ── 3. Single prompt detector ────────────────────────────────────
def detect(prompt):
    """
    Run a prompt through the transformer classifier.
    Returns label, confidence score, and risk level.
    """
    result    = classifier(prompt, LABELS)
    top_label = result["labels"][0]
    top_score = result["scores"][0] * 100

    is_malicious = top_label == "malicious prompt injection attack"

    return {
        "is_malicious": is_malicious,
        "label":        top_label,
        "confidence":   round(top_score, 1),
        "risk_score":   1 if is_malicious else 0
    }

# ── 4. Evaluate on dataset ───────────────────────────────────────
def evaluate_on_dataset(filepath):
    df      = pd.read_csv(filepath)
    correct = 0
    fp      = 0  # false positives
    fn      = 0  # false negatives

    print(f"{'PROMPT':<55} {'ACTUAL':<10} {'PREDICTED':<10} {'CONF':<8} RESULT")
    print("-" * 100)

    for _, row in df.iterrows():
        result    = detect(row["prompt"])
        predicted = result["risk_score"]
        actual    = row["label"]
        conf      = result["confidence"]

        if predicted == actual:
            correct += 1
            status = "✅"
        elif actual == 0 and predicted == 1:
            fp    += 1
            status = "⚠️ FP"
        else:
            fn    += 1
            status = "❌ FN"

        short = row["prompt"][:52] + "..." if len(row["prompt"]) > 52 else row["prompt"]
        print(f"{short:<55} {actual:<10} {predicted:<10} {conf:<8} {status}")

    total    = len(df)
    accuracy = (correct / total) * 100
    print("\n" + "=" * 100)
    print(f"📊 Transformer Results:")
    print(f"   Total prompts   : {total}")
    print(f"   Correct         : {correct}")
    print(f"   False Positives : {fp}")
    print(f"   False Negatives : {fn}")
    print(f"   Accuracy        : {accuracy:.1f}%\n")

# ── 5. Combined pipeline ─────────────────────────────────────────
# Rule-based + ML + Transformer working together
# If ANY of the 3 detectors flags it → treat as malicious
def combined_detect(prompt):
    import pickle
    from sklearn.feature_extraction.text import TfidfVectorizer
    from rule_based_detector import detect as rule_detect

    # Load saved ML model
    with open("ml_model.pkl",    "rb") as f: ml_model    = pickle.load(f)
    with open("vectorizer.pkl",  "rb") as f: vectorizer  = pickle.load(f)

    rule   = rule_detect(prompt)
    vec    = vectorizer.transform([prompt])
    ml     = ml_model.predict(vec)[0]
    trans  = detect(prompt)

    votes        = [rule["risk_score"], int(ml), trans["risk_score"]]
    final        = 1 if sum(votes) >= 1 else 0  # flag if ANY detector fires
    verdict      = "🚨 MALICIOUS" if final == 1 else "✅ SAFE"

    print(f"\n{'─'*50}")
    print(f"Prompt    : {prompt[:80]}")
    print(f"Rule-based: {'🚨 MALICIOUS' if votes[0] else '✅ SAFE'}")
    print(f"ML model  : {'🚨 MALICIOUS' if votes[1] else '✅ SAFE'}")
    print(f"Transformer: {'🚨 MALICIOUS' if votes[2] else '✅ SAFE'} ({trans['confidence']}%)")
    print(f"{'─'*50}")
    print(f"FINAL VERDICT: {verdict}")

# ── 6. Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 100)
    print("TRANSFORMER-BASED PROMPT INJECTION DETECTOR")
    print("=" * 100 + "\n")

    # Evaluate on dataset
    evaluate_on_dataset("dataset_clean.csv")

    # Live combined pipeline tester
    print("\n🔍 Combined Pipeline Tester (type 'quit' to exit)")
    print("   Uses Rule-based + ML + Transformer together\n")
    while True:
        prompt = input("Enter a prompt: ").strip()
        if prompt.lower() == "quit":
            break
        combined_detect(prompt)