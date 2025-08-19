import streamlit as st
import os
import tempfile
from test_data_validation_with_api import (
    convert_json_to_xml,
    merge_xml,
    merge_via_api,
    create_stub_from_actual,
    XMLComparator
)

st.title("📂 XML Test Data Processor (Stepwise)")

# --- Upload only XML (pricing_testdata.xml)
file1 = st.file_uploader("Upload XML file (pricing_testdata.xml)", type=["xml"])

# Assume mule_data.json is fixed / internal
MULE_JSON = "test_data/mule_data.json"   # keep in project root

if st.button("Run Pipeline") and file1:
    with tempfile.TemporaryDirectory() as tmpdir:
        file1_path = os.path.join(tmpdir, file1.name)
        with open(file1_path, "wb") as f:
            f.write(file1.read())

        st.info("Step 1: Converting mule_data.json → XML")
        mule_xml_file = os.path.join(tmpdir, "formated_mule_data.xml")
        convert_json_to_xml(MULE_JSON, mule_xml_file)

        # ---------------- Step 1: Enrichment ----------------
        st.subheader("1️⃣ Enrichment File (Merged Content)")
        enriched_file = os.path.join(tmpdir, "enriched_pricing_testdata.xml")
        merge_xml(file1_path, mule_xml_file, enriched_file)
        st.code(open(enriched_file, "r", encoding="utf-8").read()[:800], language="xml")
        with open(enriched_file, "rb") as f:
            st.download_button("⬇️ Download Enriched XML", f, file_name="enriched.xml")

        # ---------------- Step 2: Expected Results ----------------
        st.subheader("2️⃣ Expected Result (Stub)")
        expected_file = os.path.join(tmpdir, "stub_expected_result.xml")
        merge_via_api(file1_path, mule_xml_file, expected_file)
        create_stub_from_actual(expected_file, expected_file, empty_chance=0.3)
        st.code(open(expected_file, "r", encoding="utf-8").read()[:800], language="xml")
        with open(expected_file, "rb") as f:
            st.download_button("⬇️ Download Expected Result XML", f, file_name="expected.xml")

        # ---------------- Step 3: Actual Results ----------------
        st.subheader("3️⃣ Actual Result (API Merged)")
        actual_file = os.path.join(tmpdir, "actual_result.xml")
        merge_via_api(file1_path, mule_xml_file, actual_file)
        st.code(open(actual_file, "r", encoding="utf-8").read()[:800], language="xml")
        with open(actual_file, "rb") as f:
            st.download_button("⬇️ Download Actual Result XML", f, file_name="actual.xml")

        # ---------------- Step 4: Comparison Report ----------------
        st.subheader("4️⃣ Comparison Report")
        report_file = os.path.join(tmpdir, "comparison_report.html")
        comparator = XMLComparator(actual_file, expected_file)
        comparator.generate_html_report(report_file)

        with open(report_file, "rb") as f:
            st.download_button("⬇️ Download Comparison Report", f, file_name="report.html")

        st.success("✅ Pipeline complete! All steps generated.")
