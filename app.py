import os
import streamlit as st
from openai import OpenAI, OpenAIError

# ────────── Configuration ──────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error(
        "OPENAI_API_KEY not found. "
        "Set it in your environment variables or Streamlit secrets.",
        icon=":no_entry_sign:",
    )
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# ────────── Grade / Lexile metadata ──────────
LEXILE_LIMITS = {
    "Kindergarten": 220,
    "1st Grade":    500,
    "2nd Grade":    620,
    "3rd Grade":    790,
    "4th Grade":    910,
    "5th Grade":    980,
    "6th Grade":    1040,
    "7th Grade":    1160,
    "8th Grade":    1160,
    "9th Grade":    1360,
    "10th Grade":   1360,
    "11th Grade":   1360,
    "12th Grade":   1360,
}

GRADE_DESCRIPTIONS = {
    "Kindergarten":
        "Use VERY VERY simple words. The level a kindergartener could understand. Lexile score SHOULD NOT exceed 220. Keep the main concepts in tact. Use short sentences.",
    "1st Grade":
        "Use simple sentences with common, easy words focused on daily activities.",
    "2nd Grade":
        "Use slightly longer sentences and introduce a few new words with context clues.",
    "3rd Grade":
        "Mix simple and compound sentences, adding a few challenging words explained in context.",
    "4th Grade":
        "Introduce some complex sentences and academic vocabulary with brief explanations.",
    "5th Grade":
        "Use richer vocabulary and more complex sentences; define any tough terms briefly.",
    "6th Grade":
        "Use middle-school–level vocabulary and varied sentence structures; clarify uncommon terms.",
    "7th Grade":
        "Use advanced vocabulary and sentence variety; give examples for abstract ideas.",
    "8th Grade":
        "Mostly complex sentences and advanced vocabulary typical of 8th grade; clarify challenges.",
    "9th Grade":
        "High-school language with nuanced concepts while avoiding excessive jargon.",
    "10th Grade":
        "Sophisticated sentences and vocabulary appropriate for 10th grade; keep concepts clear.",
    "11th Grade":
        "Advanced vocabulary and complex sentences with brief context for technical terms.",
    "12th Grade":
        "Mature pre-college language and concepts, with context for any highly advanced terms.",
}

GRADES = list(LEXILE_LIMITS.keys())

# ────────── UI layout ──────────
st.set_page_config(page_title="Text Differentiator", page_icon=":books:", layout="wide")
st.title(":books: Text Differentiator for Special-Education Teachers")

with st.sidebar:
    st.header("Settings")
    target_grade = st.selectbox("Target grade level", GRADES, index=0)
    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.05)
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
    )
    generate_questions = st.checkbox(":brain: Generate comprehension questions")
    st.markdown("---")
    st.caption("Your API key never leaves Streamlit’s secure back-end.")

# Two vertical “bubbles” (side-by-side columns)
col_input, col_output = st.columns(2, gap="large")

with col_input:
    st.subheader("✏️ Original Text")
    input_text = st.text_area(
        "Paste the passage you want adapted:",
        key="input_text",
        height=420,
        placeholder="Enter or paste any text here…",
    )
    submit = st.button(":arrows_counterclockwise: Adapt Text", type="primary")

with col_output:
    st.subheader("✅ Adapted Text")
    # Reserve space to show adapted text later
    adapted_container = st.empty()

# ────────── Prompt builder ──────────
def build_system_prompt(grade: str) -> str:
    """Return the complete system prompt string, including strict sentence-matching
    and Lexile ceilings."""
    def line(g):
        limit = LEXILE_LIMITS[g]
        desc = GRADE_DESCRIPTIONS[g]
        return (
            f"{g}: {desc} "
            f"You cannot use a word over **{limit} Lexile** unless it is critical."
        )

    guidelines = "\n".join(line(g) for g in GRADES)

    return f"""
You are an educational content specialist who rewrites passages for K-12 students
while preserving structure **exactly**.

TASK
-----
Rewrite the user passage so that a student at **{grade}** reading level can
understand it.

CRITICAL RULES
1. **Sentence-for-sentence parity** – keep the **exact same number of sentences
   in the same order**; do not split, merge, add, or delete sentences.
2. Maintain original paragraph breaks and line spacing.
3. Output must be paragraph prose – **NO bullet points whatsoever**.
4. Vocabulary, sentence length, and complexity must align with {grade} and must
   not exceed its Lexile limit.
5. Provide brief in-sentence definitions or synonyms if a difficult word is
   unavoidable.
6. Age-appropriate tone: simpler words yet respectful.

GRADE-LEVEL ADAPTATION GUIDELINES
---------------------------------
{guidelines}

Return **only** the adapted passage in Markdown – no extra text.
"""

# ────────── OpenAI helpers ──────────
def adapt_text(text: str, grade: str) -> str:
    prompt = build_system_prompt(grade)
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip()

def generate_comprehension_qs(text: str, grade: str) -> str:
    prompt = f"""
You are an educator creating 3-5 comprehension questions for a student who
reads at **{grade}** level.

Guidelines:
• Mix who/what/where (literal) and why/how (inferential) questions.
• Use vocabulary appropriate for {grade}.
• Do **not** include answers; number each question.

Return only the list of questions in Markdown.
"""
    response = client.chat.completions.create(
        model=model,
        temperature=0.5,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip()

# ────────── Main action ──────────
if submit:
    if not input_text.strip():
        st.warning("Please enter some text first.")
        st.stop()

    with st.spinner("Adapting text…"):
        try:
            adapted_text = adapt_text(input_text, target_grade)
        except OpenAIError as e:
            st.error(f"OpenAI error: {e}")
            st.stop()

    # Display adapted text in the output “bubble”
    adapted_container.text_area(
        label="",
        value=adapted_text,
        height=420,
        key="adapted_text",
    )

    # Optional comprehension questions
    if generate_questions:
        with st.spinner("Generating questions…"):
            try:
                qs = generate_comprehension_qs(adapted_text, target_grade)
            except OpenAIError as e:
                qs = f"Error generating questions: {e}"

        st.subheader(":brain: Comprehension Questions")
        st.markdown(qs)

    # Download button
    st.download_button(
        label=":floppy_disk: Download adapted text",
        data=adapted_text,
        file_name=f"adapted_{target_grade.replace(' ', '_')}.txt",
        mime="text/plain",
    )
