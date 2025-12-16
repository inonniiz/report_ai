import streamlit as st
import google.generativeai as genai
from weasyprint import HTML, CSS
import base64
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ReportGenie AI",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS & STYLING ---
st.markdown("""
    <style>
    /* Hide Streamlit Toolbar */
    [data-testid="stToolbar"] {visibility: hidden; display: none;}
    footer {visibility: hidden;}
    
    /* Custom Buttons */
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        height: 3em;
        border-radius: 10px;
    }
    
    /* Input Text Area - Black Text Fix */
    .stTextArea>div>div>textarea {
        background-color: #f0f2f6;
        color: #000000;
        caret-color: #000000; /* Blinking Cursor */
    }
    
    /* Preview Box Style */
    .preview-box {
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        color: #000000;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("🚨 API Key Missing. Please check your app settings.")
    st.stop()

# --- 4. BACKEND LOGIC (Your Custom Prompts) ---
def get_prompt(style, user_text):
    # STRICT SYSTEM PROMPT (The "Editor" Persona)
    sys_msg = """
    ROLE: You are a strict Copy Editor and Formatter.
    TASK: Fix grammar and spelling in the USER_INPUT. Apply formatting.
    NOTE: if users input AI-generated content and they forget to remove non-content part (e.g. here is your report...) remove it for them
    CRITICAL RULE: DO NOT ADD ANY NEW CONTENT. DO NOT SUMMARIZE. DO NOT ADD HEADERS/SECTIONS THAT ARE NOT IN THE INPUT.
    Output: Return only the raw code.
    """

    if style == "Simple":
        return f"""{sys_msg}
        MODE: SIMPLE (Format Only).
        INSTRUCTIONS:
        1. Keep the exact text structure.
        2. If a line looks like a header, make it <h1> or <h2>.
        3. If a line looks like a list item, make it <ul><li>.
        4. Otherwise, wrap in <p>.
        USER_INPUT:
        {user_text}"""
        
    elif style == "Modern":
        return f"""{sys_msg}
        MODE: MODERN (CSS Tags Only).
        INSTRUCTIONS:
        1. Wrap existing headers in <h2>.
        2. Wrap key numbers/metrics in <span class='highlight'>.
        3. If there is a table, format it as HTML <table>.
        4. if user don't have Table of Contents and Executive Summary, generate Table of Contents and Executive Summary (this bypass critical rule).
        5. Just format the provided text beautifully using the classes 'title' (if there is a clear main title) and 'highlight'.
        USER_INPUT:
        {user_text}"""
        
    elif style == "Academic":
        return f"""{sys_msg}
        MODE: LATEX (Source Only).
        INSTRUCTIONS:
        1. Use \\documentclass{{article}} with packages: geometry, times, longtable, hyperref.
        2. Convert the text to LaTeX. Use \\section for headers.
        3. Use 'longtable' for data.
        4. If user don't have Abstract and reference. Add an Abstract and References (leave blank if there's no reference at all) section (this bypass critical rule)
        USER_INPUT:
        {user_text}"""

def generate_pdf(html_content, css_style):
    full_html = f"<html><head><style>{css_style}</style></head><body>{html_content}</body></html>"
    return HTML(string=full_html).write_pdf()

def display_pdf(pdf_data):
    # Function to embed PDF in the app
    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- 5. FRONTEND UI ---
with st.sidebar:
    st.title("📑 ReportGenie")
    st.caption("AI-Powered Document Formatter")
    st.markdown("---")
    
    mode = st.radio(
        "Choose Report Style", 
        ["Simple", "Modern", "Academic"],
        captions=["Plain Text (Times New Roman)", "Corporate (McKinsey Style)", "LaTeX Source (Research)"]
    )
    
    st.markdown("---")
    st.success("System Status: Online")

st.header("Create Professional Reports Instantly")
# Updated Subtext as requested
st.markdown("Paste your rough notes, meeting transcripts, or AI-generated text below.")

tab1, tab2 = st.tabs(["✍️ Input", "ℹ️ How it Works"])

with tab1:
    user_input = st.text_area(
        "Paste text here:", 
        height=300, 
        placeholder="Example: Q3 Revenue was 5M, up 10% from last year..."
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_btn = st.button("✨ Generate PDF Document")

with tab2:
    st.markdown("### How to use\n1. Paste Text\n2. Select Style\n3. Watch AI Stream\n4. Preview & Download")

# --- 6. EXECUTION LOGIC ---
if generate_btn:
    if not user_input:
        st.warning("⚠️ Please enter some text.")
    else:
        # 1. DYNAMIC TIME CALCULATION
        word_count = len(user_input.split())
        est_time = round((word_count / 50) + 2) 
        if est_time < 2: est_time = 2
        
        status_container = st.empty()
        status_container.info(f"🚀 Processing {word_count} words... (Est. time: {est_time}s)")
        my_bar = st.progress(0)

        try:
            my_bar.progress(10, text="AI is reading...")
            
            prompt = get_prompt(mode, user_input)
            model = genai.GenerativeModel('gemini-2.5-flash') 
            
            # Request Streaming Response
            response_stream = model.generate_content(prompt, stream=True)
            
            # --- CRITICAL FIX: MANUAL TEXT ACCUMULATION ---
            accumulated_text = []

            def stream_parser(stream):
                for chunk in stream:
                    if chunk.text:
                        accumulated_text.append(chunk.text)
                        yield chunk.text

            # Container for the "Typing Effect"
            with st.expander("📝 AI Output Stream (Live Preview)", expanded=True):
                # We feed the generator to Streamlit, but ignore its return value
                st.write_stream(stream_parser(response_stream))
            
            # Re-assemble the full string manually from our list
            full_text = "".join(accumulated_text)
            # -----------------------------------------------

            my_bar.progress(80, text="Rendering PDF document...")
            
            # Clean up text
            clean_output = full_text.replace("```html", "").replace("```latex", "").replace("```", "")
            
            # 3. RENDER PDF & PREVIEW
            if mode == "Academic":
                my_bar.progress(100, text="Done!")
                status_container.success("✅ Generation Complete!")
                st.markdown("### Academic Source Code")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("⬇️ Download .tex File", clean_output, "report.tex", "text/plain")
                with c2:
                    st.code(clean_output, language="latex")
                    
            else: # HTML Modes
                if mode == "Simple":
                    css = "body { font-family: 'Times New Roman'; font-size: 12pt; margin: 2cm; } h1, h2 { font-weight: bold; } ul { padding-left: 20px; }"
                elif mode == "Modern":
                    css = "@page {margin: 2.5cm;} body {font-family: Helvetica, sans-serif; line-height: 1.6;} .title {color: #2c3e50; font-size: 24pt; border-bottom: 2px solid #2c3e50; text-align: center;} .toc {background:#f4f4f4; padding:15px; border-radius:5px;}"
                
                # Convert to PDF
                pdf_data = generate_pdf(clean_output, css)
                
                my_bar.progress(100, text="Done!")
                status_container.success(f"✅ Report Ready! ({est_time}s)")
                st.balloons()
                
                # 4. PDF PREVIEW
                st.markdown("### 📄 PDF Preview")
                display_pdf(pdf_data)
                
                st.download_button(
                    "⬇️ Download PDF File", 
                    pdf_data, 
                    f"{mode.lower()}_report.pdf", 
                    "application/pdf", 
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")