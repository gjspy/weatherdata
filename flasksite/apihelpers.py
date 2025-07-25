from datetime import datetime, timedelta
import copy
import re

from sqlalch_class_defs import Result, FCST, CleanOBS
from flasksite.grade_definitions import CONDITION_BOUNDARIES
from constants import *

class InterpretParam():

	@staticmethod
	def loc_id(param: list[str]):
		if (param == ["all"]):
			return ALL_LOCIDS.copy()

		return param
	
	@staticmethod
	def time(param: datetime | str):
		if (type(param) == datetime): return param

		try: return datetime.fromisoformat(param)
		except: pass

		if (param == "yesterday"):
			return get_datetime_today() - timedelta(days = 1)
		
		days_ago = int(param.replace("daysago_", ""))
		return get_datetime_today() - timedelta(days = days_ago)
	


def get_grade(boundaries: dict[int, str], value: int):
	if (boundaries == None): return None

	value = abs(value)

	for k,v in boundaries.items():
		if (value <= v): return k
	
	if (list(boundaries.keys())[0] == "A+"): return "F"
	else: return "A+"


def get_json_graded_result(db_result: Result):
	data = {
		"i": db_result.fcst.mid,
		"o": db_result.fcst.org,
		"p": db_result.period,
		"f": get_tzsafe_str_date(db_result.fcst.fcst_time),
		"a": get_tzsafe_str_date(db_result.fcst.future_time),
		"r": {}
	}

	for k in RESULT_CONDITIONS:
		store_as = JSONIFY_STORE_AS.get(k)
		if (not store_as): continue

		db_value = None

		try: db_value = getattr(db_result, k)
		except: pass

		if (db_value != None):
			if   (k.startswith("d_")): db_value = round(db_value, 1)# * sign
			elif (k.startswith("s_")): db_value = round(db_value, 0)# * sign


		if (db_value == None):
			data["r"][store_as] = db_value
			data["r"]["g" + store_as] = None
			continue

		data["r"][store_as] = db_value
		data["r"]["g" + store_as] = get_grade(CONDITION_BOUNDARIES.get(k), db_value)
	
	return data


def get_jsoned_obj(obj: FCST | CleanOBS):
	isfcst = type(obj) == FCST
	conditions = FCST_CONDITIONS if isfcst else OBS_CONDITIONS

	data = {}

	for k in conditions: # NOT metadata (time, org, mid..).
		store_as = JSONIFY_STORE_AS.get(k)
		if (not store_as): continue
		
		v = None
		try: v = getattr(obj, k)
		except: pass

		if (type(v) == float): v = round(v, 1)
		if (store_as == "w"):
			time = getattr(obj, "future_time") if isfcst else getattr(obj, "dt")

			v = edit_wt_for_client(v, time)

		data[store_as] = v
	
	return data




def get_organised_json_results(results: list[Result], key_mode: str = "future_time"):
	key_is_future = key_mode == "future_time"
	data = {}

	for r in results:
		jsoned = get_json_graded_result(r)
		key = jsoned["a"] if key_is_future else jsoned["f"]
		org = jsoned["o"]

		if (not data.get(key)):
			data[key] = {}
		
		if (not data[key].get(org)):
			data[key][org] = {"data": []}
		
		data[key][org]["data"].append(jsoned)



	# CALCULATE AVERAGE GRADE AT EACH LAYER
	for orgs in data.values():

		for org, org_data in orgs.items():
			org_grades = []

			for entry in org_data["data"]:
				entry_grades = []

				for k, v in entry["r"].items():
					if (k.startswith("g")):
						entry_grades.append(v)
				
				entry["ga"] = get_avg_grade(entry_grades)
				org_grades.append(entry["ga"])
			
			org_data["ga"] = get_avg_grade(entry_grades)

	return data



def get_organised_fcsts(fcsts: list[FCST]):
	data = {}

	for f in fcsts:
		if (not data.get(f.org)): data[f.org] = {}

		fcst_time = get_tzsafe_str_date(f.fcst_time)
		future_time = get_tzsafe_str_date(f.future_time)
		if (not data[f.org].get(fcst_time)): data[f.org][fcst_time] = {}

		data[f.org][fcst_time][future_time] = get_jsoned_obj(f)
	

	for org, v in copy.deepcopy(data).items():
		period = 24 if (org == "BD") else 3 if (org == "M3") else 1

		for fcst_time, vs in v.items():
			if (len(vs.keys()) < 24/period): 
				del data[org][fcst_time]

	return data


def get_organised_obs(obs: list[CleanOBS]):
	data = {}

	for o in obs:
		dt = get_tzsafe_str_date(o.dt)

		data[dt] = get_jsoned_obj(o)
	
	return data





def get_hyperbolic_avg_grade(grades: list[str]):
	grades = filter(lambda x: x != None, grades)
	
	indexes = list(map(
		lambda x: GRADES.index(x),
		grades
	))

	distFromMid = list(map(
		lambda x: abs((N_GRADES // 2) - x),
		indexes
	))

	index = distFromMid.index(max(distFromMid))
	value = indexes[index]
	grade = GRADES[value]

	return grade

def get_avg_grade(grades: list[str]):
	indexes = [GRADES.index(v) for v in grades if v != None]

	total = sum(indexes)
	avgI = round(total / len(indexes))

	return GRADES[avgI]


def get_tzsafe_str_date(date: datetime):
	return date.strftime(EXACT_FMT_NO_TZ) + "Z"