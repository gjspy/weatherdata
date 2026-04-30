import requests
from time import sleep

from constants import ALL_LOCIDS

RUN_EVERY = 40 * 60 # seconds
URLS = [
	"http://127.0.0.1:8002/api/results/daily?day_date=yesterday&countback_days=30&fcst_time_buffer_days=1",
	*(f"http://127.0.0.1:8002/api/results/daily?day_date=yesterday&countback_days=30&fcst_time_buffer_days=2&loc_id={v}" for v in ALL_LOCIDS)
]



while True:
	try:
		for url in URLS:
			r = requests.get(url)
			print(r.status_code, ": got", url)
		
	except Exception as err:
		print(err)
	
	sleep(RUN_EVERY)
