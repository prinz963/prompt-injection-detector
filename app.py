from flask import Flask, request, jsonify, render_template_string
import pickle
import time
from rule_based_detector import detect as rule_detect
from transformer_detector import detect as transformer_detect

app = Flask(__name__)

# ── Load ML model once at startup ────────────────────────────────
with open("ml_model.pkl",   "rb") as f: ml_model   = pickle.load(f)
with open("vectorizer.pkl", "rb") as f: vectorizer = pickle.load(f)

# ── Simple HTML UI ───────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Prompt Injection Detector</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px;
               margin: 40px auto; padding: 20px; background: #0f172a; color: #e2e8f0; }
        h1   { color: #38bdf8; }
        textarea { width: 100%; height: 120px; padding: 12px; font-size: 14px;
                   background: #1e293b; color: #e2e8f0; border: 1px solid #334155;
                   border-radius: 8px; resize: vertical; }
        button { margin-top: 10px; padding: 12px 28px; background: #0ea5e9;
                 color: white; border: none; border-radius: 8px;
                 font-size: 15px; cursor: pointer; }
        button:hover { background: #0284c7; }
        #result { margin-top: 24px; padding: 20px; border-radius: 8px;
                  background: #1e293b; display: none; }
        .safe      { border-left: 5px solid #22c55e; }
        .malicious { border-left: 5px solid #ef4444; }
        .verdict   { font-size: 22px; font-weight: bold; margin-bottom: 12px; }
        .row       { display: flex; justify-content: space-between;
                     margin: 6px 0; font-size: 14px; }
        .badge     { padding: 2px 10px; border-radius: 12px; font-size: 12px; }
        .bad  { background: #ef4444; }
        .good { background: #22c55e; }
    </style>
</head>
<body>
    <h1>🛡️ Prompt Injection Detector</h1>
    <p>Enter any prompt below to check if it contains a prompt injection attack.</p>
    <textarea id="prompt" placeholder="Type or paste a prompt here..."></textarea>
    <br>
    <button onclick="analyze()">Analyze Prompt</button>
    <div id="result"></div>

    <script>
    async function analyze() {
        const prompt = document.getElementById("prompt").value.trim();
        if (!prompt) return alert("Please enter a prompt.");

        document.getElementById("result").style.display = "none";
        const btn = document.querySelector("button");
        btn.textContent = "Analyzing...";
        btn.disabled = true;

        const res  = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });
        const data = await res.json();

        const div      = document.getElementById("result");
        const safe     = data.final_verdict === "SAFE";
        div.className  = safe ? "safe" : "malicious";
        div.innerHTML  = `
            <div class="verdict">${safe ? "✅ SAFE" : "🚨 MALICIOUS PROMPT DETECTED"}</div>
            ${!safe ? `<div>Attack type: <b>${data.attack_category}</b></div>` : ""}
            <hr style="border-color:#334155; margin:12px 0">
            <div class="row"><span>Rule-based</span>
                <span class="badge ${data.detectors.rule ? 'bad' : 'good'}">
                    ${data.detectors.rule ? "MALICIOUS" : "SAFE"}</span></div>
            <div class="row"><span>ML Model</span>
                <span class="badge ${data.detectors.ml ? 'bad' : 'good'}">
                    ${data.detectors.ml ? "MALICIOUS" : "SAFE"}</span></div>
            <div class="row"><span>Transformer (${data.detectors.transformer_confidence}%)</span>
                <span class="badge ${data.detectors.transformer ? 'bad' : 'good'}">
                    ${data.detectors.transformer ? "MALICIOUS" : "SAFE"}</span></div>
            <hr style="border-color:#334155; margin:12px 0">
            <div class="row"><span>Risk Score</span><b>${data.risk_score}/3 detectors fired</b></div>
            <div class="row"><span>Response time</span><b>${data.response_time_ms}ms</b></div>
        `;
        div.style.display = "block";
        btn.textContent   = "Analyze Prompt";
        btn.disabled      = false;
    }
    </script>
</body>
</html>
"""

# ── Routes ───────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/analyze", methods=["POST"])
def analyze():
    start = time.time()
    data  = request.get_json()

    if not data or "prompt" not in data:
        return jsonify({"error": "Missing 'prompt' field"}), 400

    prompt = data["prompt"].strip()
    if not prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # Run all 3 detectors
    rule  = rule_detect(prompt)
    vec   = vectorizer.transform([prompt])
    ml    = int(ml_model.predict(vec)[0])
    trans = transformer_detect(prompt)

    votes        = [rule["risk_score"], ml, trans["risk_score"]]
    risk_score   = sum(votes)
    is_malicious = risk_score >= 1

    ms = round((time.time() - start) * 1000, 1)

    return jsonify({
        "prompt":         prompt,
        "final_verdict":  "MALICIOUS" if is_malicious else "SAFE",
        "risk_score":     risk_score,
        "attack_category": rule["matched_category"] if rule["risk_score"] else "unknown",
        "detectors": {
            "rule":                    bool(rule["risk_score"]),
            "ml":                      bool(ml),
            "transformer":             bool(trans["risk_score"]),
            "transformer_confidence":  trans["confidence"]
        },
        "response_time_ms": ms
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "detectors": 3})

# ── Start server ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("🛡️  Prompt Injection Detector API starting...")
    print("   Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True)