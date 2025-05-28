from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from fastapi.responses import FileResponse
from fastapi import FastAPI, Query

from datetime import datetime, timedelta
from typing import Callable
from time import time
import logging.handlers
import logging
import random
import os

from apienums import Descriptions as describe, Interval, LocId, Org
from sqlalch_class_defs import Queries
import constants


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
		
		return found
	
	def add(self, key: str, value):
		self._values[key] = CacheEntry(time(), value)

class CacheManager():
	current_wt = CacheValues()


def create_session_constructor(engine: Engine) -> Callable[[], Session]:
	return sessionmaker(bind = engine)


def connect_to_db():
	engine = create_engine(
		constants.CONNECION_URL,
		**constants.CONNECTION_KWARGS
	)

	return engine




app = FastAPI()
# uvicorn flasksite.testserver:app

global_cache_manager = CacheManager()
global_engine = connect_to_db()
global_session_constructor = create_session_constructor(global_engine)


@app.get("/api/weather/current-photo")
def current_photo(loc_id: LocId = "wholeuk"):
	cached_wt = global_cache_manager.current_wt.get(loc_id)

	if (cached_wt): return constants.get_photo_from_wt(cached_wt)

	got_wt = Queries.query(
		Queries.get_recent_obs_urgent,
		global_session_constructor
	)

	if (not got_wt): return constants.get_photo_from_wt(-1)

	global_cache_manager.current_wt.add(loc_id, got_wt)

	return constants.get_photo_from_wt(got_wt)



@app.get("/api/results/{interval}")
def get_eval_result(
	interval: Interval = Query(..., description = describe.interval),
	loc_id: LocId = Query(..., description = describe.loc_id),
	orgs: list[Org] = Query(..., description = describe.org),
	count_per_org: int = Query(1, description = describe.count),

):
	...

	# when choosing fcst_time, get one closest, incase is missing