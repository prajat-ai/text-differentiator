import os
import streamlit as st
from openai import OpenAI, OpenAIError

# ---------- Configuration ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY not found. "
             "Set it in your environment or Streamlit secrets.", icon="🚫")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Grade / Lexile metadata ----------
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
        "Use very basic words and very short sentences focused on concrete, "
        "everyday concepts. Repetition for clarity and rhythm is fine.",
    "1st Grade":
        "Use simple sentences with common, easy words. Keep ideas literal and "
        "concrete, tied to familiar objects and daily activities.",
    "2nd Grade":
        "Use slightly longer yet still straightforward sentences. Introduce a few "
        "new vocabulary words, providing context or brief explanations.",
    "3rd Grade":
        "Mix simple and compound sentences. Add more detail and a few challenging "
        "words, but explain them through context or easy definitions.",
    "4th Grade":
        "Include some complex sentences alongside simpler ones. Introduce academic "
        "vocabulary but define or rephrase difficult terms. Concepts may be a bit "
        "more abstract but must be clearly explained.",
    "5th Grade":
        "Use richer vocabulary and more complex sentence structures. Introduce new "
        "academic terms, defining any advanced words in simpler language.",
    "6th Grade":
        "Middle-school level: more complex sentences and specific vocabulary. "
        "Assume some prior knowledge, but clarify tough or uncommon terms.",
    "7th Grade":
        "Use varied sentence lengths and structures. Incorporate advanced "
        "vocabulary and some abstract ideas, giving concrete examples or "
        "explanations for difficult concepts.",
    "8th Grade":
        "Mostly complex sentences with advanced vocabulary typical of 8th grade. "
        "Clarify any particularly challenging concepts through context.",
    "9th Grade":
        "High-school language with vocabulary suited to 9th graders. Include some "
        "challenging words and nuanced concepts, but avoid jargon overload.",
    "10th Grade":
        "Use sophisticated sentences and vocabulary appropriate for 10th grade. "
        "Introduce nuance and subtlety, ensuring difficult concepts remain clear.",
    "11th Grade":
        "Use advanced vocabulary and complex sentence structures. Technical or "
        "literary terms are fine, but provide brief context so a struggling reader "
        "can follow.",
    "12th Grade":
        "Use fully mature high-school (pre-college) language and concepts. Include "
        "complex sentences and advanced vocabulary, giving context for any highly "
        "advanced terms or references.",
}

# ---------- UI ----------
st.set_page_config(page_title="Text Differentiator", page_icon="📚", layout="wide")
st.title("📚 Text Differentiator for Special-Education Teachers")

with st.sidebar:
    st.header("Settings")
    GRADES = list(LEXILE_LIMITS.keys())
    target_grade = st.selectbox("Target grade level", GRADES, index=0)
    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.05)
    model = st.selectbox("Model",
                         ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                         index=0)
    st.markdown("---")
    st.caption("Your key never leaves Streamlit’s secure back-end.")

input_text = st.text_area(
    "Paste the passage you want adapted:",
    height=300,
    placeholder="Enter or paste any text here…"
)

submit = st.button("🔄 Adapt Text", type="primary")
generate_questions = st.checkbox("🧠 Generate Comprehension Questions")

# ---------- Prompt builder ----------
def build_system_prompt(grade: str) -> str:
    """Return the complete system prompt string, with Lexile ceilings."""
    def line(g):
        limit = LEXILE_LIMITS[g]
        desc = GRADE_DESCRIPTIONS[g]
        return (f"{g}: {desc} "
                f"You cannot use a word over **{limit} Lexile** unless it is "
                f"critical to the translation.")

    guidelines = "\n".join(line(g) for g in GRADES)

    return f"""
You are an educational content specialist with expertise in simplifying texts
for K–12 students across different reading levels and special-education needs.

TASK
-----
Rewrite the user-provided passage **so that a student at reading grade level
{grade} can easily understand it**, while preserving the original structure
(heading order, paragraphs, blank lines, bullet/number lists, bold/italics).

GENERAL RULES
1. Maintain original sequence and formatting.
2. Adjust vocabulary, sentence length, and complexity according to the grade.
3. Apply special-education accommodations:
   • Break long sentences into shorter ones.  
   • Chunk information with bullets or numbered lists.  
   • Avoid unexplained idioms or jargon.  
   • Provide brief definitions or synonyms in context.  
   • Keep paragraphs short and focused.  
4. Age-appropriate tone: simple language but never childish for older students.

GRADE-LEVEL ADAPTATION GUIDELINES
---------------------------------
{guidelines}

Respond with *only* the adapted passage in Markdown—no extra commentary.
"""

# ---------- OpenAI helpers ----------
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


def generate_comprehension_questions(text: str, grade: str) -> str:
    prompt = f"""
You are an educator creating comprehension questions **for a student who reads
at {grade} level**.

Write 3 to 5 numbered questions about the passage below.
• Use language and vocabulary appropriate for {grade}.  
• Mix literal (who/what/where) and inferential (why/how) questions.  
• Do **not** include answers.  
Return only the list of questions, in Markdown.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.5,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"Error generating questions: {e}"

# ---------- Main action ----------
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

    st.subheader("✅ Adapted Text")
    st.markdown(adapted_text)

    if generate_questions:
        with st.spinner("Generating questions…"):
            questions = generate_comprehension_questions(adapted_text, target_grade)
        st.subheader("🧠 Comprehension Questions")
        st.markdown(questions)

    st.download_button(
        label="💾 Download as .txt",
        data=adapted_text,
        file_name=f"adapted_{target_grade.replace(' ', '_')}.txt",
        mime="text/plain",
    )
