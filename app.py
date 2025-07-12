import os
import streamlit as st
from openai import OpenAI, OpenAIError
from datetime import datetime
import json
import re
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# ---------- Configuration ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY not found. Set it in your environment or Streamlit secrets.", icon="🚫")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="Text Differentiator Pro", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Apple-style CSS with Dark Mode Support ----------
st.markdown("""
<style>
    /* Import SF Pro font (fallback to system fonts) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    }
    
    /* CSS Variables for Light/Dark Mode */
    :root {
        --bg-primary: #f5f5f7;
        --bg-secondary: #ffffff;
        --bg-tertiary: #f0f9ff;
        --text-primary: #1d1d1f;
        --text-secondary: #86868b;
        --border-color: #d2d2d7;
        --border-light: #e5e5e7;
        --accent-blue: #007aff;
        --accent-green: #34c759;
        --accent-orange: #ff9500;
        --shadow: rgba(0,0,0,0.04);
        --scrollbar-bg: #c7c7cc;
        --scrollbar-hover: #aeaeb2;
    }
    
    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #000000;
            --bg-secondary: #1c1c1e;
            --bg-tertiary: #2c2c2e;
            --text-primary: #ffffff;
            --text-secondary: #98989d;
            --border-color: #38383a;
            --border-light: #48484a;
            --shadow: rgba(255,255,255,0.04);
            --scrollbar-bg: #48484a;
            --scrollbar-hover: #636366;
        }
    }
    
    /* Main App Background */
    .stApp {
        background: var(--bg-primary);
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none;}
    header {visibility: hidden;}
    
    /* Remove tab navigation */
    .stTabs {
        display: none !important;
    }
    
    /* Header Styles */
    .hero-section {
        text-align: center;
        padding: 3rem 0 2rem 0;
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border-bottom: 1px solid var(--border-color);
        margin: -3rem -3rem 2rem -3rem;
    }
    
    .hero-title {
        font-size: 56px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.003em;
        margin-bottom: 0.5rem;
        line-height: 1.1;
    }
    
    .hero-subtitle {
        font-size: 21px;
        color: var(--text-secondary);
        font-weight: 400;
        margin-bottom: 2rem;
        line-height: 1.4;
    }
    
    /* Card Container */
    .card-container {
        background: var(--bg-secondary);
        border-radius: 18px;
        box-shadow: 0 4px 6px var(--shadow);
        padding: 32px;
        margin-bottom: 24px;
        border: 1px solid var(--border-light);
    }
    
    /* Text Display Containers */
    .text-comparison-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        margin-top: 24px;
    }
    
    .text-display-box {
        background: var(--bg-tertiary);
        border-radius: 12px;
        padding: 24px;
        height: 500px;
        overflow-y: auto;
        border: 1px solid var(--border-color);
        position: relative;
    }
    
    .text-display-box::-webkit-scrollbar {
        width: 14px;
    }
    
    .text-display-box::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .text-display-box::-webkit-scrollbar-thumb {
        background: var(--scrollbar-bg);
        border-radius: 100px;
        border: 4px solid var(--bg-tertiary);
    }
    
    .text-display-box::-webkit-scrollbar-thumb:hover {
        background: var(--scrollbar-hover);
    }
    
    .text-label {
        font-size: 17px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .text-content {
        font-size: 15px;
        line-height: 1.6;
        color: var(--text-primary);
        white-space: pre-wrap;
    }
    
    /* Original text styling */
    .original-text-box {
        background: var(--bg-tertiary);
    }
    
    .original-label {
        color: var(--accent-blue);
    }
    
    /* Adapted text styling */
    .adapted-text-box {
        background: var(--bg-tertiary);
        border: 1px solid var(--accent-green);
    }
    
    .adapted-label {
        color: var(--accent-green);
    }
    
    /* Input Text Area Custom Styling */
    .stTextArea textarea {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 15px;
        line-height: 1.5;
        transition: all 0.2s ease;
        color: var(--text-primary);
    }
    
    .stTextArea textarea:focus {
        border-color: var(--accent-blue);
        box-shadow: 0 0 0 3px rgba(0,122,255,0.1);
        outline: none;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding: 2rem 1rem;
    }
    
    /* Sidebar Headers */
    .sidebar-header {
        font-size: 19px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Select Boxes */
    .stSelectbox label {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-secondary);
        margin-bottom: 4px;
    }
    
    .stSelectbox > div > div {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 15px;
        color: var(--text-primary);
    }
    
    /* Buttons */
    .stButton button {
        background: var(--accent-blue);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-size: 15px;
        font-weight: 500;
        transition: all 0.2s ease;
        min-height: 40px;
    }
    
    .stButton button:hover {
        background: #0056d6;
        transform: scale(0.98);
    }
    
    /* Secondary Button */
    button[kind="secondary"] {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }
    
    button[kind="secondary"]:hover {
        background: var(--border-light);
    }
    
    /* Download Button */
    .stDownloadButton button {
        background: var(--accent-green);
        color: white;
        border-radius: 8px;
        padding: 8px 20px;
        font-size: 15px;
        font-weight: 500;
    }
    
    .stDownloadButton button:hover {
        background: #248a3d;
    }
    
    /* Comprehension Questions Box */
    .questions-container {
        background: var(--bg-tertiary);
        border: 1px solid var(--accent-orange);
        border-radius: 12px;
        padding: 24px;
        margin-top: 24px;
    }
    
    .questions-header {
        font-size: 19px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .questions-content {
        font-size: 15px;
        line-height: 1.8;
        color: var(--text-primary);
    }
    
    /* Metrics Cards */
    .metric-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    
    .metric-label {
        font-size: 13px;
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    /* Info Box */
    .info-box {
        background: var(--bg-tertiary);
        border: 1px solid var(--accent-blue);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 16px 0;
        font-size: 14px;
        color: var(--accent-blue);
    }
    
    /* Success Message */
    .success-box {
        background: var(--bg-tertiary);
        border: 1px solid var(--accent-green);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 16px 0;
        font-size: 14px;
        color: var(--accent-green);
    }
    
    /* History Section */
    .history-container {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 24px;
        margin-top: 24px;
        border: 1px solid var(--border-color);
    }
    
    /* Loading Animation */
    .stSpinner > div {
        border-color: var(--accent-blue);
    }
    
    /* Checkbox styling */
    .stCheckbox label {
        color: var(--text-primary) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        color: var(--text-primary) !important;
        background: var(--bg-tertiary) !important;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .text-comparison-container {
            grid-template-columns: 1fr;
        }
        
        .hero-title {
            font-size: 40px;
        }
        
        .hero-subtitle {
            font-size: 18px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------- Helper Functions ----------
def calculate_readability_metrics(text):
    """Calculate various readability metrics for the text."""
    sentences = re.split(r'[.!?]+', text)
    words = text.split()
    syllables = sum([count_syllables(word) for word in words])
    
    if len(sentences) > 0 and len(words) > 0:
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = syllables / len(words)
        flesch_reading_ease = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "reading_ease": round(flesch_reading_ease, 1)
        }
    return None

def count_syllables(word):
    """Count syllables in a word."""
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count == 0:
        count += 1
    return count

def get_grade_specific_guidelines(grade):
    """Return detailed guidelines for each grade level."""
    guidelines = {
        "Kindergarten": {
            "sentence_length": "3-5 words",
            "vocabulary": "Basic sight words, CVC words",
            "complexity": "Simple subject-verb sentences",
            "concepts": "Concrete, everyday objects and actions"
        },
        "1st Grade": {
            "sentence_length": "5-8 words",
            "vocabulary": "Common sight words, simple descriptive words",
            "complexity": "Simple sentences with basic conjunctions",
            "concepts": "Familiar experiences, basic cause-effect"
        },
        "2nd Grade": {
            "sentence_length": "8-12 words",
            "vocabulary": "Expanding sight words, simple multi-syllable words",
            "complexity": "Compound sentences with 'and', 'but'",
            "concepts": "Simple comparisons, basic sequencing"
        },
        "3rd Grade": {
            "sentence_length": "10-15 words",
            "vocabulary": "Academic vocabulary with context clues",
            "complexity": "Complex sentences with dependent clauses",
            "concepts": "Abstract ideas with concrete examples"
        },
        "4th Grade": {
            "sentence_length": "12-18 words",
            "vocabulary": "Subject-specific terms, multiple meanings",
            "complexity": "Varied sentence structures",
            "concepts": "Cause-effect relationships, basic inference"
        },
        "5th Grade": {
            "sentence_length": "15-20 words",
            "vocabulary": "Advanced vocabulary, figurative language",
            "complexity": "Sophisticated sentence variety",
            "concepts": "Abstract concepts, critical thinking"
        },
    }
    
    # Default for grades 6-12
    default = {
        "sentence_length": "Varies widely",
        "vocabulary": "Grade-appropriate academic vocabulary",
        "complexity": "Full range of sentence structures",
        "concepts": "Abstract and complex ideas"
    }
    
    return guidelines.get(grade, default)

def generate_history_pdf(history):
    """Generate a PDF document of the user's adaptation history."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#007AFF'),
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add title
    elements.append(Paragraph("Text Adaptation History", title_style))
    elements.append(Spacer(1, 20))
    
    # Add generation date
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Create table data
    data = [['Date/Time', 'Grade Level', 'Original Preview', 'Adapted Preview']]
    
    for item in history:
        data.append([
            item['timestamp'],
            item['grade'],
            item['original'][:50] + "...",
            item['adapted'][:50] + "..."
        ])
    
    # Create table
    table = Table(data, colWidths=[1.5*inch, 1.5*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007AFF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f7')]),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------- Main App ----------
# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Text Differentiator Pro</h1>
    <p class="hero-subtitle">Transform any text for special education students with AI-powered adaptation</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'adapted_text' not in st.session_state:
    st.session_state.adapted_text = ""
if 'questions' not in st.session_state:
    st.session_state.questions = ""
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar Configuration
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    # Grade Selection
    grades = [
        "Kindergarten", "1st Grade", "2nd Grade", "3rd Grade", "4th Grade",
        "5th Grade", "6th Grade", "7th Grade", "8th Grade",
        "9th Grade", "10th Grade", "11th Grade", "12th Grade"
    ]
    target_grade = st.selectbox("Target Grade Level", grades, index=2)
    
    # Model Settings
    st.markdown("---")
    st.markdown('<div class="sidebar-header">🤖 AI Settings</div>', unsafe_allow_html=True)
    
    model = st.selectbox(
        "AI Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
        help="GPT-4 provides best results for complex adaptations"
    )
    
    # Special Education Options
    st.markdown("---")
    st.markdown('<div class="sidebar-header">♿ Accessibility Options</div>', unsafe_allow_html=True)
    
    use_simple_vocab = st.checkbox("Use simplified vocabulary", value=True)
    add_definitions = st.checkbox("Add in-text definitions", value=True)
    use_short_paragraphs = st.checkbox("Use shorter paragraphs", value=True)
    add_visual_breaks = st.checkbox("Add visual breaks", value=False)
    
    # Output Options
    st.markdown("---")
    st.markdown('<div class="sidebar-header">📝 Output Options</div>', unsafe_allow_html=True)
    
    generate_questions = st.checkbox("Generate comprehension questions", value=True)
    generate_vocabulary = st.checkbox("Generate vocabulary list", value=False)
    generate_summary = st.checkbox("Generate summary", value=False)
    
    # History PDF Download
    if st.session_state.history:
        st.markdown("---")
        st.markdown('<div class="sidebar-header">📚 History</div>', unsafe_allow_html=True)
        
        pdf_buffer = generate_history_pdf(st.session_state.history)
        st.download_button(
            label="📄 Download History (PDF)",
            data=pdf_buffer,
            file_name=f"adaptation_history_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )

# Main Content Area - No tabs, just direct content
# Input Section
st.markdown('<div class="card-container">', unsafe_allow_html=True)
st.markdown("### 📝 Input Text")

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown('<div class="info-box">💡 Tip: Paste any educational content, article, or textbook passage below</div>', unsafe_allow_html=True)

input_text = st.text_area(
    "Text to adapt",
    height=200,
    placeholder="Paste your text here...",
    help="The text will be adapted to match the reading level and comprehension abilities of your target grade."
)

col1, col2, col3 = st.columns([2, 2, 6])
with col1:
    adapt_button = st.button("🔄 Adapt Text", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ Clear All", type="secondary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Clear functionality
if clear_button:
    st.session_state.adapted_text = ""
    st.session_state.questions = ""
    st.rerun()

# Process adaptation
if adapt_button and input_text:
    with st.spinner("🤖 Adapting text for " + target_grade + "..."):
        try:
            # Create comprehensive prompt
            system_prompt = f"""You are an expert special education content specialist tasked with adapting texts for diverse learners.

TARGET AUDIENCE: {target_grade} students with various learning needs including:
- Reading difficulties (dyslexia, processing disorders)
- Attention challenges (ADHD)
- English language learners
- Cognitive differences

ADAPTATION REQUIREMENTS:
1. Grade Level Guidelines for {target_grade}:
   - Sentence length: {get_grade_specific_guidelines(target_grade)['sentence_length']}
   - Vocabulary: {get_grade_specific_guidelines(target_grade)['vocabulary']}
   - Complexity: {get_grade_specific_guidelines(target_grade)['complexity']}
   - Concepts: {get_grade_specific_guidelines(target_grade)['concepts']}

2. Special Education Accommodations:
   {'- Use very simple, common vocabulary only' if use_simple_vocab else ''}
   {'- Define difficult words in parentheses immediately after use' if add_definitions else ''}
   {'- Break into short paragraphs (2-3 sentences max)' if use_short_paragraphs else ''}
   {'- Add line breaks between main ideas for visual clarity' if add_visual_breaks else ''}
   - Use clear topic sentences
   - Maintain logical flow with transition words
   - Replace idioms and figurative language with literal expressions
   - Use active voice whenever possible
   - Include concrete examples for abstract concepts

3. Content Preservation:
   - Keep all key information from the original
   - Maintain the original message and purpose
   - Preserve important facts and details
   - Ensure educational value is retained

OUTPUT FORMAT:
- Use clear, simple markdown formatting
- Bold key terms that students should remember
- Use bullet points for lists
- Keep paragraphs short and focused
- Return ONLY the adapted text, no commentary"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please adapt this text for {target_grade} students:\n\n{input_text}"}
            ]
            
            response = client.chat.completions.create(
                model=model,
                temperature=0.3,  # Fixed temperature for consistency
                messages=messages,
                max_tokens=2000
            )
            
            st.session_state.adapted_text = response.choices[0].message.content.strip()
            
            # Add to history
            st.session_state.history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "grade": target_grade,
                "original": input_text[:100] + "...",
                "adapted": st.session_state.adapted_text[:100] + "..."
            })
            
            # Generate questions if requested
            if generate_questions:
                with st.spinner("🧠 Creating comprehension questions..."):
                    q_prompt = f"""Create 5-7 comprehension questions for {target_grade} students based on this adapted text.

Include:
1. Two literal comprehension questions (who, what, where, when)
2. Two inferential questions (why, how)
3. One vocabulary question
4. One critical thinking question
5. One personal connection question

Make questions appropriate for {target_grade} reading level.
Format as a numbered list."""
                    
                    q_messages = [
                        {"role": "system", "content": "You are a special education teacher creating accessible comprehension questions."},
                        {"role": "user", "content": f"{q_prompt}\n\nText:\n{st.session_state.adapted_text}"}
                    ]
                    
                    q_response = client.chat.completions.create(
                        model=model,
                        temperature=0.5,
                        messages=q_messages
                    )
                    
                    st.session_state.questions = q_response.choices[0].message.content.strip()
            
            st.markdown('<div class="success-box">✅ Text successfully adapted for ' + target_grade + '</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Display Results
if st.session_state.adapted_text:
    st.markdown("---")
    st.markdown("### 📖 Text Comparison")
    
    # Create side-by-side comparison
    st.markdown(f"""
    <div class="text-comparison-container">
        <div class="text-display-box original-text-box">
            <div class="text-label original-label">📄 Original Text</div>
            <div class="text-content">{input_text}</div>
        </div>
        <div class="text-display-box adapted-text-box">
            <div class="text-label adapted-label">✨ Adapted for {target_grade}</div>
            <div class="text-content">{st.session_state.adapted_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display questions if generated
    if generate_questions and st.session_state.questions:
        st.markdown(f"""
        <div class="questions-container">
            <div class="questions-header">🧠 Comprehension Questions</div>
            <div class="questions-content">{st.session_state.questions.replace(chr(10), '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Analytics Section
    st.markdown("---")
    st.markdown("### 📊 Text Analytics")
    
    # Calculate metrics
    original_metrics = calculate_readability_metrics(input_text)
    adapted_metrics = calculate_readability_metrics(st.session_state.adapted_text)
    
    if original_metrics and adapted_metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{original_metrics['word_count']} → {adapted_metrics['word_count']}</div>
                <div class="metric-label">Word Count</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{original_metrics['avg_sentence_length']} → {adapted_metrics['avg_sentence_length']}</div>
                <div class="metric-label">Avg. Sentence Length</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{original_metrics['reading_ease']} → {adapted_metrics['reading_ease']}</div>
                <div class="metric-label">Reading Ease Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            reduction = round((1 - adapted_metrics['word_count'] / original_metrics['word_count']) * 100)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{reduction}%</div>
                <div class="metric-label">Complexity Reduction</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Download Options
    st.markdown("---")
    st.markdown("### 💾 Export Options")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.download_button(
            label="📄 Adapted Text",
            data=st.session_state.adapted_text,
            file_name=f"adapted_{target_grade.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )
    
    with col2:
        if st.session_state.questions:
            st.download_button(
                label="🧠 Questions",
                data=st.session_state.questions,
                file_name=f"questions_{target_grade.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
    
    with col3:
        complete_doc = f"""TEXT ADAPTATION PACKAGE
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Target Grade: {target_grade}
Model: {model}

ORIGINAL TEXT:
--------------
{input_text}

ADAPTED TEXT:
-------------
{st.session_state.adapted_text}

{'COMPREHENSION QUESTIONS:' if st.session_state.questions else ''}
{'------------------------' if st.session_state.questions else ''}
{st.session_state.questions if st.session_state.questions else ''}
"""
        st.download_button(
            label="📦 Complete Package",
            data=complete_doc,
            file_name=f"complete_{target_grade.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

# History Section
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📚 Recent Adaptations")
    st.markdown('<div class="history-container">', unsafe_allow_html=True)
    
    for i, item in enumerate(reversed(st.session_state.history[-5:])):  # Show last 5
        with st.expander(f"{item['timestamp']} - {item['grade']}"):
            st.write("**Original preview:**", item['original'])
            st.write("**Adapted preview:**", item['adapted'])
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); font-size: 13px; margin-top: 3rem;">
    <p>Built with ❤️ for Special Education Teachers | Powered by OpenAI</p>
</div>
""", unsafe_allow_html=True)
