from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from datetime import datetime, timezone, timedelta
from datetime import time as datetime_time
from bs4 import BeautifulSoup
from typing import Callable
import logging.handlers
import threading # daemon = end when main thread ends
import requests
import logging
import time
import copy
import re
#DEPENDENCY: LXML FOR BS4, mysql-connector-python

from constants import *
from weather_types import convert_wt_to_common
from evaluation import eval_day_of_forecast_instances

from sqlalch_class_defs import Base, DirtyOBS, FCST, Queries, CleanOBS

db_commit_queue = []
db_responses = {}
total_changes = 0

JOB_DEFAULT_WORKLOADS = {
	"MOBS": ALL_LOCIDS.copy(),
	"BOBS": ALL_LOCIDS.copy(),
	"OOBS": ALL_LOCIDS.copy(),
	"B1FCST": ALL_LOCIDS.copy(),
	"M1FCST": ALL_LOCIDS.copy(),
	"M3FCST": ALL_LOCIDS.copy(),
	"DOBS": ALL_LOCIDS.copy(),
	"BDFCST": ALL_LOCIDS.copy(),
	"CLEAN": ["clean"],
	"COMPARE": ["compare"]
}

JOB_SCHEDULE = {
	"??:00": ["MOBS", "BOBS", "OOBS"],
	"00:00": ["B1FCST"],
	"01:00": ["M1FCST", "M3FCST", "DOBS"],  # MUST DPOBS BEFORE clean.
	"02:00": ["CLEAN"],						# MUST clean before compare. clean includes dpobs, which WILL be useful for compare.
	"03:00": ["COMPARE"],					# change COMPARE_HOUR constant if moving schedule
	"06:00": ["BDFCST"] 					# change BBCDFCST_HOUR constant if moving schedule
}

# how to determine execution order, NOT by changing order in schedule.
JOB_PRIORITY = ["MOBS", "DOBS", "OOBS", "BOBS", "B1FCST", "M1FCST", "M3FCST", "BDFCST", "CLEAN", "COMPARE"]

JOBS = {
	"MOBS": [],
	"BOBS": [],
	"OOBS": [],
	"B1FCST": [],
	"M1FCST": [],
	"M3FCST": [],
	"DOBS": [],
	"BDFCST": [],
	"CLEAN":[],
	"COMPARE": [],
	"waitingforcommit": []
}





log_file_handler = logging.handlers.TimedRotatingFileHandler(
	filename = "collection.log",
	when = "midnight",
	utc = True,
	atTime = datetime_time(23, 55),
	backupCount = 14 # n of log files to keep
)

log_file_formatter = logging.Formatter(
	fmt = "%(asctime)s - %(levelname)-8s IN %(threadName)-20s :  %(message)s",
	datefmt = "%d-%m-%y %H:%M:%S"
)
log_file_handler.setFormatter(log_file_formatter)

logger = logging.getLogger("mylogger")
logger.setLevel(logging.DEBUG)
logger.addHandler(log_file_handler)

console = logging.StreamHandler()
console.setFormatter(log_file_formatter)
logger.addHandler(console)



def notify(message: str):
	logger.info(message)

	try:
		requests.post(
			url = DC_ONE_WEBHOOK,
			data = {"content": message[:2000]}
		)
	except Exception:
		logger.exception("COULDNT POST NOTIFY MESSAGE")


def notify_jobs(hour_fmt: str, msg_to_start_with: str):
	start_msg = f"{msg_to_start_with}\n{hour_fmt} starting jobs:"
	msg = start_msg

	total_jobs = 0

	for job, details in JOBS.items():
		items = ", ".join([str(v) for v in details])

		total_jobs += len(details)

		msg += f"\n{job}: [{items}]"
	
	if (total_jobs == 0):
		if (msg_to_start_with): notify(start_msg + "\nNo jobs running.")

		logger.info(f"{hour_fmt} not notifying jobs, none of them.")
		return
	
	notify(msg)


def time_to_str(t: datetime = None, short: bool = False):
	if (t == None): t = datetime.now(TIMEZONE)

	if (short): return t.strftime("%H:%M")

	return t.strftime(DATE_FMT)


def str_to_time(s: str):
	return datetime.strptime(s + "Z", DATE_FMT + "%z")

def compass_string_to_degrees(name: str, is_letters: bool = False):
	name = name.lower().replace(" ","").replace("erly", "")
	
	if (is_letters):
		name = name\
			.replace("N","north")\
			.replace("E","east")\
			.replace("S","south")\
			.replace("W","west")
		
	# 360 / ... to get degrees per change, X by
	# distance around compass

	return COMPASS.index(name) * (360 / len(COMPASS))

