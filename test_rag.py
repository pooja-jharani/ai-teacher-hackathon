"""
Standalone test for the RAG / document-upload path: parse a real file,
chunk it, retrieve relevant chunks for a question, and confirm the
lesson planner actually grounds its output in that material (not just
generating generic content from the topic name alone).

Run:
    cd ai_teacher
    python test_rag.py path\\to\\your\\file.pdf "a topic or question about it"

If you don't have a sample PDF handy, any short PDF/DOCX/TXT works --
a syllabus page, an article printout, lecture notes, etc.
"""
import sys
import ingest
import retrieval
import planner


def line(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    if len(sys.argv) < 3:
        print('Usage: python test_rag.py <path_to_file> "topic or question"')
        sys.exit(1)

    file_path = sys.argv[1]
    topic = sys.argv[2]

    with open(file_path, "rb") as f:
        file_bytes = f.read()
    filename = file_path.split("\\")[-1].split("/")[-1]

    # 1. Extract + chunk
    line("1. INGEST -- extract and chunk the uploaded file")
    chunks = ingest.process_upload(file_bytes, filename)
    print(f"Extracted {len(chunks)} chunk(s) from {filename}")
    if chunks:
        preview = chunks[0].text[:300]
        print(f"\nFirst chunk preview:\n{preview}...")
    else:
        print("!! No chunks produced -- check that the file has extractable text "
              "(not a scanned/image-only PDF, which needs OCR that this project doesn't do).")
        return

    # 2. Retrieve
    line("2. RETRIEVAL -- find chunks relevant to the topic")
    retriever = retrieval.build_retriever(chunks)
    retrieved = retriever.retrieve(topic, top_k=4)
    print(f"Retrieved {len(retrieved)} relevant chunk(s) for: \"{topic}\"")
    for i, r in enumerate(retrieved, 1):
        print(f"\n  [{i}] score={r.score:.3f} source={r.source}")
        print(f"      {r.text[:200]}...")

    if not retrieved:
        print("\n!! Nothing retrieved -- either the topic doesn't match the material's "
              "wording well, or something's off in retrieval.py. Try a topic phrase "
              "using words that actually appear in the document.")
        return

    context = retrieval.format_context(retrieved)

    # 3. Feed into the planner and check it's actually grounded
    line("3. LESSON PLAN -- grounded in the uploaded material")
    plan = planner.generate_lesson_plan(
        topic_or_instruction=topic,
        context=context,
        learner_level="Beginner",
        minutes_available=15,
        language="English",
    )
    print(f"Title: {plan.title}")
    for s in plan.segments:
        print(f"\n  [{s.get('segment_id')}] {s.get('title')}")
        print(f"      {s.get('explanation', '')[:250]}...")

    line("CHECK")
    print("Read the segments above and compare them against your source file.")
    print("Grounded  = specific facts/wording/examples clearly pulled from your document.")
    print("Ungrounded = generic textbook content that could've been written without")
    print("             ever seeing your file. If it looks ungrounded, the retrieved")
    print("             chunks above may not be reaching the planner correctly.")


if __name__ == "__main__":
    main()
