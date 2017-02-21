from calendar import HTMLCalendar
import pickle
import os.path

theyear = 2017
themonth = 2

scriptpath = os.path.dirname(__file__)
filename = os.path.join(scriptpath, 'brighton_list.txt')
tide_file = open(filename, "rb")
tide_data = pickle.load(tide_file)


html_cal = HTMLCalendar(firstweekday=6)
v = []
a = v.append
a('\n')
a('<table border="0" cellpadding="0" cellspacing="2px" class="month">')
a('\n')
a(html_cal.formatmonthname(theyear, themonth, withyear=True))
a('\n')
a(html_cal.formatweekheader())
a('\n')
for week in html_cal.monthdays2calendar(theyear, themonth):
    w = ''
    for (d, wd) in week:
        if d == 0:
            w += '<td class="noday">&nbsp;</td>' # day outside month
        else:
            daily_info = ''
            for entry in tide_data:
                if entry[0].month == themonth and entry[0].year == theyear and entry[0].day == d:
                    daily_info += '<br>' + entry[2] + ' ' + entry[1]
            w += '<td class="{}">{}{}</td>'.format(html_cal.cssclasses[wd], d, daily_info)
    a('<tr>{}</tr>'.format(w))
    a('\n')
a('</table>')
a('\n')
cal = ''.join(v)


print(cal)
