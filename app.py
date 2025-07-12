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
    """Call OpenAI to rewrite `text` for grade level `grade`."""
    system_prompt = (
        "You are an educational content specialist. "
        f"Rewrite the user‑provided passage so that a student at reading "
        f"grade level {grade} can easily understand it. "
        "Keep the original meaning but adjust vocabulary and syntax. "
        "Respond with *only* the adapted passage—no extra commentary."
    )
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