def get_next_run_time():
	now = datetime.now(TIMEZONE)
	now -= timedelta(seconds = now.second, microseconds = now.microsecond)

	return now + timedelta(minutes = (10 - (now.minute % 10)))

def ceil_round_nearest_hr(minus_one_min: bool, t: datetime = None):
	"""Round up to the nearest hour, using datetime.now() or provided datetime object."""

	if (not t): t = datetime.now(TIMEZONE)

	t -= timedelta(seconds = t.second, microseconds = t.microsecond)
	t += timedelta(minutes = 60 - t.minute)

	if (minus_one_min): t -= timedelta(minutes=1)

	return t

def validate_data(func: str, data: dict | str):
	match func:
		case "BOBS" | "BDFCST":
			# check is xml-able
			try:
				BeautifulSoup(data, "xml")

			except Exception as err:
				logger.warning("BBC RESPONSE not XML-ABLE")

				return False
			
			return True
		
		case "B1FCST":
			if (not data): return False

			if (not data.get("forecasts")): return False

			return True
		
		case "MOBS":
			if (not data): return False
			
			d_type = data.get("type")

			if (not d_type): return False

			if (d_type == "FeatureCollection"):
				if (not data.get("features")): return False
				if (len(data["features"]) == 0): return False
			
			elif (d_type == "Feature"):
				properties = data.get("properties")

				if (not properties): return False
				if (not properties.get("reportStartDateTime")): return False

				primary = properties.get("primary")
				
				if (not primary): return False
				if (len(primary.keys()) == 0): return False
			
			else:
				logger.warning(f"MOOBS DATA FEATURE TYPE NOT RECOGNISED: {d_type}\nDATA: {data}")
				return False

			return True
		
		case "M1FCST" | "M3FCST":
			if (not data): return False

			features = data.get("features")

			if (not features): return False
			if (len(features) == 0): return False
			
			properties = features[0].get("properties")

			if (not properties): return False
			if (not properties.get("modelRunDate")): return False
			if (not properties.get("location")): return False
			if (not properties["location"].get("name")): return False

			time_series = properties.get("timeSeries")

			if (not time_series): return False
			if (len(time_series) == 0): return False

			return True
		
		case "DOBS":
			if (not data): return False

			site_rep = data.get("SiteRep")
			if (not site_rep): return False

			dv = site_rep.get("DV")
			if (not dv): return False
			if (not dv.get("dataDate")): return False

			location = dv.get("Location")
			if (not location): return False
			if (len(location) == 0): return False

			return True
		
		case "OOBS":
			if (not data): return False

			if (not data.get("weather")): return False
			if (not data["weather"][0].get("id")): return False

			main = data.get("main")
			if (not main): return False
			if (len(main.keys()) == 0): return False

			return True
				
		case _:
			logger.error(f"WHAT IS {func} FUNC? (VALIDATE DATA)")
			return False
		

def get_date_from_data(func: str, data: dict | str):
	date = None

	match func:
		case "BOBS" | "BDFCST":
			soup = BeautifulSoup(data, "xml")

			date_tag = soup.find("dc:date")
			date = datetime.strptime(date_tag.contents[0], BBC_DEFAULT_DATE_FMT)

		case "B1FCST":
			date_str = data["lastUpdated"]
			date = datetime.strptime(date_str, BBC_EXACT_DATE_FMT)
		
		case "MOBS": # must be specific location, not whole data
			assert data["type"] == "Feature" # not FeatureCollection

			date_str = data["properties"]["reportStartDateTime"]
			date = datetime.strptime(date_str, MO_OBS_RESP_DATE_FMT)
		
		case "M1FCST" | "M3FCST":
			date_str = data["features"][0]["properties"]["modelRunDate"]
			date = datetime.strptime(date_str, MO_DEFAULT_DATE_FMT)

		case "OOBS":
			dt = data["dt"]
			# tz_secs = data["timezone"] 3600: +1hr
			# still not quite sure on fromtimestamp.
			# seems to work from system timezone.

			date = datetime.fromtimestamp(dt, TIMEZONE)
		
		case _:
			logger.error(f"WHAT IS {func} FUNC? (GET DATA DATE)")

	
	if (not date): return

	date = date.astimezone(TIMEZONE)

	return date







