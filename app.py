import os
import streamlit as st
from openai import OpenAI, OpenAIError
# ---------- Configuration ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY not found. "
             "Set it in your environment or Streamlit secrets.", icon=":no_entry_sign:")
    st.stop()
client = OpenAI(api_key=OPENAI_API_KEY)
# ---------- UI ----------
st.set_page_config(page_title="Text Differentiator", page_icon=":books:", layout="wide")
st.title(":books: Text Differentiator for Special-Education Teachers")
with st.sidebar:
    st.header("Settings")
    grades = [
        "Kindergarten", "1st Grade", "2nd Grade", "3rd Grade", "4th Grade",
        "5th Grade", "6th Grade", "7th Grade", "8th Grade",
        "9th Grade", "10th Grade", "11th Grade", "12th Grade"
    ]
    target_grade = st.selectbox("Target grade level", grades, index=0)
    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.05)
    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    st.markdown("---")
    st.caption("Your key never leaves Streamlit’s secure back-end.")
input_text = st.text_area(
    "Paste the passage you want adapted:",
    height=300,
    placeholder="Enter or paste any text here…"
)
submit = st.button(":arrows_counterclockwise: Adapt Text", type="primary")
generate_questions = st.checkbox(":brain: Generate Comprehension Questions")
# ---------- OpenAI Helpers ----------
def adapt_text(text: str, grade: str) -> str:
    """Rewrite `text` for the specified grade, keeping original structure/format."""
    system_prompt = f"""
You are an educational content specialist with expertise in simplifying texts for K–12 students across different reading levels and special-education needs.
TASK
-----
Rewrite the user-provided passage **so that a student at reading grade level {grade} can easily understand it**.
RULES
1. **Preserve the original structure and formatting** \
   • Return the same paragraph format.
   • Maintain the same sequence of ideas
2. Adjust vocabulary, sentence length, and complexity to match grade-level guidelines below.
3. Apply special-education accommodations (shorter sentences, chunking, definitions in-context, no unexplained idioms).
4. Maintain an age-appropriate tone: simple language ≠ “baby talk” for older students.
5. Respond with *only* the adapted passage in Markdown—no extra commentary.
GRADE-LEVEL ADAPTATION GUIDELINES
---------------------------------
Kindergarten (Grade K): very basic words and short sentences; concrete ideas; repetition OK.
1st Grade: simple sentences; easy, literal vocabulary tied to daily life.
2nd Grade: slightly longer sentences; introduce a few new words with context clues.
3rd Grade: mix of simple/compound sentences; explain challenging words in context.
4th Grade: some complex sentences; introduce academic terms with definitions.
5th Grade: richer vocabulary; define advanced words in simpler language.
6th Grade: middle-school level; clarify uncommon terms; assume some prior knowledge.
7th Grade: varied structures; include abstract ideas with concrete examples.
8th Grade: mostly complex sentences; clarify difficult concepts via context.
9th–12th Grade: increasingly sophisticated language and concepts; provide brief context for advanced terms.
"""
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip()
def generate_comprehension_questions(text: str, grade: str) -> str:
    """Generate 3–5 comprehension questions written at `grade` reading level."""
    system_prompt = f"""
You are an educator creating comprehension questions **for a student who reads at {grade} level**.
TASK
-----
Write 3 to 5 numbered questions about the passage below.
• Use language and vocabulary appropriate for {grade}.
• Mix literal (who/what/where) and inferential (why/how) questions.
• Do **not** include answers.
Return only the list of questions, numbered, in Markdown.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"Error generating questions: {e}"
# ---------- Main Action ----------
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
    st.subheader(":white_check_mark: Adapted Text")
    st.markdown(adapted_text)
    # Generate comprehension questions if requested
    if generate_questions:
        with st.spinner("Generating questions…"):
            questions = generate_comprehension_questions(adapted_text, target_grade)
        st.subheader(":brain: Comprehension Questions")
        st.markdown(questions)
    # Download adapted passage
    st.download_button(
        label=":floppy_disk: Download as .txt",
        data=adapted_text,
        file_name=f"adapted_grade_{target_grade.replace(' ', '_')}.txt",
        mime="text/plain",
    )
