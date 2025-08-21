import xml.etree.ElementTree as ET
import copy

def merge_xml_logic(file1, file2):
    tree1 = ET.parse(file1)
    tree2 = ET.parse(file2)

    root1 = tree1.getroot()
    root2 = tree2.getroot()

    for child in root2:
        root1.append(copy.deepcopy(child))

    return tree1
