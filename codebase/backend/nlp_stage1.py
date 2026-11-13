"""
Stage 1: NLP Classification Pipeline, Data Quality Gates & Feature Attribution
Course: CSE276 | Problem Statement: SIH25031
Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)

Implements:
1. Pre-Inference Data Quality Gates (Character length, token count, OOV ratio, duplicate hashing).
2. Domain-aware Text Normalization & Canonical Expansion.
3. Sublinear TF-IDF Feature Extraction (1-2 N-grams) with Zero C-Extension Dependency.
4. Calibrated Multi-Class Probability Inference.
5. Linear Feature Attribution for Exact N-gram Explainability.
"""

import os
import re
import time
import math
import json
import hashlib
from collections import Counter
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

DEPARTMENTS = ["WATER", "ROADS", "ELECTRICAL", "SANITATION", "HEALTH"]

# Common Indian civic abbreviations and canonical mappings
CANONICAL_ABBREVIATIONS = {
    "xmer": "transformer",
    "transfrmr": "transformer",
    "pwr": "power",
    "elec": "electrical",
    "stlight": "streetlight",
    "stlights": "streetlights",
    "drnkng": "drinking",
    "hosp": "hospital",
    "govt": "government",
    "sch": "school",
    "rd": "road",
    "pothols": "potholes",
    "garbag": "garbage",
    "kachra": "garbage",
    "nalla": "nallah",
    "paani": "water",
    "pani": "water",
    "bijli": "electricity",
    "sewr": "sewage",
    "swr": "sewage"
}

def normalize_text(text: str, apply_canonical: bool = True) -> str:
    """Cleans, lowercases, and canonicalizes civic complaint text."""
    if not isinstance(text, str):
        return ""
    # Lowercase & trim
    cleaned = text.lower().strip()
    # Normalize excessive punctuation & whitespace
    cleaned = re.sub(r"[^\w\s\-/]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    if apply_canonical:
        tokens = cleaned.split()
        expanded_tokens = [CANONICAL_ABBREVIATIONS.get(t, t) for t in tokens]
        cleaned = " ".join(expanded_tokens)
        
    return cleaned

def compute_text_hash(normalized_text: str, ward: str = "") -> str:
    """Generates a SHA-256 hash for deduplication within an active ward window."""
    content = f"{ward.lower().strip()}|{normalized_text.lower().strip()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def check_data_quality(
    raw_text: str,
    ward: str = "",
    recent_hashes: Optional[set] = None,
    vocabulary: Optional[set] = None
) -> Tuple[bool, str, str]:
    """
    Automated Pre-Inference Data Quality Gate:
    1. Minimum character length (>= 12 chars) & valid token count (>= 3 alphabetic tokens).
    2. Out-of-Vocabulary (OOV) / Gibberish detection (>80% OOV words).
    3. Duplicate submission detection via ward-scoped hash.
    
    Returns: (passed: bool, status_code: str, diagnostic_message: str)
    """
    if not raw_text or len(raw_text.strip()) < 12:
        return False, "DQ_FAIL_SHORT", "Complaint too short (<12 chars). Insufficient semantic context."
        
    normalized = normalize_text(raw_text)
    alpha_tokens = [t for t in normalized.split() if t.isalpha() and len(t) > 1]
    
    if len(alpha_tokens) < 3:
        return False, "DQ_FAIL_MIN_TOKENS", f"Only {len(alpha_tokens)} valid word tokens found (minimum 3 required)."
        
    # Gibberish / Repetitive Character Check
    if re.search(r"(.)\1{4,}", raw_text.lower()):
        return False, "DQ_FAIL_GIBBERISH", "Repetitive character pattern detected (likely spam/gibberish)."
        
    # Duplicate Hash Check
    if recent_hashes is not None and ward:
        complaint_hash = compute_text_hash(normalized, ward)
        if complaint_hash in recent_hashes:
            return False, "DQ_FAIL_DUPLICATE", "Duplicate grievance detected in this ward within active submission window."
            
    # OOV / Gibberish Ratio Check against trained vocabulary
    if vocabulary is not None and len(alpha_tokens) > 0:
        oov_count = sum(1 for t in alpha_tokens if t not in vocabulary)
        oov_ratio = oov_count / len(alpha_tokens)
        if oov_ratio > 0.80:
            return False, "DQ_FAIL_OOV", f"High Out-of-Vocabulary ratio ({oov_ratio*100:.1f}%). Input contains excessive unrecognized terms."
            
    return True, "DQ_PASS", "Complaint passed all data quality criteria."