def get_gathered_obs_values(rows: list[DirtyOBS]):
	obs_by_org = {v.org: v for v in rows}

	clean_obj = CleanOBS(
		mid = rows[0].mid,
		dt = rows[0].dt
	)

	for k, priorities in WEATHER_CONDITION_PRIORITIES.items():
		chosen_value = None

		for org in priorities:
			org_obj = obs_by_org.get(org)

			if (not org_obj): continue

			val = None
			try:
				val = org_obj.__getattribute__(k)
			except: continue
			if (not val): continue

			# DP is horrible, instead of returning null returns 0 sometimes.
			# would rather have no reading than an incorrect one.
			if (org == "D" and val == 0): continue 

			chosen_value = val
			break

		clean_obj.__setattr__(k, chosen_value)

	return clean_obj



def db_commit_loop(engine: Engine):
	global db_responses, db_commit_queue

	def get_debug_str(tracking: str, next_item: dict, ql: int, good):
		_id = next_item.get("id")

		task_detail = []

		query = next_item.get("query")
		objs = next_item.get("objs")
		updates = next_item.get("updates")

		if (query): task_detail.append(query.__name__)
		if (objs): task_detail.append(f"add {len(objs)} objs: " + ",".join(o.__name__ for o in objs))
		if (updates): task_detail.append(f"update {len(updates.keys())} items")

		task_str = ""
		if (task_detail): task_str = " (" + ", ".join(task_detail) + ")"


		return_detail = []

		if (type(good) == list): return_detail.append(f"len {len(good)}")
		if (type(good) == bool): return_detail.append(str(good))

		return_str = ""
		if (return_detail): return_str = " (" + ", ".join(return_detail) + ")"


		s = f"{tracking}completed task {_id}{task_str} with {ql - 1} left. good? {not not good}. returning a {type(good).__name__}{return_str}"
		return s
	

	def do_item(session: Session, item: dict): # must be QUERY ONLY, or ANY AMOUNT FROM [UPDATES, OBJS]
		if (item.get("query")): return item["query"](session)

		return_val = None

		if (item.get("objs")):
			for obj in item["objs"]:
				session.add(obj)
			
			return_val = True

		if (item.get("updates")):
			for obj, new_vals in item["updates"].items():
				obj = session.merge(obj)
				
				for k,v in new_vals.items():
					setattr(obj, k, v)
			
			return_val = True
		
		if (return_val != None):
			session.commit()
		
		return return_val	



	session_constructor = create_session_constructor(engine)

	did_last_time = False

	#tracking = "DB TASK:"
	tracking = ""# f"{tracking:<{TRACKING_STR_LEN}}"

	while True:
		time.sleep(DB_COMMIT_FREQ_FAST if did_last_time else DB_COMMIT_FREQ_SLOW)

		ql = len(db_commit_queue)

		if ((ql != 0 and not did_last_time) or (ql == 0 and did_last_time)):
			logger.debug(f"{tracking}db queue {ql} {did_last_time}")

		if (ql == 0):
			did_last_time = False
			continue

		next_item = None
		good = False
		session = None

		try:
			next_item = db_commit_queue[0]
			if (not next_item): continue

			session = session_constructor()

			good = do_item(session, next_item)		

		except Exception as err:
			logger.error(f"{tracking}ERR OCCURED FOR DB COMMIT, rolling back:\n{err}")
			session.rollback()

			if ("MySQL Connection not available" in str(err) or "server has gone away" in str(err)):
				logger.critical("Disposing engine due to connection error")
				engine.dispose()
		
		finally:
			if (session): session.close()


		if (next_item):
			_id = next_item.get("id")

			try:     logger.info(get_debug_str(tracking, next_item, ql, good))
			except:  logger.info(f"completed task {_id} with {ql - 1} left. good? {not not good}.")

			db_commit_queue.pop(0)
		
			if (next_item["return_response"]):
				db_responses[_id] = good

			did_last_time = True
		
		else: did_last_time = False


def db_commit_thread():
	engine = connect_to_db()

	while True:
		try:
			if (not engine): engine = connect_to_db()

			db_commit_loop(engine)
			
		except Exception as err:
			logger.exception("CRITICAL: db_commit_loop errored")
		
		time.sleep(2)



def wait_for_db_resp_thread(this_id: int, resolve: Callable = None):
	global db_responses

	# wait for response
	start = time.time()

	while True:
		time.sleep(DB_COMMIT_FREQ_SLOW)
		
		if (time.time() - start > MAX_WAIT_FOR_DB_RESP):
			return False

		resp = db_responses.get(this_id)

		if (resp == None): continue
		del db_responses[this_id]

		if (resolve): resolve(resp)

		return resp


