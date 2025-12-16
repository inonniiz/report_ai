import streamlit as st
import google.generativeai as genai
from weasyprint import HTML, CSS

# --- 1. PAGE CONFIGURATION (Browser Tab Title & Icon) ---
st.set_page_config(
    page_title="ReportGenie AI",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (To make the app look less "Streamlit-y") ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        height: 3em;
        border-radius: 10px;
    }
    .stTextArea>div>div>textarea {
        background-color: #f0f2f6;
    }
    .report-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #e8f4f8;
        border-left: 5px solid #00a8e8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION (Secrets) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("🚨 API Key Missing. Please check your app settings.")
    st.stop()

# --- 4. BACKEND FUNCTIONS (Your Engine) ---
def get_prompt(style, user_text):
    # (Same optimized prompts as before - condensed for brevity)
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

# --- 5. THE FRONTEND UI LAYOUT ---

# A. Sidebar (Controls)
with st.sidebar:
    st.title("📑 ReportGenie")
    st.caption("AI-Powered Document Formatter")
    st.markdown("---")
    
    # Style Selector with emoji visual cues
    mode = st.radio(
        "Choose Report Style", 
        ["Simple", "Modern", "Academic"],
        captions=["Plain Text (Times New Roman)", "Corporate (McKinsey Style)", "LaTeX Source (Research)"]
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Engine Status")
    st.success("Gemini 1.5 Flash: Online")
    st.info("Quota: ~15 Req/Min")

# B. Main Content Area
st.header("Create Professional Reports Instantly")
st.markdown("Paste your rough notes, meeting transcripts, or messy data below. We'll handle the formatting.")

# Tabs for better organization
tab1, tab2 = st.tabs(["✍️ Input", "ℹ️ How it Works"])

with tab1:
    # Large text area for input
    user_input = st.text_area(
        "Paste text here:", 
        height=300, 
        placeholder="Example: Q3 Revenue was 5M, up 10% from last year. Risks include supply chain issues..."
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Centered "Generate" button
        generate_btn = st.button("✨ Generate PDF Document")

with tab2:
    st.markdown("""
    ### How to use ReportGenie
    1. **Paste Text:** Copy your raw notes or brain dump.
    2. **Select Style:** - **Simple:** Strict formatting, no colors. Good for legal/admin.
       - **Modern:** Beautiful fonts, colors, and layout. Good for business.
       - **Academic:** Generates LaTeX code for scientific papers.
    3. **Download:** Get a polished PDF instantly.
    """)

# --- 6. EXECUTION LOGIC ---

if generate_btn:
    if not user_input:
        st.warning("⚠️ Please enter some text to begin.")
    else:
        # Progress Bar UI
        progress_text = "AI is reading your notes..."
        my_bar = st.progress(0, text=progress_text)

        try:
            # Step 1: Structure (25%)
            my_bar.progress(25, text="Structuring document logic...")
            prompt = get_prompt(mode, user_input)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            clean_output = response.text.replace("```html", "").replace("```latex", "").replace("```", "")
            
            # Step 2: Formatting (75%)
            my_bar.progress(75, text="Applying professional typography...")
            
            if mode == "Academic":
                my_bar.progress(100, text="Done!")
                st.markdown("### ✅ Academic Report Ready")
                
                # Specialized Academic UI
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div class='report-card'><b>Option 1: CloudConvert</b><br>Download the .tex file and drop it into a converter.</div>", unsafe_allow_html=True)
                    st.download_button("⬇️ Download .tex File", clean_output, "report.tex", "text/plain")
                with c2:
                    st.markdown("<div class='report-card'><b>Option 2: LaTeXBase</b><br>Copy the code below into an online editor.</div>", unsafe_allow_html=True)
                    st.code(clean_output, language="latex")
                    
            else: # HTML Modes
                if mode == "Simple":
                    css = "body { font-family: 'Times New Roman'; font-size: 12pt; margin: 2cm; } h1, h2 { font-weight: bold; } ul { padding-left: 20px; }"
                elif mode == "Modern":
                    css = "@page {margin: 2.5cm;} body {font-family: Helvetica, sans-serif; line-height: 1.6;} .title {color: #2c3e50; font-size: 24pt; border-bottom: 2px solid #2c3e50; text-align: center;}"
                
                # Generate PDF
                pdf_data = generate_pdf(clean_output, css)
                my_bar.progress(100, text="Done!")
                
                # Success UI
                st.balloons() # Fun visual effect
                st.success(f"Your **{mode}** report is ready!")
                
                # Full width download button
                st.download_button(
                    label="📄 Download Professional PDF",
                    data=pdf_data,
                    file_name=f"{mode.lower()}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")