def calculate_shannon_entropy(probabilities: np.ndarray) -> float:
    """
    Calculates normalized Shannon Entropy H(P) over K=5 departments:
    H(P) = - sum(p_i * log5(p_i))
    Yields 0.0 for deterministic certainty, 1.0 for maximal uncertainty.
    """
    probs = np.clip(probabilities, 1e-12, 1.0)
    probs = probs / np.sum(probs)
    k = len(probs)
    if k <= 1:
        return 0.0
    entropy = -np.sum(probs * (np.log(probs) / np.log(k)))
    return float(np.clip(entropy, 0.0, 1.0))

class PureNumpyTFIDFClassifier:
    """
    Mathematically exact TF-IDF + Multinomial Naive Bayes / Softmax Classifier in pure NumPy.
    Runs identically to Scikit-Learn without requiring C-extensions or external pickling.
    Eliminates all AppLocker / Smart App Control policy blocks while maintaining 100% transparency.
    """
    def __init__(self, weights_dict: dict):
        self.classes = weights_dict.get("classes", DEPARTMENTS)
        self.vocabulary = weights_dict["vocabulary"]
        self.idf = np.array(weights_dict["idf"], dtype=np.float64)
        self.feature_log_prob = np.array(weights_dict["feature_log_prob"], dtype=np.float64)
        self.class_log_prior = np.array(weights_dict["class_log_prior"], dtype=np.float64)
        self.sublinear_tf = weights_dict.get("sublinear_tf", True)
        self.vocab_size = len(self.vocabulary)
        self.idx_to_token = {idx: token for token, idx in self.vocabulary.items()}

    def transform(self, normalized_text: str) -> np.ndarray:
        tokens = re.findall(r"(?u)\b\w+\b", normalized_text.lower())
        ngrams = list(tokens)
        for i in range(len(tokens) - 1):
            ngrams.append(tokens[i] + " " + tokens[i+1])

        v = np.zeros(self.vocab_size, dtype=np.float64)
        counts = Counter(ngrams)
        for term, count in counts.items():
            if term in self.vocabulary:
                idx = self.vocabulary[term]
                tf = (1.0 + math.log(count)) if self.sublinear_tf else float(count)
                v[idx] = tf * self.idf[idx]

        norm = np.linalg.norm(v)
        if norm > 0:
            v = v / norm
        return v

    def predict_proba(self, v: np.ndarray) -> np.ndarray:
        # Logits: class_log_prior + feature_log_prob @ v
        logits = self.class_log_prior + np.dot(self.feature_log_prob, v)
        # Numerically stable softmax
        z = logits - np.max(logits)
        exp_z = np.exp(z)
        return exp_z / np.sum(exp_z)

    def explain(self, v: np.ndarray, predicted_dept: str, top_k: int = 5) -> List[Dict[str, Any]]:
        pred_idx = self.classes.index(predicted_dept) if predicted_dept in self.classes else 0
        active_indices = np.nonzero(v)[0]
        attributions = []
        for idx in active_indices:
            token = self.idx_to_token.get(idx, "")
            weight = float(v[idx] * self.feature_log_prob[pred_idx, idx])
            attributions.append({"token": token, "weight": round(weight, 4)})
        attributions.sort(key=lambda x: x["weight"], reverse=True)
        return attributions[:top_k]

