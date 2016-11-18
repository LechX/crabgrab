import xml.etree.ElementTree as ET

GOOD_LEVEL = 4.0

def read_xml(file_location):
    data = open(file_location).read()
    return data

def parse_xml(raw_data):
    tree = ET.fromstring(raw_data)
    items = []
    for i in tree.find("data"):
        try:
            items.append([i.find("date").text,
                      i.find("time").text,
                      i.find("predictions_in_ft").text,
                      i.find("highlow").text])
        except Exception as e:
            print(e)
    for i in range(len(items)-1):
        if items[i][3] == "H":
            items[i].append(float(items[i][2]) - float(items[i+1][2]) < GOOD_LEVEL)
        else:
            items[i].append("N/A LOW TIDE")
    return items
