"""
Turns (topic or retrieved material, learner level, time budget, language)
into a structured lesson plan, then expands each plan segment into a full
teaching script (explanation + example + visual cue + checkpoint question).

This is the core "human-like teaching" logic the assessment weights most
heavily -- it is deliberately kept separate from video/voice rendering so
the teaching quality can be iterated on and tested in plain text first.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

import llm

PLANNER_SYSTEM = """You are an expert human teacher designing a personalized lesson.
You do NOT just answer questions -- you plan a teaching session the way a real
tutor would: introduce the topic, build concepts progressively, use concrete
examples suited to the learner's level, and insert checkpoint questions at
natural points to confirm understanding before moving on.

Ground your lesson in the provided context when given uploaded material.
If no material is provided, teach the topic from your own knowledge, but keep
it accurate and appropriately scoped for the learner's level and time budget.
"""

PLAN_SCHEMA_HINT = """Return a JSON object with this exact shape:
{
  "lesson_title": string,
  "learner_level": string,
  "language": string,
  "estimated_minutes": number,
  "segments": [
    {
      "segment_id": number,
      "title": string,
      "concept": string,
      "explanation": string,          // the actual teaching explanation, written to be spoken aloud
      "example": string,              // a concrete example illustrating the concept
      "visual_type": string,          // e.g. "diagram", "equation", "graph", "code", "timeline", "image"
      "visual_description": string,   // what the visual should show (used to generate a slide)
      "checkpoint_question": string,  // a question to check understanding of THIS segment
      "checkpoint_answer_key": string // what a correct answer should contain
    }
  ],
  "final_assessment_questions": [
    {"question": string, "answer_key": string, "concept": string}
  ]
}
"""


@dataclass
class LessonPlan:
    raw: dict

    @property
    def title(self) -> str:
        return self.raw.get("lesson_title", "Lesson")

    @property
    def segments(self) -> List[dict]:
        return self.raw.get("segments", [])

    @property
    def final_questions(self) -> List[dict]:
        return self.raw.get("final_assessment_questions", [])


def generate_lesson_plan(
    topic_or_instruction: str,
    context: str,
    learner_level: str,
    minutes_available: int,
    language: str,
    num_segments_hint: Optional[int] = None,
) -> LessonPlan:
    """
    context: retrieved RAG chunks formatted as text (empty string if topic-only mode)
    """
    seg_hint = num_segments_hint or max(2, min(6, minutes_available // 5))

    user_prompt = f"""Student request: "{topic_or_instruction}"

Learner level: {learner_level}
Time available: {minutes_available} minutes
Teaching language: {language}
Target number of segments: about {seg_hint}

{"Grounding material (use this as the primary source of truth):" if context else "No material was uploaded -- teach this topic from general knowledge."}
{context}

Design a personalized lesson plan following the schema below. Keep the
explanation field written as natural spoken teaching language (as if a
teacher is talking to the student), not textbook prose. Write ALL content
(explanation, example, questions) in {language}.

{PLAN_SCHEMA_HINT}
"""
    data = llm.chat_json(PLANNER_SYSTEM, user_prompt, max_tokens=6000)
    return LessonPlan(raw=data)


def regenerate_segment_simpler(segment: dict, learner_level: str, language: str, student_struggle_note: str) -> dict:
    """
    Called when the student got the checkpoint question wrong. Produces a
    NEW explanation for the same concept -- a different analogy, simpler
    language, or a broken-down version -- rather than repeating the same text.
    This is the core "adaptive teaching" behavior the brief requires.
    """
    system = PLANNER_SYSTEM
    user_prompt = f"""The student struggled with this segment:

Concept: {segment.get('concept')}
Original explanation: {segment.get('explanation')}
Student's issue: {student_struggle_note}

Re-teach this SAME concept to a {learner_level} learner in {language}, using:
- A different analogy or approach than the original explanation
- Simpler language than before
- A new, different example
- A new checkpoint question (not identical to the previous one) to re-check understanding

Return a JSON object with the same shape as a single segment:
{{
  "segment_id": {segment.get('segment_id')},
  "title": string,
  "concept": string,
  "explanation": string,
  "example": string,
  "visual_type": string,
  "visual_description": string,
  "checkpoint_question": string,
  "checkpoint_answer_key": string
}}
"""
    return llm.chat_json(system, user_prompt, max_tokens=3000)