class CalibratedSoftmaxClassifier:
    """
    Mathematically transparent Multi-Class Softmax Classifier in pure NumPy.
    Trained via Gradient Descent with Cross-Entropy Loss & L2 Regularization.
    """
    def __init__(self, learning_rate: float = 0.1, max_iter: int = 300, l2_reg: float = 1e-4, random_state: int = 42):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.l2_reg = l2_reg
        self.random_state = random_state
        self.classes_: np.ndarray = np.array([])
        self.coef_: Optional[np.ndarray] = None
        self.intercept_: Optional[np.ndarray] = None
        
    def _softmax(self, z: np.ndarray) -> np.ndarray:
        z_shifted = z - np.max(z, axis=1, keepdims=True)
        exp_z = np.exp(z_shifted)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)
        
    def fit(self, X, y):
        np.random.seed(self.random_state)
        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_samples, n_features = X.shape
        
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}
        Y = np.zeros((n_samples, n_classes), dtype=np.float64)
        for i, val in enumerate(y):
            Y[i, class_to_idx[val]] = 1.0
            
        class_counts = np.sum(Y, axis=0)
        class_weights = n_samples / (n_classes * class_counts)
        sample_weights = np.sum(Y * class_weights, axis=1, keepdims=True)
        
        limit = np.sqrt(6.0 / (n_features + n_classes))
        self.coef_ = np.random.uniform(-limit, limit, (n_classes, n_features)).astype(np.float64)
        self.intercept_ = np.zeros(n_classes, dtype=np.float64)
        
        is_sparse = hasattr(X, "toarray")
        
        for iteration in range(self.max_iter):
            if is_sparse:
                Z = X.dot(self.coef_.T) + self.intercept_
            else:
                Z = np.dot(X, self.coef_.T) + self.intercept_
                
            P = self._softmax(Z)
            diff = (P - Y) * sample_weights
            
            if is_sparse:
                grad_W = (np.asarray(X.T.dot(diff)).T / n_samples) + (self.l2_reg * self.coef_)
            else:
                grad_W = (np.dot(diff.T, X) / n_samples) + (self.l2_reg * self.coef_)
                
            grad_b = np.mean(diff, axis=0)
            self.coef_ -= self.learning_rate * grad_W
            self.intercept_ -= self.learning_rate * grad_b
            
        return self
        
    def predict_proba(self, X) -> np.ndarray:
        is_sparse = hasattr(X, "toarray")
        if is_sparse:
            Z = X.dot(self.coef_.T) + self.intercept_
        else:
            Z = np.dot(X, self.coef_.T) + self.intercept_
        return self._softmax(Z)
        
    def predict(self, X) -> np.ndarray:
        proba = self.predict_proba(X)
        indices = np.argmax(proba, axis=1)
        return self.classes_[indices]

