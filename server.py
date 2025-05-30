from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from fastapi.responses import RedirectResponse, FileResponse, Response
from fastapi import FastAPI, Query, HTTPException

from datetime import datetime, timedelta
from typing import Callable
from platform import system
from time import time
import logging.handlers
import logging
import random
import os

from flasksite.apienums import Descriptions as describe, Interval, LocId, Org
from flasksite.apihelpers import *
from sqlalch_class_defs import Queries, Result
from constants import *

MAPSINIT_LOC = f"flasksite{SLASH}static{SLASH}script{SLASH}mapsinit.js"

MAX_CACHE_AGE = 20 * 60 # seconds


class CacheEntry():
	def __init__(self, timestamp: int, value):
		self.timestamp = timestamp
		self.value = value

class CacheValues():
	def __init__(self):
		self._values: dict[str, CacheEntry] = {}
	

	def get(self, key: str):
		found = self._values.get(key)

		if (not found): return None
		if (time() - found.timestamp > MAX_CACHE_AGE):
			del self._values[key]
			return None
		
		return found.value
	
	def add(self, key: str, value):
		self._values[key] = CacheEntry(time(), value)

class CacheManager():
	current_wt = CacheValues()
	scripts = CacheValues()
	daily_summaries = CacheValues()
	fcsts_of_day = CacheValues()


def create_session_constructor(engine: Engine) -> Callable[[], Session]:
	return sessionmaker(bind = engine)


def connect_to_db():
	engine = create_engine(
		CONNECION_URL,
		**CONNECTION_KWARGS
	)

	return engine

# TODO: when choosing fcst_time, get one closest, incase is missing
# TODO: clear all cache periodically
# TODO: round jsonified values
# TODO: filter all_daily_results. alwys query for all, but cache, and only return what client wants.


app = FastAPI()
# uvicorn flasksite.testserver:app

SLASH = SLASH

global_cache_manager = CacheManager()
global_engine = connect_to_db()
global_session_constructor = create_session_constructor(global_engine)

if (system() == "Windows"):
	
	@app.get("/static/{path:path}")
	def get_file(path: str):
		print(path)

		return FileResponse("flasksite\\static\\" + path.replace("/","\\"))


	@app.get("/")
	@app.get("/local")
	def main():
		return FileResponse("flasksite\\static\\doc\\main.html")
	
	



@app.get("favicon.ico")
def get_favicon():
	return FileResponse(f"flasksite{SLASH}static{SLASH}favicon.ico")


@app.get("/api/formatted/mapsinit.js")
def get_mapsinit():
	cached = global_cache_manager.scripts.get("mapsinit")
	if (cached): return Response(cached, media_type = "application/javascript")

	f = open(MAPSINIT_LOC, "r")
	data = f.read()
	f.close()

	data = data.replace("__KEY__", GOOG_MAPS_API_K)

	global_cache_manager.scripts.add("mapsinit", data)
	return Response(data, media_type = "application/javascript")



@app.get("/api/info/sites")
def get_site_info(dict: bool = True):
	if (dict): return SITES_BY_INTID
	return ALL_LOCIDS_INTED


@app.get("/api/info/keys")
def get_store_as_keys():
	return REVERSE_JSONIFY_STORE_AS





@app.get("/api/weather/current-photo")
def current_photo(loc_id: str = "all", time_aware: bool = True):
	cached_wt = global_cache_manager.current_wt.get(loc_id)

	if (cached_wt): return RedirectResponse(get_photo_from_wt(cached_wt, time_aware))

	got_wt = Queries.query(
		Queries.get_recent_obs_urgent(loc_id),
		global_session_constructor
	)

	if (not got_wt): return RedirectResponse(get_photo_from_wt(-1, False))

	try: got_wt = got_wt[0][0]
	except: return RedirectResponse(get_photo_from_wt(-1, False))

	global_cache_manager.current_wt.add(loc_id, got_wt)

	return RedirectResponse(get_photo_from_wt(got_wt, time_aware))




@app.get("/api/weather/forecasts-of")
def get_forecasts(
	loc_id: int,
	day_date: datetime | str = Query(..., description = describe.future_time),
	days: int = 1
):
	if (loc_id == "all"): return HTTPException(400, "loc_id cannot be \'all\'.")

	day_date = InterpretParam.time(day_date)

	ref = str(loc_id) + str(day_date) + str(days)
	cached = global_cache_manager.fcsts_of_day.get(ref)

	if (cached): return cached

	results = Queries.query(
		Queries.get_fcsts_of_day(loc_id, day_date, days),
		global_session_constructor
	)

	organised = get_organised_fcsts(results)

	global_cache_manager.fcsts_of_day.add(ref, organised)

	return organised





@app.get("/api/results/daily")
def get_all_daily_results(
	day_date: datetime | str = Query(..., description = describe.future_time),
	countback_days: int = Query(0, description = describe.countback_days),
	fcst_time_buffer_days: int = Query(2, description = describe.fcst_time_buffer_days)
):
	day_date = InterpretParam.time(day_date)

	ref = str(day_date) + str(countback_days) + str(fcst_time_buffer_days)
	cached = global_cache_manager.daily_summaries.get(ref)

	if (cached): return cached

	results = Queries.query(
		Queries.get_daily_summaries(
			min_future_time_inc = day_date - timedelta(days = countback_days - 1),
			max_future_time_exc = day_date + timedelta(days = 1),
			fcst_time_buffer_days = fcst_time_buffer_days
		),
		global_session_constructor
	)

	#jsoned_graded_results = [ get_json_graded_result(r) for r in results ]#[ r.jsonify() for r in results]#
	
	orgainsed = get_organised_json_results(results)

	global_cache_manager.daily_summaries.add(ref, orgainsed)

	return orgainsed







@app.get("/api/debug/log-today")
def get_logs(key: str):
	if (key != MY_API_K):
		raise HTTPException(403)
	
	return FileResponse("collection.log")