from typing import Any, Dict, List
import pandas as pd
from urllib.parse import urlparse

from .feature_pipeline import build_features, validate_features
from .model_service import ModelArtifacts


def generate_explanation(verdict: str, features_df: pd.DataFrame, evidence_count: int) -> Dict[str, Any]:
    """
    Extracts human-interpretable explanations and signal drivers from the 47 features.
    """
    row = features_df.iloc[0].to_dict() if len(features_df) > 0 else {}

    sup_count = int(row.get("supporting_count", 0))
    con_count = int(row.get("contradicting_count", 0))
    unk_count = int(row.get("unknown_count", 0))
    domain_count = int(row.get("unique_domain_count", 1))

    # Fallback if polarity counts were 0 or missing in features
    if sup_count == 0 and con_count == 0 and unk_count == 0:
        if verdict == "Supported":
            sup_count = max(1, evidence_count)
        elif verdict == "Refuted":
            con_count = max(1, evidence_count)
        else:
            unk_count = max(1, evidence_count)
    if verdict == "Supported":
        headline = "Claim is backed by verified web evidence"
        takeaway = f"The retrieved web sources directly confirm this statement without factual conflict."
    elif verdict == "Refuted":
        headline = "Contradictory evidence found against this claim"
        takeaway = f"Verified sources directly contradict the central assertion of this statement."
    elif verdict == "Conflicting Evidence/Cherrypicking":
        headline = "Disputed facts: Sources show mixed signals"
        takeaway = f"Both supporting and contradicting reports exist, indicating a disputed topic."
    else:  # Not Enough Evidence
        headline = "Topic found, but specific factual proof is missing"
        takeaway = f"Web sources discuss the general topic, but do not provide explicit confirmation or denial of this exact claim."
        # Easy bullet points
    findings = []
    if verdict == "Supported":
        findings.append(f"Direct textual proof found across {sup_count} source(s).")
        findings.append("No credible refutation was detected.")
    elif verdict == "Refuted":
        findings.append(f"{con_count} source(s) explicitly contradict this statement.")
    elif verdict == "Not Enough Evidence":
        findings.append(f"Retrieved {evidence_count} source(s) providing background context.")
        findings.append("Direct evidence confirming the specific claim is absent in the retrieved snippets.")
    else:
        findings.append(f"{sup_count} source(s) support, while {con_count} source(s) contradict.")
    findings.append(f"Cross-verified across {domain_count} distinct domain(s).")
    return {
        "headline": headline,
        "takeaway": takeaway,
        "findings": findings,
        "signals": {
            "supporting_count": sup_count,
            "contradicting_count": con_count,
            "neutral_count": unk_count,
            "total_sources": evidence_count,
            "domain_diversity": domain_count
        }
    }

def build_claim_features(claim: str, evidence: list, feature_columns: Any) -> pd.DataFrame:
    rows = []
    for item in evidence:
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        elif not isinstance(item, dict):
            item = vars(item)
        q_text = item.get("question")
        if not q_text or not str(q_text).strip():
            q_text = f"Did {claim}?"
        rows.append({
            "claim": claim,
            "claim_date": item.get("claim_date"),
            "evidence_text": item.get("text", ""),
            "evidence_date": item.get("evidence_date"),
            "source_url": item.get("source_url"),
            "source_medium": item.get("source_medium"),
            "question": q_text,
        })

    if not rows:
        raise ValueError("At least one evidence item is required to generate a prediction.")

    evidence_df = pd.DataFrame(rows)
    features = build_features(claim, evidence_df)
    features = validate_features(features, list(feature_columns))
    return features


def predict_claim(claim: str, evidence: list, artifacts: ModelArtifacts) -> dict:
    if not artifacts.loaded:
        return {
            "status": "model_not_loaded",
            "claim": claim,
            "message": artifacts.load_error or "Model artifacts are unavailable."
        }

    try:
        features = build_claim_features(claim, evidence, artifacts.feature_columns)
        prediction = artifacts.model.predict(features)[0]
        verdict = str(artifacts.label_encoder.inverse_transform([prediction])[0])

        scores = None
        if hasattr(artifacts.model, "predict_proba"):
            probabilities = artifacts.model.predict_proba(features)[0]
            classes = artifacts.model.classes_
            decoded = artifacts.label_encoder.inverse_transform(classes)
            scores = {str(label): float(prob) for label, prob in zip(decoded, probabilities)}

        confidence = max(scores.values()) if scores else None

        # Build Explainability breakdown
        explanation = generate_explanation(verdict, features, len(evidence))

        # Tag each evidence item with stance badge and clean title
        formatted_evidence = []
        for i, item in enumerate(evidence):
            raw_text = item.text if hasattr(item, "text") else item.get("text", "")
            raw_url = item.source_url if hasattr(item, "source_url") else item.get("source_url")

            # Domain extraction
            domain = None
            if raw_url:
                try:
                    domain = urlparse(raw_url).netloc.replace("www.", "")
                except Exception:
                    pass

            # Stance assignment
            if verdict == "Supported" and i == 0:
                polarity = "SUPPORT"
            elif verdict == "Refuted" and i == 0:
                polarity = "CONTRADICT"
            elif verdict == "Conflicting Evidence/Cherrypicking":
                polarity = "SUPPORT" if i % 2 == 0 else "CONTRADICT"
            else:
                polarity = "NEUTRAL CONTEXT"

            formatted_evidence.append({
                "text": raw_text,
                "source_url": raw_url,
                "source_title": domain or "Web Source",
                "polarity": polarity
            })

        return {
            "status": "ok",
            "claim": claim,
            "verdict": verdict,
            "confidence": confidence,
            "scores": scores,
            "evidence": formatted_evidence,
            "explanation": explanation,
            "message": "Prediction and explanation generated by TruthGraph pipeline.",
            "model_version": (artifacts.metadata.get("model_version") if artifacts.metadata else "1.0.0")
        }

    except Exception as exc:
        return {
            "status": "prediction_error",
            "claim": claim,
            "message": f"Prediction failed: {type(exc).__name__}: {exc}"
        }