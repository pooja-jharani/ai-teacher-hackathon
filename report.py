"""
Generates the end-of-lesson assessment report: score, strong/weak areas,
incorrect concepts, and a recommended next step -- matching the exact
report shape shown in the assessment brief (Topic / Score / Strong Areas /
Needs Improvement / Recommendation).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

import llm

REPORT_SYSTEM = """You are a teacher writing a short, encouraging end-of-lesson
report for a student, based on their checkpoint and final assessment answers."""


@dataclass
class SessionRecord:
    concept: str
    verdict: str  # correct / partial / incorrect


@dataclass
class LessonReport:
    topic: str
    score_percent: float
    strong_concepts: List[str]
    weak_concepts: List[str]
    recommendation: str
    summary: str


def compile_report(topic: str, records: List[SessionRecord], language: str) -> LessonReport:
    total = len(records) or 1
    correct = sum(1 for r in records if r.verdict == "correct")
    partial = sum(1 for r in records if r.verdict == "partial")
    score = round((correct + 0.5 * partial) / total * 100, 1)

    # Track the LATEST verdict per concept, not every verdict ever given --
    # a concept the student initially struggled with but got right after
    # adaptive re-teaching should count as understood, not stay flagged as
    # weak just because an earlier attempt on it failed.
    latest_verdict_by_concept = {}
    for r in records:
        latest_verdict_by_concept[r.concept] = r.verdict

    strong = sorted(c for c, v in latest_verdict_by_concept.items() if v == "correct")
    weak = sorted(c for c, v in latest_verdict_by_concept.items() if v in ("partial", "incorrect"))

    user_prompt = f"""Topic: {topic}
Score: {score}%
Strong concepts: {', '.join(strong) or 'None yet'}
Concepts needing improvement: {', '.join(weak) or 'None'}

Write in {language}:
1. A short (2-3 sentence) encouraging summary of how the session went.
2. One specific, actionable recommendation for what to revise or study next.

Return JSON: {{"summary": string, "recommendation": string}}
"""
    data = llm.chat_json(REPORT_SYSTEM, user_prompt, max_tokens=1500)

    return LessonReport(
        topic=topic,
        score_percent=score,
        strong_concepts=strong,
        weak_concepts=weak,
        recommendation=data.get("recommendation", "Revisit the weaker concepts above."),
        summary=data.get("summary", ""),
    )
