import os
import streamlit as st
from openai import OpenAI, OpenAIError

# -------------  Configuration -------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY not found. "
             "Set it in your environment or Streamlit secrets.", icon="🚫")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# -------------  UI -------------
st.set_page_config(page_title="Text Differentiator",
                   page_icon="📚", layout="wide")

st.title("📚 Text Differentiator for Special‑Education Teachers")

with st.sidebar:
    st.header("Settings")
    grades = []  # 1‑12
    grades.insert(0, "Kindergarten")
    grades.insert(1, "1st Grade")
    grades.insert(2, "2nd Grade")
    grades.insert(3, "3rd Grade")
    grades.insert(4, "4th Grade")
    grades.insert(5, "5th Grade")
    grades.insert(6, "6th Grade")
    grades.insert(7, "7th Grade")
    grades.insert(8, "8th Grade")
    grades.insert(9, "9th Grade")
    grades.insert(10, "10th Grade")
    grades.insert(11, "11th Grade")
    grades.insert(12, "12th Grade")
    target_grade = st.selectbox("Target grade level", grades, index=0)
    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.05)
    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    st.markdown("---")
    st.caption("Your key never leaves Streamlit’s secure back‑end.")

input_text = st.text_area(
    "Paste the passage you want adapted:",
    height=300,
    placeholder="Enter or paste any text here…"
)

submit = st.button("🔄 Adapt Text", type="primary")
generate_questions = st.checkbox("🧠 Generate Comprehension Questions")

# -------------  Back‑end call -------------
def adapt_text(text: str, grade: str) -> str:
    """Call OpenAI to rewrite `text` for the specified grade level using detailed adaptation guidelines."""

    system_prompt = f"""
You are an educational content specialist with expertise in simplifying texts for K–12 students across different reading levels and special education needs.

Your task: Rewrite the user-provided passage so that a student at reading grade level {grade} can easily understand it. Keep the original meaning but adjust the vocabulary, sentence structure, and complexity to suit that grade level.

Grade-Level Adaptation Guidelines:
Kindergarten (Grade K): Use very basic words and short, simple sentences. Focus on concrete, everyday concepts. It's okay to use repetition for clarity and rhythm.
1st Grade: Use simple sentences with common, easy words. Keep ideas literal and concrete, relating to familiar objects and daily activities.
2nd Grade: Use slightly longer but still straightforward sentences. Introduce a few new vocabulary words, providing context or brief explanations for support.
3rd Grade: Use a mix of simple and compound sentences. Include more detail and a few challenging words, but explain them through context or easy definitions so the meaning is clear.
4th Grade: Use some complex sentences along with simpler ones. Introduce academic vocabulary appropriate for this level, but define or rephrase difficult terms. Concepts can be a bit more abstract but should still be clearly explained.
5th Grade: Use more complex sentence structures and a richer vocabulary. You can include new academic terms, but ensure clarity by defining any advanced words in simpler language.
6th Grade: Use a middle-school reading level: more complex sentences and specific vocabulary. Assume the reader has some prior knowledge, but clarify tough concepts or uncommon terms as needed.
7th Grade: Use a variety of sentence lengths and structures. Incorporate some advanced vocabulary, and begin to include abstract ideas, providing concrete examples or explanations for difficult concepts.
8th Grade: Use mostly complex sentences and more advanced vocabulary typical of an 8th-grade level. Ensure any particularly challenging concepts are clarified through context or a simple restatement.
9th Grade: Use high school-level language with vocabulary suitable for 9th graders. Include some challenging words and more nuanced concepts, but keep the meaning clear by not overloading the text with jargon.
10th Grade: Use sophisticated sentences and vocabulary appropriate for 10th grade. You can introduce more nuance and subtlety in language. Ensure that any especially difficult concept is made understandable through additional context if necessary.
11th Grade: Use advanced vocabulary and complex sentence structures expected of an 11th-grade reader. It’s fine to include technical or literary terms, but provide context or brief explanations so a struggling reader can follow.
12th Grade: Use fully mature high school (pre-college) language and concepts. This includes complex sentences and advanced vocabulary appropriate for a 12th grader. Maintain clarity by offering context for any highly advanced terms or references.

Note: Always maintain an age-appropriate tone and content. For example, if you simplify a text for a teenage student who reads at a 3rd-grade level, use simple language but do not make the content babyish. The ideas and examples should be respectful of the student’s age or grade in school.

Special Accommodations for Clarity:
- Break down long sentences into shorter, clear sentences.
- Use bullet points or numbered lists when presenting steps, categories, or important points.
- Avoid idioms, figurative language, or jargon unless you plan to explain them.
- Provide brief definitions or synonyms for any difficult words in context.
- Keep paragraphs short and focused on one idea each.
- Highlight key points or terms by formatting them clearly (e.g., bold or underlined) if possible.

Respond with *only* the adapted passage—no extra commentary.
"""

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
    )
    return response.choices[0].message.content.strip()

def generate_comprehension_questions(text: str) -> str:
    """Generate 3–5 comprehension questions for the adapted passage."""
    prompt = (
        "Generate 3 to 5 comprehension questions based on the following adapted passage. "
        "Include a mix of literal and inferential questions appropriate for a student at the target reading level. "
        "Return only the list of questions, numbered."
    )
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.5,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"Error generating questions: {e}"

# -------------  Main action -------------
if submit:
    if not input_text.strip():
        st.warning("Please enter some text first.")
        st.stop()

    with st.spinner("Adapting text…"):
        try:
            adapted = adapt_text(input_text, target_grade)
        except OpenAIError as e:
            st.error(f"OpenAI error: {e}")
            st.stop()

    st.subheader("✅ Adapted Text")
    st.write(adapted)

    if generate_questions:
        st.subheader("🧠 Comprehension Questions")
    with st.spinner("Generating questions…"):
        questions = generate_comprehension_questions(adapted)
    st.markdown(questions)

    st.download_button(
        label="💾 Download as .txt",
        data=adapted,
        file_name=f"adapted_grade_{target_grade}.txt",
        mime="text/plain"
    )
