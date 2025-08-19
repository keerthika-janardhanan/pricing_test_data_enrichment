# stub_server.py
from flask import Flask, request, Response
import xml.etree.ElementTree as ET
import io
import copy

app = Flask(__name__)

@app.route("/merge_xml", methods=["POST"])
def merge_xml():
    if "file1" not in request.files or "file2" not in request.files:
        return {"error": "Missing file1 or file2"}, 400

    file1 = request.files["file1"]
    file2 = request.files["file2"]

    try:
        # Parse input XMLs
        tree1 = ET.parse(file1)
        root1 = tree1.getroot()

        tree2 = ET.parse(file2)
        root2 = tree2.getroot()

        # Insert <rarFullPostCodeResponse> into each <row> of file1
        sheet = root1.find("sheet")
        if sheet is None:
            return {"error": "file1.xml does not contain <sheet>"}, 400

        for row in sheet.findall("row"):
            row.append(copy.deepcopy(root2))

        # Output merged XML as response
        merged_io = io.BytesIO()
        tree1.write(merged_io, encoding="utf-8", xml_declaration=True)

        return Response(merged_io.getvalue(), mimetype="application/xml")

    except ET.ParseError as e:
        return {"error": f"Invalid XML format: {str(e)}"}, 400
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
