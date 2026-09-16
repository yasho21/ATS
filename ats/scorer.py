"""Scoring logic: TF-IDF similarity + keyword coverage between a resume and a job description."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Generic job-posting filler words that are technically not stopwords but
# carry little signal as "skills" when extracted as JD keywords.
EXTRA_STOPWORDS = {
    "experience", "experienced", "year", "years", "work", "working",
    "team", "teams", "ability", "role", "responsibilities", "requirements",
    "required", "preferred", "strong", "excellent", "including", "etc",
    "environment", "knowledge", "skills", "skill", "job", "company",
    "candidate", "candidates", "plus", "using", "used", "use", "related",
    "field", "position", "opportunity", "looking", "join", "help", "new",
    "day", "based", "understanding", "like", "good", "great",
}

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,}")

MIN_KEYWORDS = 5
MAX_KEYWORDS = 25


@dataclass
class MatchResult:
    overall_score: int
    similarity_score: int
    keyword_score: int
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    verdict: str = ""
    resume_word_count: int = 0
    jd_word_count: int = 0

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "similarity_score": self.similarity_score,
            "keyword_score": self.keyword_score,
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "verdict": self.verdict,
            "resume_word_count": self.resume_word_count,
            "jd_word_count": self.jd_word_count,
        }


def _tokenize(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(text.lower())
    cleaned = [t.rstrip("./-") for t in tokens]
    return [t for t in cleaned if t]


def _is_meaningful(token: str) -> bool:
    if len(token) < 3:
        return False
    if token in ENGLISH_STOP_WORDS or token in EXTRA_STOPWORDS:
        return False
    if token.isdigit():
        return False
    return True


def _extract_keywords(jd_text: str) -> list[str]:
    tokens = _tokenize(jd_text)
    meaningful = [t for t in tokens if _is_meaningful(t)]

    unigram_counts = Counter(meaningful)

    bigrams = []
    for i in range(len(tokens) - 1):
        a, b = tokens[i], tokens[i + 1]
        if _is_meaningful(a) and _is_meaningful(b):
            bigrams.append(f"{a} {b}")
    bigram_counts = Counter(bigrams)

    # Weight bigrams higher since they capture more specific skills/phrases
    # (e.g. "machine learning", "project management").
    scored: Counter[str] = Counter()
    for term, count in unigram_counts.items():
        scored[term] += count
    for term, count in bigram_counts.items():
        if count >= 2:
            scored[term] += count * 2

    ranked = [term for term, _ in scored.most_common(MAX_KEYWORDS * 2)]

    # Drop unigrams that are already covered by a selected bigram to avoid
    # redundant entries like "machine" + "learning" + "machine learning".
    selected: list[str] = []
    covered_words: set[str] = set()
    for term in ranked:
        words = term.split()
        if len(words) == 1 and term in covered_words:
            continue
        selected.append(term)
        if len(words) == 2:
            covered_words.update(words)
        if len(selected) >= MAX_KEYWORDS:
            break

    return selected[: max(MIN_KEYWORDS, len(selected))]


def _keyword_present(keyword: str, resume_text_lower: str) -> bool:
    pattern = r"\b" + re.escape(keyword) + r"\b"
    if re.search(pattern, resume_text_lower):
        return True
    # naive plural/singular tolerance
    if keyword.endswith("s") and re.search(r"\b" + re.escape(keyword[:-1]) + r"\b", resume_text_lower):
        return True
    if not keyword.endswith("s") and re.search(r"\b" + re.escape(keyword) + r"s\b", resume_text_lower):
        return True
    return False


def _similarity_score(resume_text: str, jd_text: str) -> int:
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        tfidf = vectorizer.fit_transform([resume_text, jd_text])
    except ValueError:
        return 0
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(max(0.0, min(1.0, score)) * 100)


def _verdict(score: int) -> str:
    if score >= 80:
        return "Excellent Match"
    if score >= 65:
        return "Strong Match"
    if score >= 45:
        return "Moderate Match"
    return "Weak Match"


def score_resume(resume_text: str, jd_text: str) -> MatchResult:
    resume_text_lower = resume_text.lower()

    keywords = _extract_keywords(jd_text)
    matched = [kw for kw in keywords if _keyword_present(kw, resume_text_lower)]
    missing = [kw for kw in keywords if kw not in matched]

    keyword_score = round((len(matched) / len(keywords)) * 100) if keywords else 0
    similarity_score = _similarity_score(resume_text, jd_text)

    overall_score = round(0.5 * similarity_score + 0.5 * keyword_score)

    return MatchResult(
        overall_score=overall_score,
        similarity_score=similarity_score,
        keyword_score=keyword_score,
        matched_keywords=matched,
        missing_keywords=missing,
        verdict=_verdict(overall_score),
        resume_word_count=len(_tokenize(resume_text)),
        jd_word_count=len(_tokenize(jd_text)),
    )
