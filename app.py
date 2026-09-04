"""
AI Teacher -- main Streamlit app.

Flow: upload material or enter a topic -> set level/time/language ->
generate personalized lesson plan -> watch each segment as a narrated
video -> answer a checkpoint question -> get adaptive re-teaching if
wrong -> final assessment -> report.

Run with:  streamlit run app.py
"""
import os
import uuid
import streamlit as st

import config
import ingest
import retrieval
import planner
import evaluator
import tts
import video
import report as report_mod
import profile_store

st.set_page_config(page_title="AI Teacher", page_icon="🎓", layout="centered")


def init_state():
    defaults = {
        "stage": "setup",          # setup -> lesson -> assessment -> report
        "retriever": None,
        "plan": None,
        "current_segment_idx": 0,
        "session_records": [],      # list of evaluator.Evaluation-like dicts with concept
        "struggle_count": {},       # segment_id -> number of retries
        "student_id": "guest",
        "topic": "",
        "language": "English",
        "level": "Beginner",
        "report_saved": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def media_path(name: str) -> str:
    return os.path.join(config.MEDIA_DIR, name)


def generate_segment_media(segment: dict) -> str:
    """Synthesizes audio + video for a single segment, returns video path."""
    seg_id = segment.get("segment_id", 0)
    audio_path = media_path(f"seg_{seg_id}_{uuid.uuid4().hex[:6]}.mp3")
    video_path = media_path(f"seg_{seg_id}_{uuid.uuid4().hex[:6]}.mp4")

    narration = segment.get("explanation", "") + " " + segment.get("example", "")
    tts.synthesize(narration, st.session_state.language, audio_path)
    video.render_segment_video(segment, audio_path, video_path)
    return video_path


# ---------------------------------------------------------------- SETUP
def render_setup():
    st.title("🎓 AI Teacher")
    st.caption("A personalized, adaptive AI-taught lesson -- from your material or any topic.")

    mode = st.radio("How do you want to learn?", ["Upload material", "Just give me a topic"])

    context_text = ""
    if mode == "Upload material":
        uploaded = st.file_uploader("Upload a book, textbook, notes, PDF, DOCX, or PPTX", type=["pdf", "docx", "pptx", "txt", "md"])
        if uploaded:
            chunks = ingest.process_upload(uploaded.read(), uploaded.name)
            st.session_state.retriever = retrieval.build_retriever(chunks)
            st.success(f"Processed {uploaded.name} into {len(chunks)} chunks for retrieval.")

    topic = st.text_input(
        "What should the lesson focus on? (e.g. 'Teach me Chapter 4', 'Explain Newton's Laws', 'Teach me React for interviews')",
        value=st.session_state.topic,
    )

    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("Learner level", ["Beginner", "Intermediate", "Advanced"])
    with col2:
        minutes = st.slider("Time available (minutes)", 5, 60, 20, step=5)

    language = st.selectbox(
        "Teaching language",
        ["English", "Hindi", "Hinglish", "Marathi", "Tamil", "Telugu", "Bengali", "Spanish", "French"],
    )

    st.session_state.student_id = st.text_input("Your name (for your learning profile)", value="guest")

    if st.button("Generate my lesson", type="primary", disabled=not topic):
        with st.spinner("Planning your personalized lesson..."):
            context = ""
            if st.session_state.retriever is not None:
                retrieved = st.session_state.retriever.retrieve(topic, top_k=5)
                context = retrieval.format_context(retrieved)

            plan = planner.generate_lesson_plan(
                topic_or_instruction=topic,
                context=context,
                learner_level=level,
                minutes_available=minutes,
                language=language,
            )
            st.session_state.plan = plan
            st.session_state.topic = topic
            st.session_state.level = level
            st.session_state.language = language
            st.session_state.current_segment_idx = 0
            st.session_state.session_records = []
            st.session_state.stage = "lesson"
        st.rerun()


# ---------------------------------------------------------------- LESSON
def render_lesson():
    plan = st.session_state.plan
    segments = plan.segments
    idx = st.session_state.current_segment_idx

    st.title(plan.title)
    st.progress((idx) / max(len(segments), 1))

    if idx >= len(segments):
        st.session_state.stage = "assessment"
        st.rerun()
        return

    segment = segments[idx]
    st.subheader(f"Segment {idx + 1} of {len(segments)}: {segment.get('title')}")

    video_key = f"video_path_{segment.get('segment_id')}_{idx}"
    if video_key not in st.session_state:
        with st.spinner("Generating your teaching video (narration + visuals)..."):
            st.session_state[video_key] = generate_segment_media(segment)

    st.video(st.session_state[video_key])
    with st.expander("Show explanation text"):
        st.write(segment.get("explanation"))
        st.write("**Example:** " + segment.get("example", ""))

    st.markdown("---")
    st.markdown(f"**Checkpoint:** {segment.get('checkpoint_question')}")
    answer_key = f"answer_{segment.get('segment_id')}_{idx}"
    student_answer = st.text_area("Your answer", key=answer_key)

    if st.button("Submit answer"):
        with st.spinner("Checking your understanding..."):
            eval_result = evaluator.evaluate_answer(
                question=segment.get("checkpoint_question"),
                answer_key=segment.get("checkpoint_answer_key"),
                student_answer=student_answer,
                concept=segment.get("concept"),
                language=st.session_state.language,
            )
        st.session_state.session_records.append({
            "concept": segment.get("concept"),
            "verdict": eval_result.verdict,
        })

        if eval_result.verdict == "correct":
            st.success(eval_result.feedback)
        elif eval_result.verdict == "partial":
            st.warning(eval_result.feedback)
        else:
            st.error(eval_result.feedback)

        if eval_result.should_advance:
            st.session_state.current_segment_idx += 1
            for k in list(st.session_state.keys()):
                if k.startswith("video_path_") or k.startswith("answer_"):
                    pass  # keep history; new segment gets a fresh key naturally
            st.rerun()
        else:
            seg_id = segment.get("segment_id")
            retries = st.session_state.struggle_count.get(seg_id, 0)
            st.session_state.struggle_count[seg_id] = retries + 1

            if retries >= 2:
                st.info("Let's move on and revisit this concept in your report -- you can review it after the lesson.")
                st.session_state.current_segment_idx += 1
                st.rerun()
            else:
                st.info("Let's try that concept a different way.")
                with st.spinner("Re-teaching this concept..."):
                    new_segment = planner.regenerate_segment_simpler(
                        segment, st.session_state.level, st.session_state.language, eval_result.misconception
                    )
                    new_segment["segment_id"] = seg_id
                    segments[idx] = new_segment
                    st.session_state[f"video_path_{seg_id}_{idx}"] = generate_segment_media(new_segment)
                st.rerun()


# ---------------------------------------------------------------- ASSESSMENT
def render_assessment():
    plan = st.session_state.plan
    st.title("📝 Final Assessment")
    st.caption("Let's check your understanding of the full lesson.")

    questions = plan.final_questions
    answers = []
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}. {q.get('question')}**")
        ans = st.text_area("Your answer", key=f"final_q_{i}")
        answers.append((q, ans))

    if st.button("Submit assessment", type="primary"):
        with st.spinner("Grading your assessment..."):
            for q, ans in answers:
                if not ans.strip():
                    st.session_state.session_records.append({"concept": q.get("concept"), "verdict": "incorrect"})
                    continue
                result = evaluator.evaluate_answer(
                    question=q.get("question"),
                    answer_key=q.get("answer_key"),
                    student_answer=ans,
                    concept=q.get("concept"),
                    language=st.session_state.language,
                )
                st.session_state.session_records.append({"concept": q.get("concept"), "verdict": result.verdict})
        st.session_state.stage = "report"
        st.rerun()


