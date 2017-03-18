from django.shortcuts import render
from django.http import JsonResponse
from calendar import HTMLCalendar
import datetime
import time
import os
import django
import requests
from .models import Locations, Tides
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crabgrab.settings')
django.setup()


def login(request):

    state_list = Locations.objects.values_list("state", flat=True).order_by("state")
    state_list = set(state_list)
    state_list = sorted(state_list)

    context_dict = {
        'states': state_list,
    }

    return render(request, 'home.html', context_dict)


def index(request, loc):

    loc = loc.upper()

    this_location = Locations.objects.get(id=loc)
    weather_latitude = this_location.latitude
    weather_longitude = this_location.longitude

    weather = requests.get('http://api.wunderground.com/api/3f56fbf31b6373ae/forecast10day/q/' + weather_latitude + ',' + weather_longitude + '.json')
    weather_parsed_json = weather.json()

    state_list = Locations.objects.values_list("state", flat=True).order_by("state")
    state_list = set(state_list)
    state_list = sorted(state_list)

    # populate current location name, shorten if greater than 20 characters
    current_location = this_location.name
    if len(current_location) > 20:
        current_location = current_location[:20] + '...'

    theyear = datetime.datetime.now().year
    themonth = 1

    tide_data = Tides.objects.filter(location=loc).order_by("datetime")

    full_cal = []

    for months in range(0, 12):

        # create html calendar object; a list 'v'; and a method 'a' to append to 'v'
        html_cal = HTMLCalendar(firstweekday=6)
        v = []
        a = v.append

        # create month table
        a('\n')
        a('<table border="0" cellpadding="0" cellspacing="2px" class="month">')
        a('\n')

        if themonth == datetime.date.today().month:
            a('<a name="currentmonth"></a>')

        # add [month year] header
        a(html_cal.formatmonthname(theyear, themonth, withyear=True))
        a('\n')

        # add weekday names
        a(html_cal.formatweekheader())
        a('\n')

        # loop through weeks as table rows
        for week in html_cal.monthdays2calendar(theyear, themonth):

            w = ''

            for (d, wd) in week:

                if d == 0:  # day outside month
                    w += '<td class="noday">&nbsp;</td>'

                else:  # create inner tables for each day with H/L, tide in feet, and change

                    # set up individual day table with title row for date, feet, time, and change symbol
                    daily_info = '<table border="0" cellpadding="0" cellspacing="0" class="day"><tr>' \
                                 '<th class="datenumber">{}</th><th class="feet">feet</th><th class="time">time' \
                                 '</th><th class="change">&#9651;</th></tr>'.format(d)

                    # for each tide that matches this day+month+year, add a table row with relevant data
                    for entry in tide_data:
                        if entry.datetime.month == themonth and entry.datetime.year == theyear and entry.datetime.day == d:
                            am_pm_time = entry.datetime.strftime('%I:%M %p')
                            daily_info += '<tr><td>{}</td><td>{}</td><td>{}</td><td class={}>{}</td></tr>' \
                                .format(entry.H_L, entry.height, am_pm_time, entry.classification, entry.change)

                    # for stylistic purposes, add an invisible dummy row when there are only three tide changes in a day
                    if daily_info.count('tr') == 8:  # eight instances of tr from header and three tide rows
                        daily_info += '<tr><td class="invisibleRow">CR</td><td class="invisibleRow">AB</td>' \
                                      '<td class="invisibleRow">TIDES</td><td class="invisibleRow">.COM</td></tr>'

                    # add in ten day forecast based on current day and calendar day currently being generated
                    current_day = datetime.date.today()
                    calendar_day = '{}/{}/{}'.format(themonth, d, theyear)
                    calendar_day = datetime.datetime.strptime(calendar_day, '%m/%d/%Y').date()

                    if current_day <= calendar_day <= (current_day + datetime.timedelta(days=9)):

                        # pull relevant icons for day and night weather (index 0-19 for ten days)
                        forecast_day_integer = (calendar_day - current_day).days
                        forecast_day_index = forecast_day_integer * 2
                        forecast_night_index = forecast_day_integer * 2 + 1

                        daily_weather_icon = \
                            weather_parsed_json['forecast']['txt_forecast']['forecastday'][forecast_day_index]['icon']
                        daily_weather_icon_url = 'https://icons.wxug.com/i/c/i/' + daily_weather_icon + '.gif'

                        nightly_weather_icon = \
                            weather_parsed_json['forecast']['txt_forecast']['forecastday'][forecast_night_index]['icon']
                        nightly_weather_icon_url = 'https://icons.wxug.com/i/c/i/' + nightly_weather_icon + '.gif'

                        # pull relevant description (need to figure out how to create a hover item for this)
                        # daily_weather_description = weather_parsed_json['forecast']['txt_forecast']['forecastday'][forecast_day_index]['fcttext']

                        # add daily rainfall and classification
                        accumulation = weather_parsed_json['forecast']['simpleforecast']['forecastday'][forecast_day_integer]['qpf_allday']['in']

                        if accumulation >= 0.5:
                            rain_tag = 'rain-heavy'
                        elif accumulation >= 0.25:
                            rain_tag = 'rain-moderate'
                        else:
                            rain_tag = 'rain-light'

                        # add forecast items to a new row in table
                        daily_info += '<tr><th colspan="2" class="forecast">Day</th><th class="forecast">Night</th>' \
                                      '<th class="forecast">Rain</th></tr><tr><td colspan="2">' \
                                      '<img src="{}" height="30"></td><td><img src="{}" height="30"></td>' \
                                      '<td class="{}">{} in.</td></tr>' \
                            .format(daily_weather_icon_url, nightly_weather_icon_url, rain_tag, accumulation)

                    # append daily table html string to the week's html string
                    w += '<td class="{}">{}</table></td>'.format(html_cal.cssclasses[wd], daily_info)

            # plug the week's html string into the appropriate row and start a new line
            a('<tr>{}</tr>'.format(w))
            a('\n')

        # close month table and join list 'v' as string 'month_cal'
        a('</table>')
        a('\n')
        month_cal = ''.join(v)

        # append 'month_cal' to 'full_cal' and increment themonth
        full_cal.append(month_cal)
        themonth += 1

    cal = ''.join(full_cal)

    context_dict = {
        'current_location': current_location,
        'cal': cal,
        'states': state_list,
    }

    weather.close()

    return render(request, 'index.html', context_dict)


# returns JSON including all locations for a given region
def location_picker(request):
    region = request.POST["region"]
    loc_list = list(Locations.objects.filter(state=region).order_by("name").values_list("name", "id"))
    return JsonResponse({"loc": loc_list})
