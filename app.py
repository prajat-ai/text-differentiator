import os
import re
import json
from io import BytesIO
from datetime import datetime

import streamlit as st
from openai import OpenAI
from openai import OpenAIError  # noqa: F401  (kept for completeness)

# ---------- Configuration ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY not found. Set it in your environment or Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="Text Differentiator Pro",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Apple‑style CSS (updated for light & dark modes, no emojis / outlines) ----------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text',
                     'Helvetica Neue', Helvetica, Arial, sans-serif;
        box-sizing: border-box;
    }

    .stApp {
        background: var(--background-color);
        color: var(--text-color);
        /* Respect the active Streamlit theme */
        color-scheme: light dark;
    }

    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none;}

    /* -------- HERO -------- */
    .hero-section {
        text-align: center;
        padding: 3rem 0 2rem 0;
        background: linear-gradient(180deg, var(--background-color) 0%, #f5f5f7 100%);
        border-bottom: 1px solid #d2d2d7;
        margin: -3rem -3rem 2rem -3rem;
    }
    .hero-title   {font-size: 56px; font-weight: 700; line-height: 1.1;}
    .hero-subtitle{font-size: 21px; color: #86868b; line-height: 1.4;}

    /* -------- GENERIC CARDS -------- */
    .card-container {
        background: var(--background-color);
        border-radius: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        padding: 32px;
        margin-bottom: 24px;
        border: 1px solid #e5e5e7;
    }

    /* -------- TEXT COMPARISON -------- */
    .text-comparison-container {display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px;}
    .text-display-box {
        background: var(--secondary-background-color);
        border-radius: 12px;
        padding: 24px;
        height: 500px;
        overflow-y: auto;
        border: 1px solid #d2d2d7;
    }
    .text-label   {font-size: 17px; font-weight: 600; margin-bottom: 16px;}
    .text-content {font-size: 15px; line-height: 1.6; white-space: pre-wrap;}

    /* -------- INPUT AREA -------- */
    .stTextArea textarea {
        background: #ffffff;
        border: 1px solid #d2d2d7;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 15px;
        line-height: 1.5;
    }
    .stTextArea textarea:focus {border-color: #8e8e93; outline: none; box-shadow: none;}

    /* -------- SIDEBAR -------- */
    section[data-testid="stSidebar"] {
        background: var(--background-color);
        border-right: 1px solid #d2d2d7;
    }
    section[data-testid="stSidebar"] .block-container {padding: 2rem 1rem;}
    .sidebar-header {font-size: 19px; font-weight: 600; margin-bottom: 16px;}

    /* -------- SELECTBOX -------- */
    .stSelectbox label {font-size: 13px; font-weight: 500; color: #86868b; margin-bottom: 4px;}
    .stSelectbox > div > div {
        background: var(--secondary-background-color);
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 15px;
    }

    /* -------- BUTTONS -------- */
    .stButton button, .stDownloadButton button {
        background: #1d1d1f;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-size: 15px;
        font-weight: 500;
        transition: all .15s ease;
        min-height: 40px;
    }
    .stButton button:hover, .stDownloadButton button:hover {opacity: .85;}

    /* -------- METRIC CARDS -------- */
    .metric-card    {background: var(--background-color); border: 1px solid #d2d2d7; border-radius: 12px; padding: 20px; text-align: center;}
    .metric-value   {font-size: 32px; font-weight: 700; margin-bottom: 4px;}
    .metric-label   {font-size: 13px; color: #86868b; font-weight: 500;}

    /* -------- TABS -------- */
    .stTabs [data-baseweb="tab-list"] {gap: 24px; border-bottom: 1px solid #d2d2d7;}
    .stTabs [data-baseweb="tab"] {height: 44px; background: transparent; border: none; font-size: 17px; font-weight: 500; padding-bottom: 12px;}
    .stTabs [aria-selected="true"] {border-bottom: 2px solid #1d1d1f;}

    /* -------- RESPONSIVE -------- */
    @media (max-width: 768px){
        .text-comparison-container {grid-template-columns: 1fr;}
        .hero-title   {font-size: 40px;}
        .hero-subtitle{font-size: 18px;}
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Helper Functions ----------
def calculate_readability_metrics(text: str):
    """Return basic readability metrics for the supplied text."""
    sentences = re.split(r"[.!?]+", text)
    words = text.split()
    syllables = sum(count_syllables(w) for w in words)

    if sentences and words:
        avg_sentence_len = len(words) / len(sentences)
        avg_syllables = syllables / len(words)
        score = 206.835 - 1.015 * avg_sentence_len - 84.6 * avg_syllables
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_sentence_length": round(avg_sentence_len, 1),
            "reading_ease": round(score, 1),
        }
    return None


def count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    if word and word[0] in vowels:
        count += 1
    for i in range(1, len(word)):
        if word[i] in vowels and word[i - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    return count or 1


def get_grade_specific_guidelines(grade: str):
    guidelines = {
        "Kindergarten": {
            "sentence_length": "3–5 words",
            "vocabulary": "Basic sight words, CVC words",
            "complexity": "Simple subject–verb sentences",
            "concepts": "Concrete, everyday objects and actions",
        },
        "1st Grade": {
            "sentence_length": "5–8 words",
            "vocabulary": "Common sight words, simple descriptive words",
            "complexity": "Simple sentences with basic conjunctions",
            "concepts": "Familiar experiences, basic cause–effect",
        },
        "2nd Grade": {
            "sentence_length": "8–12 words",
            "vocabulary": "Expanding sight words, simple multisyllable words",
            "complexity": "Compound sentences with 'and', 'but'",
            "concepts": "Simple comparisons, basic sequencing",
        },
        "3rd Grade": {
            "sentence_length": "10–15 words",
            "vocabulary": "Academic vocabulary with context clues",
            "complexity": "Complex sentences with dependent clauses",
            "concepts": "Abstract ideas with concrete examples",
        },
        "4th Grade": {
            "sentence_length": "12–18 words",
            "vocabulary": "Subject‑specific terms, multiple meanings",
            "complexity": "Varied sentence structures",
            "concepts": "Cause–effect relationships, basic inference",
        },
        "5th Grade": {
            "sentence_length": "15–20 words",
            "vocabulary": "Advanced vocabulary, figurative language",
            "complexity": "Sophisticated sentence variety",
            "concepts": "Abstract concepts, critical thinking",
        },
    }
    default = {
        "sentence_length": "Varies widely",
        "vocabulary": "Grade‑appropriate academic vocabulary",
        "complexity": "Full range of sentence structures",
        "concepts": "Abstract and complex ideas",
    }
    return guidelines.get(grade, default)


def generate_history_pdf(history_list):
    """Return a PDF bytes object containing adaptation history."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return None  # ReportLab not available

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50
    y = height - margin

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, "Text Differentiator Pro — Adaptation History")
    y -= 30
    c.setFont("Helvetica", 11)

    for item in history_list:
        timestamp = item["timestamp"]
        grade = item["grade"]
        orig = item["original"]
        adap = item["adapted"]

        lines = [
            f"Timestamp: {timestamp}",
            f"Grade: {grade}",
            "Original (preview): " + orig,
            "Adapted (preview):  " + adap,
            "-" * 80,
        ]
        for line in lines:
            if y < margin + 40:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 11)
            c.drawString(margin, y, line)
            y -= 14

    c.save()
    buffer.seek(0)
    return buffer.read()


# ---------- Main Content ----------
st.markdown(
    """
<div class="hero-section">
    <h1 class="hero-title">Text Differentiator Pro</h1>
    <p class="hero-subtitle">Transform instructional materials into accessible texts for any learner.</p>
</div>
""",
    unsafe_allow_html=True,
)

# Session state
st.session_state.setdefault("adapted_text", "")
st.session_state.setdefault("questions", "")
st.session_state.setdefault("history", [])

# ------------- SIDEBAR -------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">Configuration</div>', unsafe_allow_html=True)

    grades = [
        "Kindergarten",
        "1st Grade",
        "2nd Grade",
        "3rd Grade",
        "4th Grade",
        "5th Grade",
        "6th Grade",
        "7th Grade",
        "8th Grade",
        "9th Grade",
        "10th Grade",
        "11th Grade",
        "12th Grade",
    ]
    target_grade = st.selectbox("Target grade level", grades, index=2)

    st.markdown("---")
    st.markdown('<div class="sidebar-header">AI Settings</div>', unsafe_allow_html=True)
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
    )

    # NOTE:  Temperature slider removed.  Fixed temperature used internally.

    st.markdown("---")
    st.markdown('<div class="sidebar-header">Accessibility Options</div>', unsafe_allow_html=True)
    use_simple_vocab = st.checkbox("Simplify vocabulary", value=True)
    add_definitions = st.checkbox("Add in‑text definitions", value=True)
    use_short_paragraphs = st.checkbox("Short paragraphs", value=True)
    add_visual_breaks = st.checkbox("Add visual breaks", value=False)

    st.markdown("---")
    st.markdown('<div class="sidebar-header">Output Options</div>', unsafe_allow_html=True)
    generate_questions = st.checkbox("Generate comprehension questions", value=True)
    generate_vocabulary = st.checkbox("Generate vocabulary list", value=False)  # Placeholder for future use
    generate_summary = st.checkbox("Generate summary", value=False)  # Placeholder for future use


# ------------- TABS -------------
tab_adapt, tab_analytics, tab_history = st.tabs(["Adapt Text", "Analytics", "History"])

# ------- ADAPT TAB -------
with tab_adapt:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.markdown("#### Input Text")

    input_text = st.text_area(
        "Paste or type the text you want to adapt",
        height=200,
        placeholder="Enter your text here...",
    )

    col_a, col_b = st.columns([1, 1])
    adapt_button = col_a.button("Adapt Text", use_container_width=True)
    clear_button = col_b.button("Clear", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if clear_button:
        st.session_state.adapted_text = ""
        st.session_state.questions = ""
        st.rerun()

    if adapt_button and input_text.strip():
        with st.spinner(f"Adapting text for {target_grade}..."):
            try:
                guidelines = get_grade_specific_guidelines(target_grade)
                system_prompt = f"""
You are an expert special‑education content specialist.

TARGET AUDIENCE: {target_grade} students with diverse learning needs:
- Reading difficulties
- Attention challenges
- English‑language learners
- Cognitive differences

ADAPTATION RULES
  • Sentence length: {guidelines['sentence_length']}
  • Vocabulary: {guidelines['vocabulary']}
  • Complexity: {guidelines['complexity']}
  • Concepts:   {guidelines['concepts']}

ACCOMMODATIONS
  {'• Use simple vocabulary' if use_simple_vocab else ''}
  {'• Provide definitions in parentheses' if add_definitions else ''}
  {'• Limit paragraphs to 2–3 sentences' if use_short_paragraphs else ''}
  {'• Insert blank lines between ideas' if add_visual_breaks else ''}
  • Clear topic sentences and transitions
  • Replace idioms with literal language
  • Use active voice

CONTENT PRESERVATION
  • All key ideas must remain intact
  • Keep original meaning and purpose

OUTPUT
  • Markdown only (no commentary)
  • Bold key terms
  • Use bullet lists where helpful
  • Short, focused paragraphs
"""

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Adapt this text for {target_grade} students:\n\n{input_text}"},
                ]

                response = client.chat.completions.create(
                    model=model,
                    temperature=0.3,  # fixed temperature
                    messages=messages,
                    max_tokens=2000,
                )
                st.session_state.adapted_text = response.choices[0].message.content.strip()

                # Add history preview
                st.session_state.history.append(
                    {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "grade": target_grade,
                        "original": (input_text[:100] + "...") if len(input_text) > 100 else input_text,
                        "adapted": (
                            st.session_state.adapted_text[:100] + "..."
                            if len(st.session_state.adapted_text) > 100
                            else st.session_state.adapted_text
                        ),
                    }
                )

                # Optional questions
                if generate_questions:
                    q_prompt = f"""
Create 6 comprehension questions for {target_grade} students:

1–2 literal (who/what/where/when)
3–4 inferential (why/how)
5 vocabulary in context
6 personal connection
"""
                    q_messages = [
                        {
                            "role": "system",
                            "content": "You write clear, level‑appropriate comprehension questions.",
                        },
                        {"role": "user", "content": f"{q_prompt}\n\nTEXT:\n{st.session_state.adapted_text}"},
                    ]
                    q_resp = client.chat.completions.create(model=model, temperature=0.3, messages=q_messages)
                    st.session_state.questions = q_resp.choices[0].message.content.strip()

                st.success("Text adapted successfully.")

            except Exception as e:
                st.error(f"Error: {e}")

    # SHOW OUTPUT
    if st.session_state.adapted_text:
        st.markdown("---")
        st.markdown("#### Text Comparison")

        st.markdown(
            f"""
<div class="text-comparison-container">
  <div class="text-display-box">
    <div class="text-label">Original</div>
    <div class="text-content">{input_text}</div>
  </div>
  <div class="text-display-box">
    <div class="text-label">Adapted for {target_grade}</div>
    <div class="text-content">{st.session_state.adapted_text}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        if generate_questions and st.session_state.questions:
            st.markdown("---")
            st.markdown("#### Comprehension Questions")
            st.markdown(st.session_state.questions)

        # Export options
        st.markdown("---")
        st.markdown("#### Export")

        col_x, col_y, col_z = st.columns(3)

        col_x.download_button(
            "Download adapted text",
            data=st.session_state.adapted_text,
            file_name=f"adapted_{target_grade}_{datetime.now():%Y%m%d_%H%M}.txt",
            mime="text/plain",
        )

        if st.session_state.questions:
            col_y.download_button(
                "Download questions",
                data=st.session_state.questions,
                file_name=f"questions_{target_grade}_{datetime.now():%Y%m%d_%H%M}.txt",
                mime="text/plain",
            )

        # Combined package
        package = f"""GENERATED: {datetime.now():%Y-%m-%d %H:%M}
GRADE: {target_grade}
MODEL: {model}

ORIGINAL
--------
{input_text}

ADAPTED
-------
{st.session_state.adapted_text}

{"QUESTIONS" if st.session_state.questions else ""}
{"---------" if st.session_state.questions else ""}
{st.session_state.questions if st.session_state.questions else ""}
"""
        col_z.download_button(
            "Download complete package",
            data=package,
            file_name=f"package_{target_grade}_{datetime.now():%Y%m%d_%H%M}.txt",
            mime="text/plain",
        )

# ------- ANALYTICS TAB -------
with tab_analytics:
    st.markdown("#### Text Analytics")
    if st.session_state.adapted_text and input_text.strip():
        orig = calculate_readability_metrics(input_text)
        adap = calculate_readability_metrics(st.session_state.adapted_text)
        if orig and adap:
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(
                f"""<div class="metric-card">
                    <div class="metric-value">{orig["word_count"]} → {adap["word_count"]}</div>
                    <div class="metric-label">Words</div>
                </div>""",
                unsafe_allow_html=True,
            )
            col2.markdown(
                f"""<div class="metric-card">
                    <div class="metric-value">{orig["avg_sentence_length"]} → {adap["avg_sentence_length"]}</div>
                    <div class="metric-label">Avg. Sent. Length</div>
                </div>""",
                unsafe_allow_html=True,
            )
            col3.markdown(
                f"""<div class="metric-card">
                    <div class="metric-value">{orig["reading_ease"]} → {adap["reading_ease"]}</div>
                    <div class="metric-label">Flesch Ease</div>
                </div>""",
                unsafe_allow_html=True,
            )
            reduction = round((1 - adap["word_count"] / orig["word_count"]) * 100)
            col4.markdown(
                f"""<div class="metric-card">
                    <div class="metric-value">{reduction}%</div>
                    <div class="metric-label">Complexity ↓</div>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.write("Adapt a text first to see analytics.")

# ------- HISTORY TAB -------
with tab_history:
    st.markdown("#### Adaptation History")
    history = st.session_state.history
    if history:
        # Download PDF
        pdf_bytes = generate_history_pdf(history)
        if pdf_bytes:
            st.download_button(
                "Download history (PDF)",
                data=pdf_bytes,
                file_name=f"history_{datetime.now():%Y%m%d_%H%M}.pdf",
                mime="application/pdf",
            )
        else:
            st.caption("PDF generation not available (ReportLab missing).")

        for item in reversed(history[-10:]):  # Show last 10
            with st.expander(f"{item['timestamp']} — {item['grade']}"):
                st.write("**Original preview**:", item["original"])
                st.write("**Adapted preview**:", item["adapted"])
    else:
        st.write("No adaptations yet. Your history will appear here.")
