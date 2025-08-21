import streamlit as st
import os
import xml.etree.ElementTree as ET
from pricing_validation import run_pipeline

# ------------------------
# Helpers
# ------------------------
def load_pricing_testdata(xml_file):
    """Count number of <row> elements in pricing test data."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    rows = root.findall(".//row")
    return len(rows)

# ------------------------
# Global Styling
# ------------------------
st.set_page_config(page_title="Pricing Validation", page_icon="💹", layout="wide")

st.markdown(
    """
    <style>
    /* Background */
    .stApp {
        background-color: #f8f9fa;
    }

    /* Headers */
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', sans-serif;
    }
    h2 {
    font-size: 20px !important;
    }

    /* Success & Warning messages */
    .stSuccess {
        background-color: #e6ffed !important;
        border: 1px solid #2ecc71 !important;
    }
    .stWarning {
        background-color: #fff8e6 !important;
        border: 1px solid #f39c12 !important;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #2c3e50;
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-size: 10px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #1abc9c;
        color: white;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: bold;
        font-size: 5px;
        color: #34495e;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------
# Session State Init
# ------------------------
for key in ["step1_done", "step2_done", "step3_done", "step4_done",
            "warn_step2", "warn_step3", "warn_step4"]:
    if key not in st.session_state:
        st.session_state[key] = False

if "output_files" not in st.session_state:
    st.session_state["output_files"] = {}

OUTPUT_DIR = "results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------
# UI Flow
# ------------------------
st.title("💹 Pricing Data Validation Workflow")

# Step 1
st.header("Step 1: Collect & Preprocess Pricing Data")
if st.button("🔍 Collect Pricing Test Data"):
    row_count = load_pricing_testdata("test_data/pricing_testdata.xml")
    st.success(f"✅ Pricing file processed with **{row_count} scenarios**. This file will be processed into application/api")
    st.session_state.step1_done = True

# Step 2
st.header("Step 2: Generate Expected Pricing Data")
if st.button("⚙️ Generate Expected Result"):
    if not st.session_state.step1_done:
        st.session_state.warn_step2 = True
    else:
        enriched, stub_expected, report = run_pipeline(
            "test_data/pricing_testdata.xml",
            "test_data/mule_data.json",
            OUTPUT_DIR
        )
        st.session_state.output_files["enriched"] = enriched
        st.session_state.output_files["stub_expected"] = stub_expected
        st.session_state.output_files["report"] = report

        with open(stub_expected, "r") as f:
            stub_content = f.read()

        st.success(f"✅ Expected Pricing Data Generated → `{stub_expected}`")
        with st.expander("📄 View Expected Stub Content"):
            st.code(stub_content, language="xml")

        st.download_button(
            label="⬇️ Download Expected Stub",
            data=stub_content,
            file_name="stub_expected_result.xml",
            mime="application/xml"
        )

        st.session_state.step2_done = True
        st.session_state.warn_step2 = False

if st.session_state.warn_step2:
    st.warning("⚠️ Please proceed with Step 1 to continue.")

# Step 3
st.header("Step 3: Generate Actual Enriched Pricing Data")
if st.button("🔧 Generate Actual Result"):
    if not st.session_state.step2_done:
        st.session_state.warn_step3 = True
    else:
        enriched_file = st.session_state.output_files.get("enriched")
        with open(enriched_file, "r") as f:
            enriched_content = f.read()

        st.success(f"✅ Actual Enriched Pricing Data Generated → `{enriched_file}`")
        with st.expander("📄 View Enriched Pricing Data"):
            st.code(enriched_content, language="xml")

        st.download_button(
            label="⬇️ Download Enriched Pricing Data",
            data=enriched_content,
            file_name="enriched_pricing_testdata.xml",
            mime="application/xml"
        )

        st.session_state.step3_done = True
        st.session_state.warn_step3 = False

if st.session_state.warn_step3:
    st.warning("⚠️ Please proceed with Step 2 to continue.")

# Step 4
st.header("Step 4: Compare Expected vs Actual Results")
if st.button("📑 Generate Comparison Report"):
    if not st.session_state.step3_done:
        st.session_state.warn_step4 = True
    else:
        report_file = st.session_state.output_files.get("report")
        with open(report_file, "r") as f:
            report_content = f.read()

        st.success(f"✅ Report Generated → `{report_file}`")
        with st.expander("📄 View Comparison Report"):
            st.components.v1.html(report_content, height=500, scrolling=True)

        st.download_button(
            label="⬇️ Download Comparison Report",
            data=report_content,
            file_name="actual_expected_comparison_result.html",
            mime="text/html"
        )

        st.session_state.step4_done = True
        st.session_state.warn_step4 = False

if st.session_state.warn_step4:
    st.warning("⚠️ Please proceed with Step 3 to continue.")
