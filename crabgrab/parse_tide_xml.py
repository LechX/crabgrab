import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone, make_aware
import pickle
import requests
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crabgrab.settings')
django.setup()
from pages.models import Locations, Tides
import time

start_time = time.time()

# annual_forecast = list()

# SME designations
GOOD_LEVEL = 4.0
MODERATE_LEVEL = 6.0

# Google TZ API Key AIzaSyBr6teGFmauT76DNn4jjiI-yqgvxJuqRiQ
# https://maps.googleapis.com/maps/api/timezone/json?location=LAT,LNG&timestamp=SECONDSSINCE1970&key=KEY
# Alaska vs. Alaska/Hawaii time zone border at -169.30
# Florida time zone somewhere between -85.3933 and -85.3133

current_state = "Cuba"

def convert_ss_sr_utc_to_local(date_time, longitude):

    # convert date_time argument from ss/sr JSON to python datetime object
    target = date_time.replace('T', ' ')
    target = target.split('+')
    target = datetime.strptime(target[0], '%Y-%m-%d %H:%M:%S')
    target = make_aware(target, get_current_timezone(), is_dst=False)

    # set up DST start and end (2017 specific, in UTC)
    DST_start = datetime.strptime('2017-03-11 02:00:00', '%Y-%m-%d %H:%M:%S')
    DST_start = make_aware(DST_start, get_current_timezone(), is_dst=False)

    DST_end = datetime.strptime('2017-11-05 02:00:00', '%Y-%m-%d %H:%M:%S')
    DST_end = make_aware(DST_end, get_current_timezone(), is_dst=False)

    # apply adjustment to convert from UTC to local time (inelegant solution to avoid paying Google for time zone API)
    if current_state == "Hawaii" or current_state == "Alaska" and float(longitude) < -169.3:
        target = target - timedelta(hours=10)  # HAST
    elif current_state == "Alaska":
        if target > DST_start and target < DST_end:
            target = target - timedelta(hours=8)  # AKDT
        else:
            target = target - timedelta(hours=9)  # AKST
    elif current_state == "Washington" or current_state == "Oregon" or current_state == "California":
        if target > DST_start and target < DST_end:
            target = target - timedelta(hours=7)  # PDT
        else:
            target = target - timedelta(hours=8)  # PST
    elif current_state == "Texas" or current_state == "Louisiana" or current_state == "Mississippi" or current_state == "Alabama" or current_state == "Florida" and float(longitude) < -85.3533:
        if target > DST_start and target < DST_end:
            target = target - timedelta(hours=5)  # CDT
        else:
            target = target - timedelta(hours=6)  # CST
    else:
        if target > DST_start and target < DST_end:
            target = target - timedelta(hours=4)  # EDT
        else:
            target = target - timedelta(hours=5)  # EST

    return target


def parse_xml(raw_data, latitude, longitude, station_id):

    try:
        tree = ET.fromstring(raw_data)
    except:
        print("error with station_id {}".format(station_id))
        return ""

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
        peak_time = make_aware(peak_time, get_current_timezone(), is_dst=True)  # is this reading as UTC and converting to pacific?
        peak_time = peak_time - timedelta(hours=8)  # adjusting per theory in line above

        # append time, water level, high/low
        try:
            items.append([peak_time,
                      i.find("pred_in_ft").text,
                      i.find("highlow").text])
        except Exception as e:
            print(e)
            print(year_month_day)

    # process list items to generate calendar IDs and add change level
    for i in range(len(items)):

        time_of_day = str()
        change_level = str()

        # determine if day or night
        if items[i][0].date() != items[i-1][0].date():
            sr_ss_date = items[i][0].strftime('%Y-%m-%d')
            sr_ss_UTC_result = requests.get('http://api.sunrise-sunset.org/json?lat=' + str(latitude) + '&lng=' + str(longitude) + '&date=' + sr_ss_date + '&formatted=0').json()

        # for day_start, turn srssresult into datetime object offset to pst (use sunrise plus one hour)
        day_start = sr_ss_UTC_result.get('results').get('sunrise')
        day_start = convert_ss_sr_utc_to_local(day_start, longitude)
        day_start = day_start - timedelta(hours=8)  # converting per theory that make_aware is changing time under assumption that it is given UTC when in fact it is a Pacific time
        day_start = day_start + timedelta(hours=1)  # hour buffer so dad doesn't try to crab in the dark

        # for day_end, turn srssresult into datetime object offset to pst (use civil_twilight_end)
        day_end = sr_ss_UTC_result.get('results').get('civil_twilight_end')
        day_end = convert_ss_sr_utc_to_local(day_end, longitude)
        day_end = day_end - timedelta(hours=8)  # converting per theory that make_aware is changing time under assumption that it is given UTC when in fact it is a Pacific time

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

        # add change level
        items[i].append(change)
        items[i].append(station_id)

        # store each tide in database
        t = Tides()
        l = Locations.objects.get(id=station_id)

        t.location = l
        t.datetime = items[i][0]
        t.height = items[i][1]
        t.H_L = items[i][2]
        t.classification = items[i][3]
        t.change = items[i][4]
        t.save()

    # return items


