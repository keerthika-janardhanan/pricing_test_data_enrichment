import os
import json
import xml.etree.ElementTree as ET
import copy
import random
import pandas as pd
from jinja2 import Template
from xml.dom import minidom
import requests

# ---------- FOLDERS ----------
TEST_DATA_DIR = "test_data"
TEST_RESULTS_DIR = "test_results"
REPORTS_DIR = "reports"

os.makedirs(TEST_DATA_DIR, exist_ok=True)
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ---------- STEP 1: Convert JSON to XML ----------
def json_to_xml_element(tag, data):
    elem = ET.Element(tag)
    if isinstance(data, dict):
        for k, v in data.items():
            elem.append(json_to_xml_element(k, v))
    else:
        elem.text = str(data)
    return elem

def convert_json_to_xml(json_file, xml_output_file):
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    if "factors" in json_data.get("rarFullPostCodeResponse", {}):
        try:
            json_data["rarFullPostCodeResponse"]["factors"] = json.loads(
                json_data["rarFullPostCodeResponse"]["factors"]
            )
        except Exception:
            pass

    file2_elem = json_to_xml_element(
        "rarFullPostCodeResponse",
        json_data["rarFullPostCodeResponse"]
    )

    file2_pretty = minidom.parseString(
        ET.tostring(file2_elem, encoding="utf-8")
    ).toprettyxml(indent="    ")
    file2_pretty = "\n".join(file2_pretty.split("\n")[1:]).strip()

    with open(xml_output_file, "w", encoding="utf-8") as f:
        f.write(file2_pretty)

    print(f"✅ Step1: {xml_output_file} created")
    return xml_output_file

# ---------- STEP 2a: Local merge ----------
def merge_xml(file1, file2_converted, output_file):
    tree1 = ET.parse(file1)
    root1 = tree1.getroot()

    tree2 = ET.parse(file2_converted)
    root2 = tree2.getroot()

    sheet = root1.find("sheet")
    if sheet is None:
        raise Exception(f"File {file1} does not contain <sheet> element")

    for row in sheet.findall("row"):
        row.append(copy.deepcopy(root2))

    tree1.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ Step2a: Local merged XML → {output_file}")
    return output_file

# ---------- STEP 2b: Merge via API ----------
def merge_via_api(file1, file2_converted, output_file, api_url="http://127.0.0.1:8000/merge_xml"):
    with open(file1, "rb") as f1, open(file2_converted, "rb") as f2:
        response = requests.post(
            api_url,
            files={
                "file1": ("file1.xml", f1, "application/xml"),
                "file2": ("file2.xml", f2, "application/xml")
            }
        )

    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"✅ Step2b: API merged XML → {output_file}")
    else:
        raise Exception(f"API call failed with status {response.status_code}: {response.text}")
    return output_file

