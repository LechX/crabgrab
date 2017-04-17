import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crabgrab.settings')
django.setup()
from pages.models import Locations, Tides
import time

start_time = time.time()

def remove_tides(state):

    tides = Tides.objects.filter(location__state=state)
    for t in tides:
        print(t.location)
        t.delete()

# remove_tides("Bermuda Islands")
# remove_tides("Oregon")
# remove_tides("Washington")
# remove_tides("California")

# remove_tides("Maine")

print("{} total seconds elapsed".format(time.time() - start_time))