def invoke_db(objs: list[DirtyOBS | FCST] = None, query: str = None, updates: dict = None, wait: bool = True, resolve: Callable = None):
	"""One of resolve or wait maximum. If resolve supplied, thread will be called and not joined."""
	global total_changes, db_commit_queue, db_responses

	total_changes += 1

	this_id = total_changes

	request = {"id": this_id, "return_response": wait or resolve}

	if (objs): request["objs"] = objs
	if (query): request["query"] = query
	if (updates): request["updates"] = updates

	db_commit_queue.append(request)

	if (wait or resolve):
		thread = ThreadThatReturns(
			target = wait_for_db_resp_thread,
			name = f"DBResp{this_id}",
			args = [this_id, resolve],
			daemon = True
		)

		thread.start()
		
		if (not wait): return

		response = thread.join()		
		return response

	

def create_session_constructor(engine: Engine) -> Callable[[], Session]:
	return sessionmaker(bind = engine)


def connect_to_db():
	engine = create_engine(
		CONNECION_URL,
		**CONNECTION_KWARGS
	)

	return engine



def daily_fcst_evaluate(detail: str = "COMPAREcompare"):
	JOBS["waitingforcommit"].append(detail)

	result = invoke_db(query = Queries.get_fcsts_to_eval)
	grouped = {}

	row: FCST
	for row in (result or []):
		key = (row.mid, row.org, row.fcst_time)

		if (not grouped.get(key)): grouped[key] = []
		grouped[key].append(row)
	
	if (not grouped):
		JOBS["COMPARE"] = []

		try: JOBS["waitingforcommit"].remove(detail)
		except: pass

		return
	
	for k, rows in grouped.items():
		logger.debug(f"KEY DOING {k}")
		future_times = [fcst.future_time for fcst in rows]

		mid, org, fcst_time = k
		period = 3 if (org == "M3") else 24 if (org == "BD") else 1

		obs = invoke_db(
			query = Queries.get_obs_between_times(
				min(future_times), 
				max(future_times) + timedelta(hours = period), 
				mid
			),
			wait = True
		)

		try:
			changes = eval_day_of_forecast_instances(obs, rows, org)
		except Exception:
			logger.exception(f"ERR EVALING KEY {k}")
		if (not changes): continue

		invoke_db(**changes, wait = False)


	JOBS["COMPARE"] = []

	try: JOBS["waitingforcommit"].remove(detail)
	except: pass



	



def hourly_obs_clean(detail: str = "CLEANclean"):
	#tracking = f"{"OBSCLEAN:":<{TRACKING_STR_LEN}}"

	JOBS["waitingforcommit"].append(detail)
	
	result = invoke_db(query = Queries.get_dirtyobs_older_than_buffer)
	grouped = {}

	row: DirtyOBS
	for row in (result or []):
		key = (row.mid, row.dt)

		if (not grouped.get(key)): grouped[key] = []
		grouped[key].append(row)
	

	if (not grouped):
		JOBS["CLEAN"] = []

		try: JOBS["waitingforcommit"].remove(detail)
		except: pass

		return

	
	for k, rows in grouped.items():
		#already_clean = invoke_db(
		#	query = Queries.get_obs(k[0], k[1]),
		#	wait = True
		#)

		#if (already_clean):
		#	updates = {v: {"has_cleaned": False} for v in rows}
		#	invoke_db(updates = updates, wait = False)

		#	continue


		clean_obj = get_gathered_obs_values(rows)

		updates = {v: {"has_cleaned": True} for v in rows}
		invoke_db(
			objs = [clean_obj],
			updates = updates,
			wait = False#,
			#resolve = {
			#	"func": cleaning_db_invoke_callback,
			#	"args": []
			#}
		)
	

	JOBS["CLEAN"] = []

	try: JOBS["waitingforcommit"].remove(detail)
	except: pass






def bbcd_value_corrector(k: str, v: str | int):
	match k:
		case "Temperature" | "Minimum Temperature" | "Maximum Temperature":
			temp = re.findall("(\\d+)°C", v)[0] # exclude (farenheight)

			v = int(temp)
		
		case "Wind Direction":
			v = compass_string_to_degrees(v)

		case "Wind Speed":
			mph = re.findall("(\\d+)", v)[0]

			v = int(mph) * MILE_TO_KM

		case "Humidity" | "Pressure":
			v = int(re.findall("(\\d+)", v)[0])
		
		case "Visibility":
			v = bbc_convert_vis_str_to_int(v)

	return v


