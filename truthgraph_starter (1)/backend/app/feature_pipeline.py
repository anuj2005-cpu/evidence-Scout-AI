import re
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import torch

from sentence_transformers import SentenceTransformer
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)
ARCHIVE_DOMAINS = {
    "web.archive.org",
    "archive.ph",
    "archive.is",
    "archive.today",
    "webcache.googleusercontent.com",
}

BASE_FEATURES = ["evidence_count"]

TEMPORAL_FEATURES = [
    "event_supported_count",
    "after_claim_count",
    "before_or_same_count",
    "temporal_unknown_count",
    "temporal_valid_count",
    "evidence_date_count",
    "referenced_year_count",
    "event_supported_ratio",
    "after_claim_ratio",
    "before_or_same_ratio",
    "temporal_unknown_ratio",
    "temporal_valid_ratio",
]

POLARITY_FEATURES = [
    "supporting_count",
    "contradicting_count",
    "unknown_count",
    "support_ratio",
    "contradict_ratio",
    "unknown_ratio",
    "polarity_margin",
    "polarity_conflict",
    "high_confidence_support",
    "high_confidence_contradict",
]

SOURCE_FEATURES = [
    "unique_source_count",
    "unique_domain_count",
    "source_medium_count",
    "source_diversity_ratio",
    "domain_diversity_ratio",
    "dominant_source_ratio",
]

NLI_FEATURES = [
    "nli_evidence_count",
    "nli_entailment_count",
    "nli_contradiction_count",
    "nli_neutral_count",
    "nli_entailment_mean",
    "nli_contradiction_mean",
    "nli_neutral_mean",
    "nli_max_entailment",
    "nli_max_contradiction",
    "nli_mean_confidence",
    "nli_max_confidence",
    "nli_entailment_ratio",
    "nli_contradiction_ratio",
    "nli_neutral_ratio",
    "nli_polarity_margin",
    "nli_conflict",
    "nli_high_confidence_entail",
    "nli_high_confidence_contradict",
]

EXPECTED_FEATURES = (
    BASE_FEATURES
    + TEMPORAL_FEATURES
    + POLARITY_FEATURES
    + SOURCE_FEATURES
    + NLI_FEATURES
)
_POLARITY_MODEL = None


def parse_date(value):
    if value is None or pd.isna(value) or not str(value).strip():
        return None

    value = str(value).strip()

    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return pd.to_datetime(value, format=fmt)
        except (ValueError, TypeError):
            pass

    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed


def extract_years(text):
    if not text:
        return []

    years = re.findall(r"\b(?:19|20)\d{2}\b", str(text))
    return sorted(set(int(y) for y in years))


def normalize_domain(url):
    if not url:
        return None

    try:
        parsed = urlparse(str(url).strip())
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        if domain == "web.archive.org":
            match = re.search(
                r"/web/\d+(?:[a-z_]+)?/(https?://[^/]+)",
                str(url),
                re.IGNORECASE,
            )

            if match:
                original_domain = urlparse(match.group(1)).netloc.lower()

                if original_domain.startswith("www."):
                    original_domain = original_domain[4:]

                return original_domain or None

        if domain in {"archive.ph", "archive.is", "archive.today"}:
            match = re.search(
                r"(https?://[^/?]+)",
                str(url),
                re.IGNORECASE,
            )

            if match:
                original_domain = urlparse(match.group(1)).netloc.lower()

                if original_domain.startswith("www."):
                    original_domain = original_domain[4:]

                if original_domain and original_domain not in ARCHIVE_DOMAINS:
                    return original_domain

        return domain or None

    except Exception:
        return None


def _get_polarity_model():
    global _POLARITY_MODEL

    if _POLARITY_MODEL is None:
        _POLARITY_MODEL = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    return _POLARITY_MODEL


def _normalize_text(text):
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _clean_question(question):
    question = _normalize_text(question)

    return re.sub(
        r"^(did|does|do|is|are|was|were|has|have|had|can|could|will|would|should)\s+",
        "",
        question,
    ).strip()


def _normalize_boolean_answer(answer):
    answer = _normalize_text(answer)

    if answer in {"yes", "true"}:
        return "YES"

    if answer in {"no", "false"}:
        return "NO"

    return None


