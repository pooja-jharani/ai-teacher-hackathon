"""
Standalone test for Person A's pieces: planner, evaluator, adaptive
re-teaching, report generation, and a non-English language check.

No Streamlit, no TTS, no video -- just the reasoning/text pipeline,
so you can verify it works before touching the UI at all.

Run:
    cd ai_teacher
    python test_person_a.py
"""
import json
import planner
import evaluator
import report as report_mod

TOPIC = "Explain Newton's Second Law of Motion"
LEVEL = "Beginner"
MINUTES = 15
LANGUAGE = "English"


def line(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    # 1. Generate a lesson plan (no uploaded material -- topic-only mode)
    line("1. LESSON PLAN")
    plan = planner.generate_lesson_plan(
        topic_or_instruction=TOPIC,
        context="",
        learner_level=LEVEL,
        minutes_available=MINUTES,
        language=LANGUAGE,
    )
    print(f"Title: {plan.title}")
    print(f"Segments: {len(plan.segments)}")
    for s in plan.segments:
        print(f"\n  [{s.get('segment_id')}] {s.get('title')}")
        print(f"      Concept: {s.get('concept')}")
        print(f"      Checkpoint Q: {s.get('checkpoint_question')}")

    if not plan.segments:
        print("\n!! No segments returned -- check the LLM output / JSON parsing in llm.py")
        return

    segment = plan.segments[0]

    # 2. Deliberately answer the first checkpoint WRONG
    line("2. EVALUATOR -- deliberately wrong answer")
    wrong_answer = "I'm not sure, maybe it has something to do with speed?"
    eval_result = evaluator.evaluate_answer(
        question=segment.get("checkpoint_question"),
        answer_key=segment.get("checkpoint_answer_key"),
        student_answer=wrong_answer,
        concept=segment.get("concept"),
        language=LANGUAGE,
    )
    print(f"Verdict: {eval_result.verdict}")
    print(f"Feedback: {eval_result.feedback}")
    print(f"Misconception detected: {eval_result.misconception}")
    print(f"Should advance: {eval_result.should_advance}")

    # 3. Adaptive re-teach -- should be a genuinely different explanation
    line("3. ADAPTIVE RE-TEACH -- check this actually differs from original")
    new_segment = planner.regenerate_segment_simpler(
        segment, LEVEL, LANGUAGE, eval_result.misconception
    )
    print("ORIGINAL explanation:\n", segment.get("explanation"))
    print("\nNEW explanation:\n", new_segment.get("explanation"))
    print("\nNEW checkpoint question:", new_segment.get("checkpoint_question"))
    print("\n>> Manually compare the two explanations above -- same analogy/wording",
          "\n>> repeated = bad. Different angle/analogy/simpler language = good.")

    # 4. Now answer CORRECTLY and check the evaluator agrees
    line("4. EVALUATOR -- correct answer")
    correct_answer = new_segment.get("checkpoint_answer_key", "")
    eval_correct = evaluator.evaluate_answer(
        question=new_segment.get("checkpoint_question"),
        answer_key=new_segment.get("checkpoint_answer_key"),
        student_answer=correct_answer,
        concept=new_segment.get("concept"),
        language=LANGUAGE,
    )
    print(f"Verdict: {eval_correct.verdict} (expect 'correct')")
    print(f"Feedback: {eval_correct.feedback}")

    # 5. Final report using a fabricated small session history
    line("5. FINAL REPORT")
    records = [
        report_mod.SessionRecord(concept=segment.get("concept"), verdict="incorrect"),
        report_mod.SessionRecord(concept=new_segment.get("concept"), verdict="correct"),
    ]
    rep = report_mod.compile_report(TOPIC, records, LANGUAGE)
    print(f"Score: {rep.score_percent}%")
    print(f"Summary: {rep.summary}")
    print(f"Strong concepts: {rep.strong_concepts}")
    print(f"Weak concepts: {rep.weak_concepts}")
    print(f"Recommendation: {rep.recommendation}")

    # 6. Language check -- same topic, Hindi this time
    line("6. LANGUAGE CHECK -- Hindi")
    hindi_plan = planner.generate_lesson_plan(
        topic_or_instruction=TOPIC,
        context="",
        learner_level=LEVEL,
        minutes_available=MINUTES,
        language="Hindi",
    )
    print(f"Title: {hindi_plan.title}")
    if hindi_plan.segments:
        print(f"First segment explanation:\n{hindi_plan.segments[0].get('explanation')}")
        print("\n>> Confirm the text above is actually in Hindi, not English.")
    else:
        print("!! No segments returned for Hindi -- check language handling in planner.py")

    line("DONE -- review the output above for each of the 4 checks")


if __name__ == "__main__":
    main()