def json_value_corrector(func: str, k: str, v: str | int):
	if (func == "B1FCST"):
		if (k == "windDirectionFull"): v = compass_string_to_degrees(v)
		elif (k == "visibility"): v = bbc_convert_vis_str_to_int(v)
		elif (k == "weatherType"): v = convert_wt_to_common("B1", v)


	elif (func == "M1FCST" or func == "M3FCST"):
		if (k == "time"): v = datetime.strptime(v, MO_DEFAULT_DATE_FMT).astimezone(TIMEZONE)
		elif (k == "visibility"): v /= 1000
		elif (k == "mslp"): v /= 100 # 100 NOT 1000!!
		elif (k == "windSpeed10m" or k == "windGustSpeed10m"): v *= METRE_SEC_TO_KM_HR
		elif (k == "significantWeatherCode"): v = convert_wt_to_common(func.replace("FCST",""), v)
	

	elif (func == "MOBS"):
		if (k == "dws"): v *= KNOT_TO_KM
		elif (k == "dwt"): v = convert_wt_to_common(func.replace("OBS",""), v)
	

	elif (func == "DOBS"):
		if (k == "V"): v = int(v) / 1000
		elif (k == "D"): v = compass_string_to_degrees(v, True)
		elif (k == "G" or k == "S"): v = int(v) * MILE_TO_KM
		elif (k == "W"): v = convert_wt_to_common(func.replace("OBS", ""), v)


	elif (func == "OOBS"):
		if (k == "wind_speed" or k == "wind_gust"): v *= METRE_SEC_TO_KM_HR	
		elif (k == "visibility"): v /= 1000	
		elif (k == "weather_id"): v = convert_wt_to_common("O", v)
	
	return v


def save_from_xml(func: str, mId: str, batch_time: datetime, data_date: datetime, data: bytes):
	is_fcst = "FCST" in func

	soup = BeautifulSoup(data, "xml")
	weather_items = soup.find_all("item")

	obj = FCST if is_fcst else DirtyOBS

	all_periods = []

	for i, weather_item in enumerate(weather_items):
		to_store = obj(
			mid = mId,
			org = "BD" if is_fcst else "B"
		)

		if (is_fcst):
			fcst_time = batch_time - timedelta(hours = batch_time.hour)

			to_store.fcst_time = fcst_time
			to_store.future_time = fcst_time + timedelta(days = i)

		else: to_store.dt = data_date

		title = weather_item.find("title")
		description = weather_item.find("description")

		title = str(title.contents[0])
		description = str(description.contents[0])

		colon_index = title.find(": ")

		comma_index = title.find(",", colon_index) # get first comma
		weather_type = title[colon_index + 2 : comma_index] # +2, start is inclusive, remove space.

		to_store.wt = convert_wt_to_common("B", weather_type)

		parts = description.split(", ")

		for part in parts:
			k_v_split = part.split(": ")

			if (len(k_v_split) != 2): continue # Pressure: "1024mb, Falling, Vis..."

			condition, value = k_v_split
			store_key = BBCD_DB_CONDITION_NAMES.get(condition)

			if (not store_key): continue # i don't want this field
			if (value.find("--") != -1): continue

			try: value = bbcd_value_corrector(condition, value)
			except: continue

			to_store.__setattr__(store_key, value)
		
		all_periods.append(to_store)

	return all_periods


def save_from_json(func: str, mId: str, batch_time: datetime, data_date: datetime, data: list[dict]):
	is_fcst = "FCST" in func
	all_periods = []

	obj = FCST if is_fcst else DirtyOBS

	condition_names = None

	match func:
		case "B1FCST": condition_names = BBC1_DB_CONDITION_NAMES
		case "MOBS": condition_names = MOO_DB_CONDITION_NAMES
		case "M1FCST": condition_names = MOF1_DB_CONDITION_NAMES
		case "M3FCST": condition_names = MOF3_DB_CONDITION_NAMES
		case "DOBS": condition_names = DP_DB_CONDITION_NAMES
		case "OOBS": condition_names = OWM_DB_CONDITION_NAMES
	
	org = func.replace("FCST","").replace("OBS","")
	
	for report in data:
		to_store = obj(
			mid = mId,
			org = org
		)

		if (is_fcst):
			if ("B1" in func): to_store.fcst_time = batch_time
			else: to_store.fcst_time = data_date
		
		else:
			to_store.dt = data_date - timedelta(minutes = data_date.minute, seconds = data_date.second)

		for original_k, tostore_k in condition_names.items():
			v = report.get(original_k)
			if (v == None): continue

			try: v = json_value_corrector(func, original_k, v)
			except: continue

			to_store.__setattr__(tostore_k, v)
		
		if (func == "B1FCST"):
			to_store.future_time = datetime.strptime(report["localDate"] + report["timeslot"], BBC1FCST_DATE_FMT)
	
		all_periods.append(to_store)
	
	return all_periods





