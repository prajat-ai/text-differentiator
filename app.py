import streamlit as st
import openai

# Use the OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Text Differentiator", layout="centered")
st.title("📚 Text Differentiator")
st.markdown("Help students by simplifying text to a chosen reading level.")

grade_level = st.sidebar.selectbox(
    "Select Grade Level:",
    ["Kindergarten", "1st Grade", "2nd Grade", "3rd Grade", "4th Grade", "5th Grade", 
     "6th Grade", "7th Grade", "8th Grade", "High School"]
)

input_text = st.text_area("Enter the original text you'd like to simplify:", height=200)

if st.button("Simplify Text"):
    if not input_text.strip():
        st.warning("Please enter some text.")
    else:
        with st.spinner("Simplifying text..."):
            prompt = (
                f"Rewrite the following text so it is understandable by a {grade_level} student. "
                f"Keep the meaning but simplify the vocabulary and sentence structure:\n\n"
                f"{input_text}"
            )
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant who rewrites complex text for students at different reading levels."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                simplified_text = response['choices'][0]['message']['content']
                st.success("Here is the simplified version:")
                st.text_area("Simplified Text", simplified_text, height=200)
            except Exception as e:
                st.error(f"Error: {e}")
