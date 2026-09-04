"""
Evaluates a student's answer to a checkpoint or assessment question.
Does NOT just mark right/wrong -- identifies the specific misconception
so the planner can re-teach appropriately. This is the module most directly
tied to the "Human-Like Teaching & Adaptation" criterion (20% weight).
"""
from __future__ import annotations
from dataclasses import dataclass

import llm

EVALUATOR_SYSTEM = """You are an expert, encouraging teacher evaluating a student's answer.
You do not simply mark answers right or wrong. You diagnose WHY an answer is
wrong when it is wrong, in the way an experienced human tutor would --
identifying the specific misconception rather than a generic "incorrect".
Be warm and constructive, never dismissive.
"""


@dataclass
class Evaluation:
    verdict: str          # "correct" | "partial" | "incorrect"
    feedback: str          # short encouraging feedback shown to student immediately
    misconception: str     # empty string if correct
    should_advance: bool   # True if the student can move to the next segment


def evaluate_answer(question: str, answer_key: str, student_answer: str, concept: str, language: str) -> Evaluation:
    user_prompt = f"""Concept being tested: {concept}
Question asked: {question}
What a correct answer should contain: {answer_key}
Student's actual answer: "{student_answer}"

Evaluate the student's answer. Respond in {language}. Return JSON:
{{
  "verdict": "correct" | "partial" | "incorrect",
  "feedback": string,          // 1-3 sentences of direct feedback to the student, constructive and specific
  "misconception": string,     // the specific misunderstanding, empty string "" if verdict is "correct"
  "should_advance": boolean    // true if understanding is sufficient to move on, false if re-teaching is needed
}}
"""
    data = llm.chat_json(EVALUATOR_SYSTEM, user_prompt, max_tokens=2000)
    return Evaluation(
        verdict=data.get("verdict", "incorrect"),
        feedback=data.get("feedback", ""),
        misconception=data.get("misconception", ""),
        should_advance=bool(data.get("should_advance", False)),
    )