def send_request(func: str, mId: str, batch_time: datetime, fileId: str = None, tracking: str = "", allow_non_json: bool = False):
	location = None
	if (mId): location = SITES_BY_ID[mId]

	endpoint = None
	headers = {}

	match func:
		case "BOBS": endpoint = BBC_OBS_ENDPOINT.format(location["bId"])
		case "BDFCST": endpoint = BBCD_FCST_ENDPOINT.format(location["bId"])
		case "B1FCST": endpoint = BBC1_FCST_ENDPOINT.format(location["bId"])
		case "MOBS":
			t = ceil_round_nearest_hr(True, batch_time) # must do this. 13:00 data = request url 14:59

			endpoint = MO_OBS_ENDPOINT.format(t.strftime(MO_OBS_ENDPOINT_DATE_FMT))
			headers = {"Referer":"https://wow.metoffice.gov.uk/"}

		case "M1FCST":
			endpoint = MO1_FCST_ENDPOINT.format(lat = location["lat"], long = location["long"])
			headers = {"apikey": MO_GS_K}

		case "M3FCST":
			endpoint = MO3_FCST_ENDPOINT.format(lat = location["lat"], long = location["long"])
			headers = {"apikey": MO_GS_K}
		
		case "DOBS": endpoint = DP_OBS_ENDPOINT
		case "OOBS":
			endpoint = OWM_OBS_ENDPOINT.format(lat = location["lat"], long = location["long"], key = OWM_K)
	

	logger.debug(f"{tracking}{endpoint}")


	try: response = requests.get(url = endpoint, headers = headers, stream = True)
	except Exception:
		logger.exception(f"{tracking}REQUEST ERRORED:\nENDPOINT:{endpoint}")
		return None

	if (response.status_code != 200):
		logger.error(f"{tracking}STATUS CODE {response.status_code}\nENDPOINT:{endpoint}\nRESP TEXT:{response.text}")
		return
	
	try:
		data = response.json()
		return data

	except requests.JSONDecodeError:
		if (allow_non_json): return response.content
		else: return None


def get(func: str, mId: str, batch_time: datetime, wanted_model_run_time: datetime, tracking: str = ""):
	allow_non_json = True if (func == "BDFCST" or func == "BOBS") else False
	
	data = send_request(func, mId, batch_time, tracking = tracking, allow_non_json = allow_non_json)

	if (not data): return
	if (not validate_data(func, data)):
		logger.warning(f"{tracking}DATA NOT VALID {data}")
		return

	data_date = get_date_from_data(func, data)
	if (not data_date): return

	if (data_date < wanted_model_run_time):
		logger.warning(f"{tracking}returned old data. wanted: {time_to_str(wanted_model_run_time)}, got: {time_to_str(data_date)}")
		return

	# SUCCESS
	datas = []

	match func:
		case "BOBS" | "BDFCST":
			datas = save_from_xml(func, mId, batch_time, data_date, data)

		case "B1FCST":
			wanted_data = [] # NOT doing summary, already get that thru rss.

			# flatten dict
			for day in data["forecasts"]:
				if (not day.get("detailed")): continue
				if (not day["detailed"].get("reports")): continue

				for report in day["detailed"]["reports"]:
					wanted_data.append(report)

			datas = save_from_json(func, mId, batch_time, data_date, wanted_data)

		case "M1FCST" | "M3FCST":
			wanted_data = data["features"][0]["properties"]["timeSeries"]
			datas = save_from_json(func, mId, batch_time, data_date, wanted_data)

		case "OOBS":
			wanted_data = {}

			data["weather"] = data["weather"][0] # is a list, containing 1 dict with id,description,icon. -> dict.

			# flatten dict into 2 dimensions
			for k,v in data.items():
				if (type(v) != dict):
					wanted_data[k] = v
					continue

				for kk,vv in v.items():
					wanted_data[f"{k}_{kk}"] = vv

			datas = save_from_json(func, mId, batch_time, data_date, [wanted_data])

		case _:
			logger.error(f"{tracking}WHAT IS THIS FUNCTION IM NOT SAVING THAT: {func}")
	
	return [datas]


