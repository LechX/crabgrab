import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pickle
import requests

annual_forecast = []

# somewhat arbitrary designations
GOOD_LEVEL = 4.0
MODERATE_LEVEL = 6.0


def read_xml(file_location):
    data = open(file_location).read()
    return data


def convert_ss_sr_utc_to_pst(date_time):

    # convert date_time argument from ss/sr JSON to python datetime object
    target = date_time.replace('T', ' ')
    target = target.split('+')
    target = datetime.strptime(target[0], '%Y-%m-%d %H:%M:%S')

    # set up DST start and end (2017 specific) and apply adjustment to UTC
    DST_start = datetime.strptime('2017-03-11 02:00:00', '%Y-%m-%d %H:%M:%S')
    DST_end = datetime.strptime('2017-11-05 02:00:00', '%Y-%m-%d %H:%M:%S')
    if target > DST_start and target < DST_end:
        target = target - timedelta(hours=8)
    else:
        target = target - timedelta(hours=7)

    return target


def parse_xml(raw_data, latitude, longitude):

    tree = ET.fromstring(raw_data)
    items = []

    # start parsing xml and building list items with time, water level, high/low
    for i in tree.find("data"):

        # pull date and time to create a datetime object
        year_month_day = i.find("date").text
        year_month_day = year_month_day.split('/')
        year = year_month_day[0]
        month = year_month_day[1]
        day = year_month_day[2]
        time_12h = i.find("time").text
        peak_time = datetime.strptime(month + " " + day + " " + year + " " + time_12h, '%m %d %Y %I:%M %p')

        # append time, water level, high/low
        try:
            items.append([peak_time,
                      i.find("predictions_in_ft").text,
                      i.find("highlow").text])
        except Exception as e:
            print(e)
            print(year_month_day)

    # process list items to generate calendar IDs and add change level
    for i in range(len(items)):

        time_of_day = str()
        change_level = str()

        # determine if day or night
        if items[i][0].date != items[i-1][0].date:
            sr_ss_date = items[i][0].strftime('%Y-%m-%d')
            sr_ss_UTC_result = requests.get('http://api.sunrise-sunset.org/json?lat=' + str(latitude) + '&lng=' + str(longitude) + '&date=' + sr_ss_date + '&formatted=0').json()
        else:
            continue

        # for day_start, turn srssresult into datetime object offset to pst (use sunrise plus one hour)
        day_start = sr_ss_UTC_result.get('results').get('sunrise')
        day_start = convert_ss_sr_utc_to_pst(day_start)
        day_start = day_start + timedelta(hours=1)  # hour buffer so dad doesn't try to crab in the dark

        # for day_end, turn srssresult into datetime object offset to pst (use civil_twilight_end)
        day_end = sr_ss_UTC_result.get('results').get('civil_twilight_end')
        day_end = convert_ss_sr_utc_to_pst(day_end)

        # compare item[0] to day start/end and set time_of_day accordingly
        if items[i][0] > day_start and items[i][0] < day_end:
            time_of_day = "day"
        else:
            time_of_day = "night"

        change = round(float(items[i][1]) - float(items[i-1][1]), 1)

        # determine position relative to GOOD_LEVEL and MODERATE_LEVEL
        if abs(change) < GOOD_LEVEL:
            change_level = "good"
        elif abs(change) < MODERATE_LEVEL:
            change_level = "moderate"
        else:
            change_level = "poor"

        html_sequence = [time_of_day, change_level]
        id_for_html = "-".join(html_sequence)
        items[i].append(id_for_html)
        print(id_for_html)

        # add change level
        items[i].append(change)

    return items

brighton_latitude = '+45.6700'
brighton_longitude = '-123.9250'
brighton_id = '9437815'
station_id = brighton_id

location_xml = requests.get("https://tidesandcurrents.noaa.gov/noaatidepredictions/NOAATidesFacade.jsp?datatype=Annual+XML&Stationid=" + station_id)

annual_forecast = parse_xml(location_xml.text, brighton_latitude, brighton_longitude)


# annual_forecast = parse_xml(read_xml("brighton_test_tide.xml"), brighton_latitude, brighton_longitude)

# write annual forecast to a binary txt file with pickle
# brighton_list = open("brighton_list_ss_sr_test.txt", "wb")
brighton_list = open("big_test.txt", "wb")
pickle.dump(annual_forecast, brighton_list)
brighton_list.close()
