import streamlit as st
import google.generativeai as genai
from weasyprint import HTML, CSS

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ReportGenie AI",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. HIDE STREAMLIT UI (The 5 Buttons) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stToolbar"] {visibility: hidden; display: none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 3. CUSTOM CSS (Visuals + White Text Fix) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        height: 3em;
        border-radius: 10px;
    }
    /* FIX: Force text to be black so it's visible in Dark Mode */
    .stTextArea>div>div>textarea {
        background-color: #f0f2f6;
        color: #000000; 
    }
    .report-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #e8f4f8;
        border-left: 5px solid #00a8e8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("🚨 API Key Missing. Please check your app settings.")
    st.stop()

# --- 5. BACKEND LOGIC ---
def get_prompt(style, user_text):
    sys_msg = "Role:Formatter. Action:Fix grammar,structure logic,expand brevity. Output:Raw Code only(No Markdown)."
    
    if style == "Simple":
        return f"{sys_msg} Mode:SIMPLE_HTML. Rules: Tags:<h1>(L1),<h2>(L2),<ul><li>(L3). Txt:Manual numbering. Bodyonly. Input: {user_text}"
    elif style == "Modern":
        return f"{sys_msg} Mode:CORP_HTML. Rules: Struct:Title(.title)->ExecSum->TOC(.toc)->H2->H3->Refs(Harvard). Data=<table>. Bodyonly. Input: {user_text}"
    elif style == "Academic":
        return f"{sys_msg} Mode:LATEX. Rules: Pkg:geometry,times,longtable,hyperref. Struct:Title,Abs,Sec,Ref. NO images. Input: {user_text}"

def generate_pdf(html_content, css_style):
    full_html = f"<html><head><style>{css_style}</style></head><body>{html_content}</body></html>"
    return HTML(string=full_html).write_pdf()

# --- 6. FRONTEND UI ---
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
st.markdown("Paste your rough notes, meeting transcripts, or messy data below.")

tab1, tab2 = st.tabs(["✍️ Input", "ℹ️ How it Works"])

with tab1:
    user_input = st.text_area(
        "Paste text here:", 
        height=300, 
        placeholder="Example: Q3 Revenue was 5M..."
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_btn = st.button("✨ Generate PDF Document")

with tab2:
    st.markdown("### How to use\n1. Paste Text\n2. Select Style\n3. Download PDF")

# --- 7. EXECUTION ---
if generate_btn:
    if not user_input:
        st.warning("⚠️ Please enter some text.")
    else:
        progress_text = "AI is reading your notes..."
        my_bar = st.progress(0, text=progress_text)

        try:
            # Step 1: Generate
            my_bar.progress(25, text="Structuring document logic...")
            prompt = get_prompt(mode, user_input)
            
            # UPDATED: Using 'latest' to avoid 404 errors
            model = genai.GenerativeModel('gemini-1.5-flash-latest') 
            response = model.generate_content(prompt)
            clean_output = response.text.replace("```html", "").replace("```latex", "").replace("```", "")
            
            # Step 2: Render
            my_bar.progress(75, text="Applying professional typography...")
            
            if mode == "Academic":
                my_bar.progress(100, text="Done!")
                st.markdown("### ✅ Academic Report Ready")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("⬇️ Download .tex File", clean_output, "report.tex", "text/plain")
                with c2:
                    st.code(clean_output, language="latex")
                    
            else: 
                if mode == "Simple":
                    css = "body { font-family: 'Times New Roman'; font-size: 12pt; margin: 2cm; } h1, h2 { font-weight: bold; } ul { padding-left: 20px; }"
                elif mode == "Modern":
                    css = "@page {margin: 2.5cm;} body {font-family: Helvetica, sans-serif; line-height: 1.6;} .title {color: #2c3e50; font-size: 24pt; border-bottom: 2px solid #2c3e50; text-align: center;}"
                
                pdf_data = generate_pdf(clean_output, css)
                my_bar.progress(100, text="Done!")
                st.balloons()
                st.success(f"Your **{mode}** report is ready!")
                st.download_button("📄 Download PDF", pdf_data, f"{mode.lower()}_report.pdf", "application/pdf", use_container_width=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")