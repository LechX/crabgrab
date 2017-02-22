from django.shortcuts import render
from django.http import JsonResponse
from calendar import HTMLCalendar
import json
import pickle
import os.path
import datetime
from .models import Locations

# this should be request, year, month, location
def index(request, loc, yr, mnt, dur):

    state_list = set(Locations.objects.values_list("state", flat=True))

    current_location = loc

    theyear = int(yr)  # replace with year from view definition
    themonth = int(mnt)  # replace with month from view definition

    scriptpath = os.path.dirname(__file__)
    filename = os.path.join(scriptpath, 'big_test.txt')  # replace with path to location data in database
    tide_file = open(filename, "rb")
    tide_data = pickle.load(tide_file)

    full_cal = []

    for months in range(0, int(dur)):

        html_cal = HTMLCalendar(firstweekday=6)
        v = []
        a = v.append

        # create month table
        a('\n')
        a('<table border="0" cellpadding="0" cellspacing="2px" class="month">')
        a('\n')

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
                    daily_info = '<table border="0" cellpadding="0" cellspacing="0" class="day"><tr>' \
                                 '<th class="datenumber">{}</th><th class="feet">feet</th><th class="time">time' \
                                 '</th><th class="change">&#9651;</th></tr>'.format(d)

                    for entry in tide_data:
                        if entry[0].month == themonth and entry[0].year == theyear and entry[0].day == d:
                            am_pm_time = entry[0].strftime('%I:%M %p')
                            daily_info += '<tr><td>{}</td><td>{}</td><td>{}</td><td class={}>{}</td></tr>' \
                                .format(entry[2], entry[1], am_pm_time, entry[3], entry[4])

                    if daily_info.count('tr') == 8:
                        daily_info += '<tr><td class="invisibleRow">CR</td><td class="invisibleRow">AB</td>' \
                                      '<td class="invisibleRow">TIDES</td><td class="invisibleRow">.COM</td></tr>'

                    w += '<td class="{}">{}</table></td>'.format(html_cal.cssclasses[wd], daily_info)

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

    return render(request, 'index.html', context_dict)


def location_picker(request):
    if request.method == "POST":
        region = request.POST["region"]
        loc_list = list(Locations.objects.filter(state=region).values_list("name", flat=True))
        print(type(loc_list[0]))
        return JsonResponse({"loc": loc_list})
