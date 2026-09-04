# AI Teacher 🎓

### Personalized AI-powered learning through interactive lessons, voice narration, adaptive teaching, and learning history

Built for **AI Innovation Hackathon 2026 — Round 2 (Bharat Academix)**.

---

## Overview

AI Teacher is an AI-powered learning platform that creates personalized lessons based on a learner's topic, level, language, and available time.

Learners can either:

- Upload learning material such as PDF, DOCX, or PPTX
- Provide a topic directly

The system then:

1. Retrieves relevant information from uploaded material using RAG.
2. Generates a structured and personalized lesson using an LLM.
3. Converts lesson segments into narrated teaching videos.
4. Asks checkpoint questions during the lesson.
5. Evaluates learner responses.
6. Detects incorrect understanding and triggers adaptive re-teaching.
7. Conducts a final assessment.
8. Generates a learning report with score, strengths, weak areas, and recommendations.
9. Persists learner history across sessions.

---

## Key Features

### 📚 RAG-Based Learning

Learners can upload study material.

The system:

`Document → Text Extraction → Chunking → Retrieval → Grounded Lesson`

The current retrieval implementation uses **TF-IDF**, providing a lightweight approach without requiring a separate embedding model.

Supported document formats include:

- PDF
- DOCX
- PPTX

---

### 🤖 AI Lesson Generation

Lessons are generated dynamically based on:

- Topic
- Learner level
- Language
- Available lesson time
- Retrieved learning material, when provided

The lesson is divided into manageable teaching segments with checkpoints.

---

### 🔄 Adaptive Re-Teaching

Adaptive teaching is a core part of the system.

When a learner gives an incorrect answer:

`Wrong Answer → Evaluation → Feedback → Re-teaching → New Checkpoint`

Instead of simply repeating the same explanation, the system generates a simpler alternative explanation with different examples or analogies.

---

### 🌐 Multilingual Teaching

The system supports language-aware lesson generation and narration.

Currently tested:

- English
- Hindi

The selected language is passed through the lesson-generation and TTS pipeline.

---

### 🔊 AI Voice

The current TTS provider is **gTTS**.

Both English and Hindi narration have been tested successfully.

---

### 🎥 Teaching Video Generation

The application generates slide-based teaching videos containing:

- Lesson title
- Subject-aware visual content
- Captions
- AI-generated narration
- Synchronized audio

The generated videos are playable directly through the Streamlit application.

---

### 📊 Assessment & Learning Report

At the end of a lesson, the system provides:

- Assessment score
- Strong concepts
- Weak concepts
- Personalized recommendation
- Learning history

---

### 💾 Learner Profile Persistence

Learner sessions are stored locally in JSON format.

The system maintains:

- Session history
- Strong concepts
- Weak concepts
- Recommendations
- Timestamps

This allows learning history to persist across sessions.

---

## Application Flow

