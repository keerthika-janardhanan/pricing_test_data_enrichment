import streamlit as st
import os
import xml.etree.ElementTree as ET
from pricing_validation import run_pipeline
from streamlit_option_menu import option_menu

# ------------------------
# Helpers
# ------------------------
def load_pricing_testdata(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    rows = root.findall(".//row")
    return len(rows)

# ------------------------
# Page Config
# ------------------------
st.set_page_config(page_title="Pricing Validation", page_icon="💹", layout="wide")

# ------------------------
# Global CSS Tweaks
# ------------------------
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    .workflow-card {
        background: #ffffff;
        padding: 20px 25px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .workflow-card h3, .workflow-card h2 {
        margin-top: 0;
        color: #2c3e50;
    }
    .workflow-card p {
        color: #555;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------
# Session State Init
# ------------------------
for key in ["step1_done", "step2_done", "step3_done", "step4_done"]:
    if key not in st.session_state:
        st.session_state[key] = False

if "output_files" not in st.session_state:
    st.session_state["output_files"] = {}

OUTPUT_DIR = "results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------
# Sidebar Navigation
# ------------------------
with st.sidebar:
    st.title("Pricing Validation Workflow")
    step = option_menu(
        "Steps",
        ["Step 1: Collect Data", "Step 2: Expected Data", "Step 3: Actual Data", "Step 4: Comparison Report"],
        icons=["cloud-download", "clipboard-data", "gear", "bar-chart"],
        menu_icon="list-task",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"background-color": "#f4f6f9"},
            "icon": {"color": "#1abc9c", "font-size": "18px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "5px", "--hover-color": "#e6f7f1"},
            "nav-link-selected": {"background-color": "#1abc9c", "color": "white"},
        },
    )

# ------------------------
# Header
# ------------------------
st.markdown("""
<div style="
    display: inline-block;
    font-size: 40px;
    font-weight: bold;
    line-height: 1.5;
    padding-top: 20px;
    padding-bottom: 10px;
">
💹 Stage 2 - Pricing Validation
</div>
""", unsafe_allow_html=True)

# ------------------------
# Main Content
# ------------------------

# Step 1
# Step 1
if "Step 1" in step:
    st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
    st.subheader("Step 1: Collect & Process Pricing Test Data")
    st.write("Load pricing test data from TDM - Stage 1.")
    
    if st.button("Process test data"):
        xml_file = "test_data/pricing_testdata.xml"
        row_count = load_pricing_testdata(xml_file)
        st.success(f"✔ Processed {row_count} scenarios successfully.")
        
        # Read and show XML content
        with open(xml_file, "r") as f:
            xml_content = f.read()
        
        with st.expander("Pricing test data preview"):
            st.code(xml_content, language="xml")
        
        st.session_state.step1_done = True
    st.markdown('</div>', unsafe_allow_html=True)

# Step 2
elif "Step 2" in step:
    st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
    st.subheader("Step 2: Generate Expected Pricing Data")
    st.write("Generate expected pricing data by applying defined business rules to input data")
    if not st.session_state.step1_done:
        st.warning("⚠ Please complete the previous step.")
    else:
        if st.button("Generate Result"):
            enriched, stub_expected, report = run_pipeline(
                "test_data/pricing_testdata.xml",
                "test_data/mule_data.json",
                OUTPUT_DIR,
            )
            st.session_state.output_files.update({
                "enriched": enriched,
                "stub_expected": stub_expected,
                "report": report
            })

            with open(stub_expected, "r") as f:
                stub_content = f.read()

            st.success("✔ Expected Pricing Test Results Generated")
            with st.expander("Preview Result"):
                st.code(stub_content, language="xml")

            st.download_button(
                label="Download Test Results",
                data=stub_content,
                file_name="stub_expected_result.xml",
                mime="application/xml",
            )
            st.session_state.step2_done = True
    st.markdown('</div>', unsafe_allow_html=True)

# Step 3
elif "Step 3" in step:
    st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
    st.subheader("Step 3: Generate Actual Enrichment Pricing")
    st.write("Run the pipeline to generate the Enrichment pricing results.")
    if not st.session_state.step2_done:
        st.warning("⚠ Please complete the previous steps.")
    else:
        if st.button("Generate Result"):
            enriched_file = st.session_state.output_files.get("enriched")
            with open(enriched_file, "r") as f:
                enriched_content = f.read()

            st.success("✔ Enriched Pricing Data Generated")
            with st.expander("Preview Enriched Data"):
                st.code(enriched_content, language="xml")

            st.download_button(
                label="Download Test Data",
                data=enriched_content,
                file_name="enriched_pricing_testdata.xml",
                mime="application/xml",
            )
            st.session_state.step3_done = True
    st.markdown('</div>', unsafe_allow_html=True)

# Step 4
elif "Step 4" in step:
    st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
    st.subheader("Step 4: Compare Expected vs Actual Results")
    st.write("Generate the final report highlighting mismatches between expected and actual data.")
    if not st.session_state.step3_done:
        st.warning("⚠ Please complete the previous steps.")
    else:
        if st.button("Generate comparison report"):
            report_file = st.session_state.output_files.get("report")
            with open(report_file, "r") as f:
                report_content = f.read()

            st.success("✔ Comparison Report Generated")
            with st.expander("View Report"):
                st.components.v1.html(report_content, height=600, scrolling=True)

            st.download_button(
                label="Download Report",
                data=report_content,
                file_name="actual_expected_comparison_result.html",
                mime="text/html",
            )
            st.session_state.step4_done = True
    st.markdown('</div>', unsafe_allow_html=True)