class CivicNLPPipeline:
    """
    Stage 1 Core Inference Engine:
    Supports both standalone Pure NumPy weights loading (immune to AppLocker blocks)
    and Scikit-Learn joblib loading.
    """
    def __init__(self, model_artifact_path: Optional[str] = None):
        self.model_path = model_artifact_path
        self.pure_engine: Optional[PureNumpyTFIDFClassifier] = None
        self.model = None
        self.vectorizer = None
        self.classes: List[str] = DEPARTMENTS
        self.vocabulary_set: set = set()
        self.recent_submission_hashes: set = set()
        
        if self.model_path:
            self.load_model(self.model_path)
            
    def load_model(self, path: str):
        """Loads model from weights JSON or joblib artifact."""
        # 1. Check for weights JSON (Zero C-extension dependency)
        weights_path = path.replace(".joblib", "_weights.json")
        if not os.path.exists(weights_path):
            weights_path = os.path.join(os.path.dirname(path), "civic_classifier_weights.json")

        if os.path.exists(weights_path):
            try:
                with open(weights_path, "r", encoding="utf-8") as f:
                    weights = json.load(f)
                self.pure_engine = PureNumpyTFIDFClassifier(weights)
                self.classes = self.pure_engine.classes
                self.vocabulary_set = set(self.pure_engine.vocabulary.keys())
                self.model = self.pure_engine
                return
            except Exception as e:
                print(f"[WARN] Failed loading weights JSON: {e}")

        # 2. Fallback to joblib unpickling
        if os.path.exists(path):
            try:
                import joblib
                artifact = joblib.load(path)
                if isinstance(artifact, dict):
                    self.vectorizer = artifact.get("vectorizer")
                    self.model = artifact.get("model")
                    self.classes = artifact.get("classes", DEPARTMENTS)
                else:
                    self.model = artifact
                if self.vectorizer is not None and hasattr(self.vectorizer, "vocabulary_"):
                    self.vocabulary_set = set(self.vectorizer.vocabulary_.keys())
            except Exception as e:
                print(f"[WARN] Joblib load encountered environment policy: {e}")

    def explain_prediction(self, raw_text: str, predicted_dept: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Calculates exact linear token attribution scores."""
        if self.pure_engine is not None:
            normalized = normalize_text(raw_text)
            v = self.pure_engine.transform(normalized)
            return self.pure_engine.explain(v, predicted_dept, top_k=top_k)

        if self.model is None or self.vectorizer is None:
            return []
            
        normalized = normalize_text(raw_text)
        tfidf_vec = self.vectorizer.transform([normalized])
        feature_names = self.vectorizer.get_feature_names_out()
        pred_idx = list(self.classes).index(predicted_dept) if predicted_dept in self.classes else 0
        
        if hasattr(self.model, "coef_"):
            weights = self.model.coef_[pred_idx]
        elif hasattr(self.model, "feature_log_prob_"):
            weights = self.model.feature_log_prob_[pred_idx]
        else:
            return []
            
        cx = tfidf_vec.tocoo()
        attributions = []
        for col, val in zip(cx.col, cx.data):
            token = feature_names[col]
            attr_score = float(val * weights[col])
            attributions.append({"token": token, "weight": round(attr_score, 4)})
            
        attributions.sort(key=lambda x: x["weight"], reverse=True)
        return attributions[:top_k]

    def predict(
        self,
        raw_text: str,
        ward_location: str = "",
        check_duplicate: bool = False,
        register_hash: bool = False
    ) -> Dict[str, Any]:
        """
        Executes complete Stage 1 Pipeline on a civic grievance:
        1. Pre-inference data quality gate.
        2. TF-IDF vectorization.
        3. Calibrated probability prediction.
        4. Confidence, margin, and Shannon entropy metrics.
        5. Token attribution explainability.
        """
        start_time = time.perf_counter()
        
        # 1. Run Data Quality Gate
        dq_pass, dq_status, dq_msg = check_data_quality(
            raw_text=raw_text,
            ward=ward_location,
            recent_hashes=self.recent_submission_hashes if check_duplicate else None,
            vocabulary=self.vocabulary_set if self.vocabulary_set else None
        )
        
        normalized = normalize_text(raw_text)
        
        # If input is too short or gibberish, semantic features cannot be reliably extracted
        if not dq_pass and dq_status in ("DQ_FAIL_SHORT", "DQ_FAIL_MIN_TOKENS", "DQ_FAIL_GIBBERISH"):
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            uniform_prob = 1.0 / len(self.classes)
            return {
                "predicted_department": "UNCLASSIFIED",
                "department_probabilities": {d: round(uniform_prob, 4) for d in self.classes},
                "top1_confidence": round(uniform_prob, 4),
                "top2_margin": 0.0,
                "shannon_entropy": 1.0,
                "data_quality_status": dq_status,
                "data_quality_message": dq_msg,
                "token_attributions": [],
                "inference_latency_ms": round(latency_ms, 2),
                "is_disqualified": True
            }
            
        # 2. Vectorization & Inference on valid text (or duplicate check)
        if self.pure_engine is not None:
            v = self.pure_engine.transform(normalized)
            probs = self.pure_engine.predict_proba(v)
            class_prob_pairs = list(zip(self.classes, probs))
            class_prob_pairs.sort(key=lambda x: x[1], reverse=True)
            
            top1_dept, top1_conf = class_prob_pairs[0]
            top2_dept, top2_conf = class_prob_pairs[1]
            top2_margin = float(top1_conf - top2_conf)
            entropy = calculate_shannon_entropy(probs)
            attributions = self.pure_engine.explain(v, top1_dept, top_k=5)
            prob_dict = {dept: round(float(p), 4) for dept, p in zip(self.classes, probs)}
        elif self.vectorizer is not None and self.model is not None:
            X_vec = self.vectorizer.transform([normalized])
            probs = self.model.predict_proba(X_vec)[0]
            class_prob_pairs = list(zip(self.classes, probs))
            class_prob_pairs.sort(key=lambda x: x[1], reverse=True)
            
            top1_dept, top1_conf = class_prob_pairs[0]
            top2_dept, top2_conf = class_prob_pairs[1]
            top2_margin = float(top1_conf - top2_conf)
            entropy = calculate_shannon_entropy(probs)
            attributions = self.explain_prediction(raw_text, top1_dept, top_k=5)
            prob_dict = {dept: round(float(p), 4) for dept, p in zip(self.classes, probs)}
        else:
            top1_dept = "UNCLASSIFIED"
            prob_dict = {d: round(1.0 / len(self.classes), 4) for d in self.classes}
            top1_conf = round(1.0 / len(self.classes), 4)
            top2_margin = 0.0
            entropy = 1.0
            attributions = []
            
        if register_hash and dq_pass:
            comp_hash = compute_text_hash(normalized, ward_location)
            self.recent_submission_hashes.add(comp_hash)
            
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        return {
            "predicted_department": top1_dept,
            "department_probabilities": prob_dict,
            "top1_confidence": round(float(top1_conf), 4),
            "top2_margin": round(float(top2_margin), 4),
            "shannon_entropy": round(float(entropy), 4),
            "data_quality_status": dq_status,
            "data_quality_message": dq_msg,
            "token_attributions": attributions,
            "inference_latency_ms": round(latency_ms, 2),
            "is_disqualified": not dq_pass
        }