def get_multi_from_one_request_moobs(func: str, task: list[str], batch_time: datetime, wanted_model_run_time: datetime, tracking: str = ""):
	if (len(task) == 0): return

	data = send_request(func, None, batch_time)

	if (not data): return
	if (not validate_data(func, data)):
		logger.warning(f"{tracking}DATA NOT VALID {data}")
		return


	datas = []
	
	for report in data["features"]:
		if (len(datas) == len(task)): break # got all needed

		if (not validate_data(func, report)):
			logger.warning(f"{tracking}DATA NOT VALID {report}")
			continue

		mId = report["properties"]["siteId"]
		if (not mId in task): continue

		data_date = get_date_from_data(func, report)
		
		if (data_date < wanted_model_run_time):
			logger.warning(f"{tracking}{mId} returned old data. wanted: {time_to_str(wanted_model_run_time)}, got: {time_to_str(data_date)}")
			continue

		to_store: list = save_from_json(func, mId, batch_time, data_date, [report["properties"]["primary"]])
		datas.append(to_store)
	
	return datas# [[to_store], [to_store]]



def get_multi_from_one_request_dpobs(func: str, task: list[str], batch_time: datetime, wanted_model_run_time: datetime, tracking: str = ""):
	if (len(task) == 0): return

	data = send_request(func, None, batch_time)

	if (not data): return
	if (not validate_data(func, data)):
		logger.warning(f"{tracking}DATA NOT VALID {data}")
		return
	
	if (func == "DOBS"):
		data_date_str = data["SiteRep"]["DV"]["dataDate"]
		data_date = datetime.strptime(data_date_str, DP_OBS_MAIN_DATE_FMT)

		if (data_date < wanted_model_run_time):
			logger.warning(f"{tracking}returned old data. wanted: {time_to_str(wanted_model_run_time)}, got: {time_to_str(data_date)}")
			return


	datas = []
	
	for loc in data["SiteRep"]["DV"]["Location"]:
		if (len(datas) == len(task)): break # got all needed

		site = SITES_BY_DID.get(loc["i"])
		if (not site): continue

		mId = site["mId"]
		if (not mId in task): continue

		datas_this_loc = []

		day_of_periods = loc["Period"] # 1am: {1am,2am,3am...,11pm},{$:0,"D":1,..}
		if (type(day_of_periods) == dict): day_of_periods = [day_of_periods] # !!

		for day in day_of_periods:
			day_dt = datetime.strptime(day["value"], DP_OBS_DAY_DATE_FMT)

			reports = day["Rep"]
			if (type(reports) == dict): reports = [reports] # DP IS THE WORST!!

			for report in reports:
				data_date = day_dt + timedelta(minutes=int(report["$"]))

				to_store = save_from_json(func, mId, batch_time, data_date, [report])
				datas_this_loc.append(to_store[0])
		
		datas.append(datas_this_loc)
	
	return datas# [[to_store], [to_store]]



def do_job(func: str, detail: str | list[str], batch_time: datetime, wanted_model_run_time: datetime):
	data_groups = None

	tracking = ""#func # prefix for logs

	if (type(detail) == list): tracking += str(len(detail)) + ":"
	else: tracking += detail + ":"

	tracking = ""#f"{tracking:<{TRACKING_STR_LEN}}"


	logger.info(f"{tracking}doing job {wanted_model_run_time}")
	data_groups = []

	try:
		match func:
			case "BOBS" | "OOBS" | "B1FCST" | "BDFCST" | "M1FCST" | "M3FCST":
				data_groups = get(func, detail, batch_time, wanted_model_run_time, tracking)
			
			case "MOBS":
				data_groups = get_multi_from_one_request_moobs(func, detail, batch_time, wanted_model_run_time, tracking)

			case "DOBS":
				data_groups = get_multi_from_one_request_dpobs(func, detail, batch_time, wanted_model_run_time, tracking)
			
			case "CLEAN":
				hourly_obs_clean("CLEANclean")

			case "COMPARE":
				daily_fcst_evaluate("COMPAREcompare")
	except Exception:
		logger.exception(f"ERR DOING JOB {func}{detail}")

	if (not data_groups):
		logger.debug(f"{tracking}no data")
		return

	for datas in data_groups:
		if (len(datas) == 0): continue

		this_detail = datas[0].mid # have to have this, not detail_str!
		id_ = func + this_detail
		JOBS["waitingforcommit"].append(id_)

		try:
			result = invoke_db(objs = datas)
		except Exception:
			logger.exception(f"{tracking}err adding change to db {this_detail}")
		

		try: JOBS["waitingforcommit"].remove(id_)
		except: pass

		if (result == True):
			try: JOBS[func].remove(this_detail)
			except: pass


