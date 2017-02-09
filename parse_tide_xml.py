import xml.etree.ElementTree as ET
from datetime import datetime
import pickle

GOOD_LEVEL = 4.0
annual_forecast = []

def read_xml(file_location):
    data = open(file_location).read()
    return data

def parse_xml(raw_data):
    tree = ET.fromstring(raw_data)
    items = []
    for i in tree.find("data"):
        year_month_day = i.find("date").text
        year_month_day = year_month_day.split('/')
        year = year_month_day[0]
        month = year_month_day[1]
        day = year_month_day[2]
        time_12h = i.find("time").text
        peak_time = datetime.strptime(month + " " + day + " " + year + " " + time_12h, '%m %d %Y %I:%M %p')
        try:
            items.append([peak_time,
                      i.find("predictions_in_ft").text,
                      i.find("highlow").text])
        except Exception as e:
            print(e)
            print(year_month_day)
    for i in range(len(items)-1):
        if items[i][2] == "H": # need to add start and end time conditions here (sunrise/set agnostic to start)
            items[i].append(float(items[i][1]) - float(items[i+1][1]) < GOOD_LEVEL)
        else:
            items[i].append("N/A LOW TIDE")
        change = round(float(items[i][1]) - float(items[i+1][1]), 1)
        items[i].append(change)
    return items

brighton_tides = parse_xml(read_xml("brighton_test_tide.xml"))

for i in brighton_tides:
    annual_forecast.append(i)
    # if len(i) == 5:
    #     if i[3] == True:
    #         print(i)

brighton_list = open("brighton_list.txt", "wb")

pickle.dump(annual_forecast, brighton_list)

brighton_list.close()
