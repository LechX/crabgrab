import pickle
import requests


location_file = open("master_noaa_location_list.txt", "rb")
location_dictionary = pickle.load(location_file)

location_file.close()

# add if statement to grab only dictionary entries with west coast lat/lon
#
#
#
#
#

brighton_id = '9437815'
station_id = brighton_id

location_xml = requests.get("https://tidesandcurrents.noaa.gov/noaatidepredictions/NOAATidesFacade.jsp?datatype=Annual+XML&Stationid=" + station_id)

print(location_xml.text)