```text
                  ┌──────────────────┐
                  │   Learner Setup  │
                  └────────┬─────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │ Topic / Uploaded Material│
              └────────────┬────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ RAG / LLM   │
                    └──────┬──────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ Personalized     │
                 │ Lesson Plan      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Teaching Video   │
                 │ + AI Voice       │
                 └────────┬─────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Checkpoint    │
                  │ Question      │
                  └───────┬───────┘
                          │
                   ┌──────┴──────┐
                   │             │
                Correct        Wrong
                   │             │
                   │             ▼
                   │      ┌──────────────┐
                   │      │ Adaptive     │
                   │      │ Re-teaching  │
                   │      └──────┬───────┘
                   │             │
                   └──────┬──────┘
                          ▼
                  ┌───────────────┐
                  │ Final         │
                  │ Assessment    │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Learning      │
                  │ Report        │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Learner       │
                  │ History       │
                  └───────────────┘
Tech Stack
Component	Technology
Frontend / UI	Streamlit
LLM	Google Gemini
RAG	TF-IDF + scikit-learn
Document Processing	pypdf, python-docx, python-pptx
TTS	gTTS
Video Generation	MoviePy + Pillow
Persistence	JSON
Configuration	python-dotenv
Language	Python
Project Structure
ai-teacher-hackathon/
│
├── app.py
├── config.py
├── ingest.py
├── retrieval.py
├── llm.py
├── planner.py
├── evaluator.py
├── tts.py
├── video.py
├── profile_store.py
├── report.py
│
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
└── data/
    ├── media/
    └── learner_profiles.json

data/ and .env are excluded from Git using .gitignore.

Quick Start
1. Clone the repository
git clone https://github.com/pooja-jharani/ai-teacher-hackathon.git
cd ai-teacher-hackathon
2. Install dependencies
pip install -r requirements.txt
3. Configure environment variables

Create a .env file in the project root.

Example:

LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash

TTS_PROVIDER=gtts

AVATAR_PROVIDER=slides

Never commit .env or API keys to GitHub.

4. Run the application
streamlit run app.py

The Streamlit interface will open in your browser.

Current Video / Avatar Implementation

The current implementation uses:

AVATAR_PROVIDER=slides

The slide-based provider generates narrated educational videos with synchronized audio and visuals.

D-ID and HeyGen providers are structured as optional provider paths in video.py, but they are not enabled in the current working configuration.

This keeps the demonstrated pipeline reproducible without requiring an external avatar API.

Adaptive Learning Example

A typical interaction looks like:

Learner answers checkpoint
          ↓
      Evaluation
          ↓
      Incorrect?
          ↓
  Misconception detected
          ↓
 Alternative explanation
          ↓
    Re-teaching
          ↓
   New checkpoint
          ↓
     Assessment

This allows the system to respond to learner performance instead of following a completely fixed lesson sequence.

Testing

The following components have been tested:

Gemini connectivity
Lesson generation
RAG ingestion and retrieval
English TTS
Hindi TTS
Slide-based video generation
Audio-video synchronization
Streamlit video playback
Checkpoint evaluation
Adaptive re-teaching
Final assessment
Learning report
Learner profile persistence
End-to-end lesson flow
End-to-End Validation

The complete flow was validated as:

Lesson Setup
     ↓
Lesson Generation
     ↓
Teaching Video
     ↓
Checkpoint
     ↓
Intentional Wrong Answer
     ↓
Adaptive Re-teaching
     ↓
New Checkpoint
     ↓
Final Assessment
     ↓
Learning Report
     ↓
Learner History
Evaluation Criteria Coverage
Criterion	Implementation
Human-Like Teaching & Adaptation	Adaptive checkpoint evaluation and re-teaching
AI / ML & LLM	Gemini-powered lesson generation and evaluation
RAG & Knowledge Grounding	Document ingestion + TF-IDF retrieval
AI Teaching Video	MoviePy/Pillow slide-based video generation
Multilingual Capability	Language-aware lessons + English/Hindi TTS
Voice	gTTS narration
Innovation	Misconception-aware adaptive re-teaching
UX / Interface	Streamlit interactive learning flow
Documentation	README + module documentation
Design Philosophy

AI Teacher is designed around a simple principle:

Teaching should adapt to the learner, not force every learner through the same explanation.

The system therefore combines:

Personalized lesson planning
Knowledge grounding
Interactive checkpoints
Performance evaluation
Adaptive re-teaching
Voice-based instruction
Learning history

into a single learning loop.

Known Limitations
Slide-Based Avatar

The current demo uses narrated educational slides rather than a photorealistic talking avatar.

The video pipeline is fully functional, but external avatar services such as D-ID or HeyGen are not enabled in the current configuration.

Lightweight Retrieval

RAG currently uses TF-IDF retrieval rather than neural embeddings.

This keeps the system lightweight and easy to run locally.

Local Persistence

Learner profiles are currently stored in a local JSON file rather than a production database.

Future Improvements

Possible future extensions include:

Real-time talking-avatar integration
Neural embedding-based retrieval
Vector database integration
Cloud learner profiles
More languages and TTS providers
Richer educational animations
Advanced learner analytics
Long-term personalized learning paths
Hackathon

AI Innovation Hackathon 2026 — Round 2

Theme: Bharat Academix

AI Teacher demonstrates an end-to-end AI-powered personalized teaching workflow combining LLMs, RAG, adaptive learning, voice narration, video generation, assessment, and learner persistence.