# ---------------------------------------------------------------- REPORT
def render_report():
    st.title("📊 Your Learning Report")
    records = [report_mod.SessionRecord(concept=r["concept"], verdict=r["verdict"]) for r in st.session_state.session_records]

    with st.spinner("Compiling your report..."):
        lesson_report = report_mod.compile_report(st.session_state.topic, records, st.session_state.language)

    st.metric("Score", f"{lesson_report.score_percent}%")
    st.write(lesson_report.summary)

    col1, col2 = st.columns(2)
    with col1:
        st.success("**Strong areas**\n\n" + ("\n".join(f"- {c}" for c in lesson_report.strong_concepts) or "None yet"))
    with col2:
        st.warning("**Needs improvement**\n\n" + ("\n".join(f"- {c}" for c in lesson_report.weak_concepts) or "None"))

    st.info(f"**Recommendation:** {lesson_report.recommendation}")

    if not st.session_state.report_saved:
        profile_store.record_session(
        student_id=st.session_state.student_id,
        topic=st.session_state.topic,
        score=lesson_report.score_percent,
        strong=lesson_report.strong_concepts,
        weak=lesson_report.weak_concepts,
        recommendation=lesson_report.recommendation,
    )
    st.session_state.report_saved = True

    profile = profile_store.get_profile(st.session_state.student_id)
    with st.expander("Your learning history"):
        for s in profile["sessions"]:
            st.write(f"- {s['topic']} — {s['score']}% — {s['timestamp'][:10]}")

    if st.button("Start a new lesson"):
        for key in ["stage", "plan", "current_segment_idx", "session_records", "struggle_count", "retriever"]:
            st.session_state.pop(key, None)
        st.rerun()


# ---------------------------------------------------------------- MAIN
def main():
    init_state()
    st.sidebar.title("Settings")
    st.sidebar.write(f"LLM provider: `{config.LLM_PROVIDER}`")
    st.sidebar.write(f"TTS provider: `{config.TTS_PROVIDER}`")
    st.sidebar.write(f"Avatar provider: `{config.AVATAR_PROVIDER}`")
    st.sidebar.caption("Change providers in your .env file. See README for setup.")

    stage = st.session_state.stage
    if stage == "setup":
        render_setup()
    elif stage == "lesson":
        render_lesson()
    elif stage == "assessment":
        render_assessment()
    elif stage == "report":
        render_report()


if __name__ == "__main__":
    main()
