from django.shortcuts import render
from django.http import JsonResponse
from calendar import HTMLCalendar
import datetime
import os
import django
from .models import Locations, Tides
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crabgrab.settings')
django.setup()



def index(request, loc):

    state_list = Locations.objects.values_list("state", flat=True).order_by("state")
    state_list = set(state_list)
    state_list = sorted(state_list)

    loc = loc.upper()
    current_location = Locations.objects.get(id=loc)
    current_location = current_location.name

    theyear = 2017
    themonth = 1

    tide_data = Tides.objects.filter(location=loc).order_by("datetime")

    full_cal = []

    for months in range(0, 12):

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
                        if entry.datetime.month == themonth and entry.datetime.year == theyear and entry.datetime.day == d:
                            am_pm_time = entry.datetime.strftime('%I:%M %p')
                            daily_info += '<tr><td>{}</td><td>{}</td><td>{}</td><td class={}>{}</td></tr>' \
                                .format(entry.H_L, entry.height, am_pm_time, entry.classification, entry.change)

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
        loc_list = list(Locations.objects.filter(state=region).order_by("name").values_list("name", "id"))
        return JsonResponse({"loc": loc_list})