def launch_job(func: str, detail: str, batch_time: datetime, wanted_model_run_time: datetime):
	detail_str = func if type(detail) != str else detail
	id_ = func + detail_str

	if (id_ in JOBS["waitingforcommit"]):
		logging.warning(f"{id_} is waiting to commit, not launching job again")
		return
	
	t = threading.Thread(
		target = do_job,
		name = f"{id_}_{time_to_str(batch_time, True)}",
		args = [func, detail, batch_time, wanted_model_run_time],
		daemon = True
	)

	t.start()

def launch_db_commit():
	t = threading.Thread(
		target = db_commit_thread,
		name = f"DB_COMMIT",
		daemon = True
	)

	t.start()


def register_jobs(hour_fmt: str):

	def refill_jobs(schedule_period: str):
		for job in JOB_SCHEDULE[schedule_period]:
			default_details = JOB_DEFAULT_WORKLOADS[job]

			for detail in default_details:
				if (detail in JOBS[job]): continue

				JOBS[job].append(detail)


	if (hour_fmt.endswith(":00")): refill_jobs("??:00")
			

	for hour in JOB_SCHEDULE.keys():
		if (hour_fmt != hour): continue

		refill_jobs(hour)



def every_10_mins(batch_time: datetime, _testing_hour_fmt: str = None):
	global db_commit_queue

	if (_testing_hour_fmt): hour_fmt = _testing_hour_fmt
	else: hour_fmt = time_to_str(batch_time, True)

	batch_time -= timedelta(minutes=batch_time.minute)
	wanted_model_run_time = batch_time - timedelta(hours=1)

	register_jobs(hour_fmt)

	jobs_copy = copy.deepcopy(JOBS)

	msg_to_start_with = ""
	if (len(db_commit_queue) > 0):
		msg_to_start_with = f"DB commit queue rolled over into next period, {len(db_commit_queue)} items."

	notify_jobs(hour_fmt, msg_to_start_with)

	to_wait_each = min(RUN_SLOW_MAX_COOLDOWN, (EVENT_LOOP_EVERY * 0.8) / len(jobs_copy))

	for job in JOB_PRIORITY:
		details = jobs_copy[job]

		if (job == "MOBS" or job == "DOBS"):
			if (len(details) == 0): continue
			details = [details]

		for detail in details:
			try:
				launch_job(job, detail, batch_time, wanted_model_run_time)
			except Exception:
				logger.exception(f"do_job {job} {detail}")

			time.sleep(to_wait_each)


def start_loop():
	while True:
		now = datetime.now(TIMEZONE)

		next_run_time = get_next_run_time()
		time_to_wait = (next_run_time - now).total_seconds()

		logger.debug(f"{next_run_time} waiting seconds {time_to_wait}")

		time.sleep(time_to_wait)

		every_10_mins(next_run_time)

		time.sleep(10) # for testing, to stop fast loop



def ensure_default_obs(query_resp: list[CleanOBS]):
	if ((query_resp) and len(query_resp) > 0):
		logger.info("default OBS(id=-1) exists.")
		return
	
	new_obj = CleanOBS(
		id = -1,
		mid = 0,
		dt = datetime.fromtimestamp(0)
	)

	invoke_db(objs = [new_obj])
	
	


def main():
	notify(f"All times are UTC/GMT. Starting at: {time_to_str()}")

	launch_db_commit()

	invoke_db(query = Queries.get_default_obs, wait = False, resolve = ensure_default_obs)

	while True:
		try: start_loop()
		except Exception:
			logger.exception("loop errored")
		
		time.sleep(10)
	

def testing(hour_fmt: str):
	launch_db_commit()

	invoke_db(query = Queries.get_default_obs, wait = False, resolve = ensure_default_obs)

	batch_time = datetime.now(TIMEZONE)
	batch_time -= timedelta(seconds=batch_time.second, minutes=batch_time.minute, microseconds=batch_time.microsecond)
	every_10_mins(batch_time, hour_fmt)

	time.sleep(120)

	every_10_mins(batch_time, "13:10")

	time.sleep(200)


if (__name__ == "__main__"): main()
#testing("15:00")