def _has_negation(text):
    text = _normalize_text(text)

    patterns = [
        r"\bno\b", r"\bnot\b", r"\bnever\b", r"\bnone\b",
        r"\bnothing\b", r"\bneither\b", r"\bnor\b", r"\bwithout\b",
        r"\bcan't\b", r"\bcannot\b", r"\bdoesn't\b", r"\bdon't\b",
        r"\bdidn't\b", r"\bwasn't\b", r"\bweren't\b",
        r"\bisn't\b", r"\baren't\b", r"\bhasn't\b", r"\bhaven't\b",
        r"\bhadn't\b", r"\bwon't\b", r"\bwouldn't\b",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def _count_polarity_cues(text, cues):
    text = _normalize_text(text)
    return sum(1 for cue in cues if re.search(cue, text))


CONTRADICTION_CUES = [
    r"\bdebunked\b", r"\bdebunk\b", r"\bfalse\b", r"\bfake\b",
    r"\bfabricated\b", r"\bhoax\b", r"\bmisleading\b",
    r"\bincorrect\b", r"\buntrue\b", r"\bnot true\b",
    r"\bno evidence\b", r"\bdenied\b", r"\bdisputed\b",
    r"\brejected\b", r"\brefuted\b", r"\bcontradicted\b",
    r"\bhas no connection\b", r"\bno connection\b",
    r"\bdoes not exist\b", r"\bdid not happen\b",
    r"\bnever happened\b", r"\bnot issued\b",
    r"\bnot associated\b",
    r"\bno such (?:scheme|program|policy|announcement|notification)\b",
]

SUPPORT_CUES = [
    r"\bconfirmed\b",
    r"\bverified\b",
    r"\baccurate\b",
    r"\bcorrect\b",
    r"\bindeed\b",
    r"\brecords show\b",
    r"\bdata show\b",
]
def build_temporal_features(df):
    records = []

    for _, row in df.iterrows():
        claim_date = parse_date(row.get("claim_date"))
        evidence_date = parse_date(row.get("evidence_date"))
        claim = str(row.get("claim", ""))
        evidence_text = str(row.get("evidence_text", ""))

        referenced_years = extract_years(claim)

        is_after = 0
        is_before_or_same = 0
        temporal_unknown = 0
        temporal_valid = 0
        event_supported = 0

        # Match the training scorer:
        # event-year match takes precedence.
        if referenced_years and evidence_date is not None:
            if evidence_date.year in referenced_years:
                event_supported = 1
                temporal_valid = 1
            elif claim_date is not None:
                if evidence_date <= claim_date:
                    is_before_or_same = 1
                    temporal_valid = 1
                else:
                    is_after = 1
            else:
                temporal_unknown = 1

        elif claim_date is not None and evidence_date is not None:
            if evidence_date <= claim_date:
                is_before_or_same = 1
                temporal_valid = 1
            else:
                is_after = 1

        else:
            temporal_unknown = 1

        records.append({
            "is_event_supported": event_supported,
            "is_after_claim": is_after,
            "is_before_or_same": is_before_or_same,
            "temporal_unknown": temporal_unknown,
            "temporal_valid": temporal_valid,
            "has_evidence_date": int(evidence_date is not None),
            "has_referenced_year": int(len(referenced_years) > 0),
        })

    temp = pd.DataFrame(records)
    evidence_count = len(temp)

    if evidence_count == 0:
        evidence_count = 1

    result = {
        "event_supported_count": int(temp["is_event_supported"].sum()),
        "after_claim_count": int(temp["is_after_claim"].sum()),
        "before_or_same_count": int(temp["is_before_or_same"].sum()),
        "temporal_unknown_count": int(temp["temporal_unknown"].sum()),
        "temporal_valid_count": int(temp["temporal_valid"].sum()),
        "evidence_date_count": int(temp["has_evidence_date"].sum()),
        "referenced_year_count": int(temp["has_referenced_year"].sum()),
    }

    result["event_supported_ratio"] = result["event_supported_count"] / evidence_count
    result["after_claim_ratio"] = result["after_claim_count"] / evidence_count
    result["before_or_same_ratio"] = result["before_or_same_count"] / evidence_count
    result["temporal_unknown_ratio"] = result["temporal_unknown_count"] / evidence_count
    result["temporal_valid_ratio"] = result["temporal_valid_count"] / evidence_count

    return result
def build_polarity_features(claim, evidence):
    """Build inference-time polarity features using the same frozen schema.

    Boolean evidence uses the claim/question/answer logic. Non-Boolean
    evidence additionally uses explicit contradiction/support cues before the
    original semantic fallback. Cue rules are applied only when the evidence
    is relevant to the claim/question.
    """
    model = _get_polarity_model()

    questions = evidence.get(
        "question", pd.Series("", index=evidence.index)
    ).fillna("").astype(str).tolist()
    answers = evidence["evidence_text"].fillna("").astype(str).tolist()

    if not answers:
        return {
            "supporting_count": 0,
            "contradicting_count": 0,
            "unknown_count": 0,
            "support_ratio": 0,
            "contradict_ratio": 0,
            "unknown_ratio": 0,
            "polarity_margin": 0,
            "polarity_conflict": 0,
            "high_confidence_support": 0,
            "high_confidence_contradict": 0,
        }

    claim_embedding = model.encode(
        [claim], normalize_embeddings=True
    )[0]
    question_texts = [_clean_question(q) for q in questions]

    q_embeddings = model.encode(
        question_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    a_embeddings = model.encode(
        answers,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    supporting = 0
    contradicting = 0
    unknown = 0
    high_support = 0
    high_contradict = 0

    for i, answer in enumerate(answers):
        q_claim = float(np.dot(q_embeddings[i], claim_embedding))
        c_answer = float(np.dot(claim_embedding, a_embeddings[i]))
        q_answer = float(np.dot(q_embeddings[i], a_embeddings[i]))

        boolean_answer = _normalize_boolean_answer(answer)

        # --------------------------------------------------------
        # Boolean evidence: preserve the tested training logic.
        # --------------------------------------------------------
        if boolean_answer is not None:
            if q_claim >= 0.55:
                same_negation = (
                    _has_negation(claim)
                    == _has_negation(question_texts[i])
                )

                if same_negation:
                    is_support = boolean_answer == "YES"
                else:
                    is_support = boolean_answer == "NO"

                confidence = q_claim

                if is_support:
                    supporting += 1
                    if confidence >= 0.80:
                        high_support += 1
                else:
                    contradicting += 1
                    if confidence >= 0.80:
                        high_contradict += 1
            else:
                unknown += 1
            continue

        # --------------------------------------------------------
        # Non-Boolean evidence must be relevant first.
        # --------------------------------------------------------
        if q_claim < 0.55 or q_answer < 0.50:
            unknown += 1
            continue

        answer_text = _normalize_text(answer)
        contradiction_cues = _count_polarity_cues(
            answer_text, CONTRADICTION_CUES
        )
        support_cues = _count_polarity_cues(
            answer_text, SUPPORT_CUES
        )

        # Explicit debunking/denial is strong evidence against the claim.
        if contradiction_cues > 0:
            confidence = min(
                1.0,
                0.50 * q_claim
                + 0.30 * q_answer
                + 0.20 * min(1.0, 0.60 + 0.10 * contradiction_cues),
            )
            contradicting += 1
            if confidence >= 0.80:
                high_contradict += 1
            continue

        # Explicit verification/confirmation supports the claim.
        if support_cues > 0 and c_answer >= 0.55:
            confidence = min(
                1.0,
                0.45 * q_claim
                + 0.30 * q_answer
                + 0.25 * c_answer,
            )
            supporting += 1
            if confidence >= 0.80:
                high_support += 1
            continue

        # --------------------------------------------------------
        # Original semantic fallback.
        # --------------------------------------------------------
        if c_answer >= 0.72 and q_answer >= 0.72:
            supporting += 1
            confidence = min(c_answer, q_answer)
            if confidence >= 0.80:
                high_support += 1

        elif (
            q_claim >= 0.72
            and q_answer >= 0.72
            and c_answer < 0.72
        ):
            confidence = (
                q_claim + q_answer + (1.0 - c_answer)
            ) / 3.0

            if confidence >= 0.55:
                contradicting += 1
                if confidence >= 0.80:
                    high_contradict += 1
            else:
                unknown += 1

        elif (
            q_claim >= 0.65
            and q_answer >= 0.65
            and c_answer >= 0.65
        ):
            supporting += 1
            confidence = min(q_claim, q_answer, c_answer)
            if confidence >= 0.80:
                high_support += 1
        else:
            unknown += 1

    count = len(answers)

    return {
        "supporting_count": supporting,
        "contradicting_count": contradicting,
        "unknown_count": unknown,
        "support_ratio": supporting / count,
        "contradict_ratio": contradicting / count,
        "unknown_ratio": unknown / count,
        "polarity_margin": (supporting - contradicting) / count,
        "polarity_conflict": int(
            supporting > 0 and contradicting > 0
        ),
        "high_confidence_support": high_support,
        "high_confidence_contradict": high_contradict,
    }
def build_source_features(df):

    source_urls = (
        df["source_url"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    domains = [
        normalize_domain(url)
        for url in source_urls
    ]

    usable_urls = [
        url
        for url in source_urls
        if url
    ]

    usable_domains = [
        domain
        for domain in domains
        if domain
    ]

    source_mediums = (
        df["source_medium"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    source_mediums = [
        value
        for value in source_mediums
        if value
    ]

    evidence_count = len(df)

    if evidence_count == 0:
        evidence_count = 1

    unique_sources = len(set(usable_urls))
    unique_domains = len(set(usable_domains))
    unique_mediums = len(set(source_mediums))

    dominant_source_ratio = 0

    if usable_urls:

        counts = pd.Series(
            usable_urls
        ).value_counts()

        dominant_source_ratio = (
            counts.iloc[0]
            / evidence_count
        )

    return {
        "unique_source_count": unique_sources,
        "unique_domain_count": unique_domains,
        "source_medium_count": unique_mediums,

        "source_diversity_ratio":
            unique_sources / evidence_count,

        "domain_diversity_ratio":
            unique_domains / evidence_count,

        "dominant_source_ratio":
            dominant_source_ratio,
    }
def build_nli_features(claim, evidence):

    model_name = (
        "cross-encoder/nli-MiniLM2-L6-H768"
    )

    tokenizer = AutoTokenizer.from_pretrained(
        model_name
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name
    )

    model.eval()

    texts = (
        evidence["evidence_text"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    if not texts:

        return {
            feature: 0
            for feature in NLI_FEATURES
        }

    # Training used evidence as premise and claim as hypothesis.
    inputs = tokenizer(
        texts,
        [claim] * len(texts),
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )

    with torch.no_grad():

        outputs = model(
            **inputs
        )

    probabilities = torch.softmax(
        outputs.logits,
        dim=-1
    ).cpu().numpy()

    # The model's standard NLI label order is
    # contradiction / neutral / entailment.
    contradiction = probabilities[:, 0]
    neutral = probabilities[:, 1]
    entailment = probabilities[:, 2]

    confidence = probabilities.max(
        axis=1
    )

    count = len(texts)

    entail_count = int(
        (entailment >= 0.50).sum()
    )

    contradiction_count = int(
        (contradiction >= 0.50).sum()
    )

    neutral_count = int(
        (neutral >= 0.50).sum()
    )

    result = {

        "nli_evidence_count": count,

        "nli_entailment_count":
            entail_count,

        "nli_contradiction_count":
            contradiction_count,

        "nli_neutral_count":
            neutral_count,

        "nli_entailment_mean":
            float(entailment.mean()),

        "nli_contradiction_mean":
            float(contradiction.mean()),

        "nli_neutral_mean":
            float(neutral.mean()),

        "nli_max_entailment":
            float(entailment.max()),

        "nli_max_contradiction":
            float(contradiction.max()),

        "nli_mean_confidence":
            float(confidence.mean()),

        "nli_max_confidence":
            float(confidence.max()),

        "nli_entailment_ratio":
            entail_count / count,

        "nli_contradiction_ratio":
            contradiction_count / count,

        "nli_neutral_ratio":
            neutral_count / count,

        "nli_polarity_margin":
            float(
                entailment.mean()
                - contradiction.mean()
            ),

        "nli_conflict": int(
            entail_count > 0
            and contradiction_count > 0
        ),

        "nli_high_confidence_entail":
            int(
                (entailment >= 0.80).sum()
            ),

        "nli_high_confidence_contradict":
            int(
                (contradiction >= 0.80).sum()
            ),
    }

    return result
def build_features(claim, evidence):
    temporal = build_temporal_features(evidence)
    polarity = build_polarity_features(claim, evidence)
    source = build_source_features(evidence)
    nli = build_nli_features(claim, evidence)

    features = {
        "evidence_count": len(evidence),
        **temporal,
        **polarity,
        **source,
        **nli,
    }

    return pd.DataFrame([features])
def validate_features(feature_df, frozen_columns):

    generated = list(feature_df.columns)

    missing = [
        column
        for column in frozen_columns
        if column not in generated
    ]

    unexpected = [
        column
        for column in generated
        if column not in frozen_columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing features: {missing}"
        )

    if unexpected:
        raise RuntimeError(
            f"Unexpected features: {unexpected}"
        )

    ordered = feature_df[frozen_columns].copy()

    if ordered.isna().any().any():
        raise RuntimeError("NaN values detected.")

    if np.isinf(ordered.to_numpy()).any():
        raise RuntimeError("Infinite values detected.")

    return ordered