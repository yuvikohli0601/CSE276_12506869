"""
Standalone Model Evaluation & Diagnostic Suite
Course: CSE276 | Problem Statement: SIH25031
Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)

Evaluates the saved production model artifact on the test dataset,
printing formatted precision/recall/F1 metrics and confusion matrix.
"""

import os
import sys
import json
import csv
import argparse
import joblib
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

current_dir = os.path.dirname(os.path.abspath(__file__))
codebase_dir = os.path.abspath(os.path.join(current_dir, ".."))
if codebase_dir not in sys.path:
    sys.path.insert(0, codebase_dir)

from backend.nlp_stage1 import normalize_text, DEPARTMENTS

def evaluate_artifact(artifact_path: str = None, test_csv: str = None):
    if artifact_path is None:
        artifact_path = os.path.join(codebase_dir, "ml", "artifacts", "civic_classifier.joblib")
    if test_csv is None:
        test_csv = os.path.join(codebase_dir, "data", "civic_complaints_india.csv")
        
    print(f"Loading artifact from: {artifact_path}")
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Model artifact not found at {artifact_path}. Run train_models.py first.")
        
    payload = joblib.load(artifact_path)
    model = payload["model"]
    vectorizer = payload["vectorizer"]
    classes = payload.get("classes", DEPARTMENTS)
    model_name = payload.get("model_name", "Unknown Classifier")
    
    print(f"Model: {model_name} | Author: {payload.get('author', 'Yuvi Kohli')}")
    
    # Load dataset
    texts, true_labels = [], []
    with open(test_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["raw_text"])
            true_labels.append(row["true_department"])
            
    print(f"Evaluating across {len(texts)} complaints...")
    cleaned_texts = [normalize_text(t) for t in texts]
    X_vec = vectorizer.transform(cleaned_texts)
    y_pred = model.predict(X_vec)
    
    acc = accuracy_score(true_labels, y_pred)
    macro_f1 = f1_score(true_labels, y_pred, average="macro")
    weighted_f1 = f1_score(true_labels, y_pred, average="weighted")
    cm = confusion_matrix(true_labels, y_pred, labels=classes)
    
    print("\n" + "=" * 65)
    print(f"EVALUATION RESULTS FOR {model_name.upper()}")
    print("=" * 65)
    print(f"Overall Accuracy:  {acc * 100:.2f}%")
    print(f"Macro F1-Score:    {macro_f1:.4f} (Acceptance Target: >= 0.85)")
    print(f"Weighted F1-Score: {weighted_f1:.4f}")
    print("\nDetailed Per-Class Performance:")
    print(classification_report(true_labels, y_pred, labels=classes))
    
    print("\nConfusion Matrix (Rows: True, Columns: Predicted):")
    header = "       " + " ".join([f"{c[:6]:>7}" for c in classes])
    print(header)
    for i, row in enumerate(cm):
        row_str = f"{classes[i][:6]:<7}" + " ".join([f"{val:>7d}" for val in row])
        print(row_str)
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate CivicPulse Model Artifact")
    parser.add_argument("--model", type=str, default=None, help="Path to .joblib artifact")
    parser.add_argument("--test-csv", type=str, default=None, help="Path to evaluation CSV")
    args = parser.parse_args()
    evaluate_artifact(args.model, args.test_csv)
