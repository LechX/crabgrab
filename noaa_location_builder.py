import requests
import re
from bs4 import BeautifulSoup
import pickle

noaa = requests.get("https://tidesandcurrents.noaa.gov/tide_predictions.html")

soup = BeautifulSoup(noaa.text, 'html.parser')

location_dict = dict()

intermediate_list = re.findall(r'<a href="(\?gid=[0-9]*?)">\s*?\s+(.*?)\n\s*?\s+<\/a>', soup.prettify())

location_dict = {b:a for a,b in intermediate_list}

index = 0

master_dict = dict()

for i in location_dict:

    noaa_location = requests.get("https://tidesandcurrents.noaa.gov/tide_predictions.html" + location_dict.get(i))
    soupy = BeautifulSoup(noaa_location.text, 'html.parser')

    location_list = re.findall(r'href=\"\/noaatidepredictions\/NOAATidesFacade\.jsp\?Stationid=([A-Z0-9]*)\">\s*([a-zA-Z0-9\,\ \.\)\(\/\-\'\&\#\:\@]*)\s*<\/a>\s*<\/td>\s*<td class=\"stationid\">\s*[A-Z0-9]*\s*<\/td>\s*<td class=\"latitude\">\s*(\+?\-?[0-9]*\.[0-9]*)\s*<\/td>\s*<td class=\"longitude\">\s*(\+?\-?[0-9]*\.[0-9]*)\s*<\/td>\s*<td class=\"pred_type\">\s*<?b?>?\s*([a-zA-Z]*)\s*<?\/?b?>?\s*<\/td>\s*<\/tr>', soupy.prettify())

    for j in location_list:
        location_string = str(i) + "_" + j[1] + "_" + j[0]
        master_dict[location_string] = j

    print("master dict length is {}".format(len(master_dict)))
    print("index at {}".format(index))
    index += 1

master_noaa_location_list = open("master_noaa_location_list.txt", "wb")

pickle.dump(master_dict, master_noaa_location_list)

master_noaa_location_list.close()