# brighton_latitude = '+45.6700'
# brighton_longitude = '-123.9250'
# brighton_id = '9437815'


def main(station_id, latitude, longitude):

    # location_xml = requests.get("https://tidesandcurrents.noaa.gov/noaatidepredictions/NOAATidesFacade.jsp?datatype=Annual+XML&Stationid=" + station_id) # 2017 version
    location_xml = requests.get("https://tidesandcurrents.noaa.gov/cgi-bin/predictiondownload.cgi?&stnid=" + station_id + "&threshold=&thresholdDirection=greaterThan&bdate=2018&timezone=LST/LDT&datum=MLLW&clock=12hour&type=xml&annual=true") # 2018 version
    parse_xml(location_xml.text, latitude, longitude, station_id)

    # annual_forecast = parse_xml(location_xml.text, latitude, longitude, station_id)

    # with open("big_test_non_binary.txt", "w") as test_list:
    #     pickle.dump(annual_forecast, test_list)
    # test_list = open("big_test_non_binary.txt", "w")
    # pickle.dump(annual_forecast, test_list)
    # test_list.close()

# mid_april_weekend_states = ["Alabama", "Mississippi", "Louisiana", "Texas", "Maine", "New Hampshire", "Massachusetts", "Rhode Island", "Connecticut", "New York", "New Jersey", "Delaware", "Pennsylvania", "Maryland", "Virginia", "Washington DC", "North Carolina", "South Carolina", "Georgia", "Florida"]

# mid_april_weekend_states = ["Oregon"]

# for s in mid_april_weekend_states:
    # current_state = s
    # locs = Locations.objects.filter(state=current_state)


#######################################################
## NEW LOOP FOR GRABBING ALL TIDES FOR ALL LOCATIONS ##
#######################################################

locs = Locations.objects.all()
location_index = 0

for x in locs:
    # set time to test program speed
    location_start_time = time.time()

    # clear current 2018 tides if present
    loc_tides = Tides.objects.filter(location=x)
    for loc_tide in loc_tides:
        if loc_tide.datetime.year == 2018:
            loc_tide.delete()

    # run main tide function on this location
    main(x.id, x.latitude, x.longitude)
    location_index += 1
    print("{} seconds elapsed while parsing {}".format(time.time() - location_start_time, x.name))

print("{} locations parsed".format(location_index))
print("{} total seconds elapsed".format(time.time() - start_time))

# completed_states = ["Oregon", "Washington", "California", "Hawaii", "Alaska", "Alabama", "Mississippi", "Louisiana", "Texas", "Maine", "New Hampshire", "Massachusetts", "Rhode Island", "Connecticut", "New York", "New Jersey", "Delaware", "Pennsylvania", "Maryland", "Virginia", "Washington DC", "North Carolina", "South Carolina", "Georgia", "Florida"]
# locs = Locations.objects.all().exclude(state__in=completed_states)