# ---------- STEP 3: Create Stub from API result ----------
def create_stub_from_actual(actual_file, expected_file, empty_chance=0.2):
    tree = ET.parse(actual_file)
    root = tree.getroot()

    # Apply 30% empty rule to all elements
    for elem in root.findall(".//*"):
        if elem.text and random.random() < empty_chance:
            elem.text = ""

    tree.write(expected_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ Step3: Stub created → {expected_file}")
    return expected_file

# ---------- STEP 4: Compare XMLs & Generate HTML ----------
class XMLComparator:
    def __init__(self, actual_xml, expected_xml):
        self.output_root = ET.parse(actual_xml).getroot()
        self.expected_root = ET.parse(expected_xml).getroot()

    def row_to_dict(self, row):
        return {elem.tag: elem.text for elem in row.iter() if elem is not row}

    def generate_failed_data(self):
        failed_data = []
        output_rows = self.output_root.findall(".//row")
        expected_rows = self.expected_root.findall(".//row")

        total_tags = 0
        passed_count = 0
        failed_count = 0

        for i, (o_row, e_row) in enumerate(zip(output_rows, expected_rows), start=1):
            o_dict = self.row_to_dict(o_row)
            e_dict = self.row_to_dict(e_row)
            row_failed = {"Row": i, "failed_attrs": []}

            for field, e_val in e_dict.items():
                total_tags += 1
                o_val = o_dict.get(field, "")
                if o_val != e_val:
                    failed_count += 1
                    row_failed["failed_attrs"].append({
                        "field": field,
                        "expected": e_val,
                        "actual": o_val,
                        "status": "Failed"
                    })
                else:
                    passed_count += 1

            if row_failed["failed_attrs"]:
                failed_data.append(row_failed)

        summary = {
            "total_tags": total_tags,
            "passed": passed_count,
            "failed": failed_count
        }
        return failed_data, summary

    def generate_html_report(self, filename="comparison_report.html"):
        failed_data, summary = self.generate_failed_data()

        # Full actual XML table
        df_actual = pd.DataFrame([self.row_to_dict(r) for r in self.output_root.findall(".//row")]).fillna("")
        html_actual = df_actual.to_html(border=1, index=False, escape=False)

        # Build HTML
        html_template = """
        <html>
        <head>
        <title>XML Comparison Report</title>
        <style>
            table {border-collapse: collapse; margin-bottom: 20px;}
            th, td {border: 1px solid black; padding: 5px; text-align: center;}
            .Failed {background-color: #ffc7ce; color: #9c0006;}
        </style>
        </head>
        <body>
        <h2>Part 1: Summary</h2>
        <table>
            <tr><th>Summary</th><th>Count</th></tr>
            <tr><td>Total tags</td><td>{{summary.total_tags}}</td></tr>
            <tr><td>Passed</td><td>{{summary.passed}}</td></tr>
            <tr><td>Failed</td><td>{{summary.failed}}</td></tr>
        </table>

        <h2>Part 2: Failed Details</h2>
        {% for row in failed_data %}
            <table>
                <tr>
                    <th>Row</th>
                    {% for attr in row.failed_attrs %}
                        <th>expected_{{attr.field}}</th>
                        <th>actual_{{attr.field}}</th>
                        <th>Status</th>
                    {% endfor %}
                </tr>
                <tr>
                    <td>{{row.Row}}</td>
                    {% for attr in row.failed_attrs %}
                        <td>{{attr.expected}}</td>
                        <td>{{attr.actual}}</td>
                        <td class="Failed">{{attr.status}}</td>
                    {% endfor %}
                </tr>
            </table>
        {% endfor %}

        <h2>Part 3: Actual Result (Full Output)</h2>
        {{actual_xml | safe}}
        </body>
        </html>
        """

        template = Template(html_template)
        html_report = template.render(
            summary=summary,
            failed_data=failed_data,
            actual_xml=html_actual
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_report)

        print(f"✅ HTML report generated → {filename}")

# ---------- DEMO EXECUTION ----------
def run_pipeline(file1_path, file2_path, output_dir="results"):
    os.makedirs(output_dir, exist_ok=True)

    # Step1: Convert JSON → XML
    formated_mule_data_file = os.path.join(output_dir, "formated_mule_data.xml")
    convert_json_to_xml(file2_path, formated_mule_data_file)

    # Step2a: Local merge
    enriched_pricing_file = os.path.join(output_dir, "enriched_pricing_testdata.xml")
    merge_xml(file1_path, formated_mule_data_file, enriched_pricing_file)

    # Step2b: API merge
    stub_expected_file = os.path.join(output_dir, "stub_expected_result.xml")
    merge_via_api(file1_path, formated_mule_data_file, stub_expected_file)

    # Step3: Create stub
    create_stub_from_actual(stub_expected_file, stub_expected_file, empty_chance=0.3)

    # Step4: Compare & HTML report
    report_file = os.path.join(output_dir, "comparison_report.html")
    comparator = XMLComparator(enriched_pricing_file, stub_expected_file)
    comparator.generate_html_report(report_file)

    return enriched_pricing_file, stub_expected_file, report_file
