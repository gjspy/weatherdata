
from datetime import datetime, timedelta
from copy import deepcopy
import re

from constants import *
from weather_types import *
from sqlalch_class_defs import Base, DirtyOBS, FCST, Queries, CleanOBS, Result, get_objs_between_dates_from_list



MO1_IGNORE_STD = ["d_scr_temp/M3", "precip/M3", "precip/B1", "s_wt/M3"]
MO3_IGNORE_STD = ["d_scr_temp/M1", "precip/M1", "precip/B1",  "s_wt/M1"]
B1_IGNORE_STD = ["d_scr_temp/M3", "precip/M1", "precip/M3", "s_wt/M3"]
BD_IGNORE_STD = ["d_scr_temp/M1", "precip/M1", "precip/M3", "precip/B1", "s_wt/M1"]

MO1_TEMP_WITHIN_RANGE_BOOST = 0.2 # degC

def eval_temp_mo1(fcst: FCST, obs: CleanOBS):
	ftemp, ftemp_min, ftemp_max, = fcst.scr_temp, fcst.temp_min, fcst.temp_max
	otemp = obs.scr_temp

	diff = ftemp - otemp

	if (diff == 0): return 0

	if (ftemp_max and ftemp_min and ftemp < ftemp_max and ftemp > ftemp_min):
		#accuracy_p = min(100, accuracy_p + 5)
		sign = diff / abs(diff)

		diff = max(0, abs(diff) - MO1_TEMP_WITHIN_RANGE_BOOST) * sign
		# give 5% boost if is within their range. (this works well, bumps up by ~5% total avg, more positive small errors bcs they will be in the range.)

	return diff

def eval_feels(fcst: FCST, obs: CleanOBS):
	ffeels = fcst.feels_like
	ofeels = obs.feels_like

	diff = ffeels - ofeels

	return diff

def eval_precip_mo1(fcst: FCST, obs: CleanOBS):
	# idk what precip_tots are, so not using them.
	# todo: snow, probs

	frate, fprob, orate = fcst.precip_rt, fcst.precip_prob, obs.precip_rt
	
	if (frate == None): frate = 0.0
	if (orate == None): orate = 0.0
	
	diff = abs(frate - orate)

	confidence_score = None

	if (orate <= 0):
		if (frate <= 0): # didnt rain, none forecast, award low
			confidence_score = 100 - (fprob * 0.5)

		else: # didnt rain, fcsted some, award low
			confidence_score = max(0, 100 - (fprob * 1.5))

	else: # did rain, award high confidence
		confidence_score = min(100, fprob * 1.5)

	return {
		"d_p_rate": diff,
		"s_p_conf": confidence_score
	}

def eval_wind_s(fcst: FCST, obs: CleanOBS):
	fwind_s = fcst.wind_s
	owind_s = obs.wind_s

	if (fwind_s == None or owind_s == None): return None

	fwind_s = round(fwind_s * 10) / 10
	owind_s = round(owind_s * 10) / 10

	diff = fwind_s - owind_s

	return diff

def eval_wind_d(fcst: FCST, obs: CleanOBS):
	fwind_d = fcst.wind_d
	owind_d = obs.wind_d

	if (fwind_d == None or owind_d == None): return None

	fwind_d = (fwind_d // 15) * 15
	owind_d = (owind_d // 15) * 15

	diff = abs(fwind_d - owind_d)
	if (diff > 180):
		# can be wrong CW or ACW.
		# could fcst 0deg, obs 270deg. without this line diff = 270 CW.
		# real diff = 90deg ACW.
		diff = 360 - diff
	
	return diff

def eval_wind_g(fcst: FCST, obs: CleanOBS):
	fwind_g = fcst.wind_g
	owind_g = obs.wind_g

	if (fwind_g == None or owind_g == None): return None

	fwind_g = round(fwind_g * 10) / 10
	owind_g = round(owind_g * 10) / 10

	diff = fwind_g - owind_g

	return diff

def eval_hum(fcst: FCST, obs: CleanOBS):
	fhum = fcst.hum
	ohum = obs.hum

	fhum = round(fhum)# * 10) / 10
	ohum = round(ohum)# * 10) / 10

	diff = fhum - ohum
	return diff

def eval_prs(fcst: FCST, obs: CleanOBS):
	fprs = fcst.prs
	oprs = obs.prs

	fprs = round(fprs)
	oprs = round(oprs)

	diff = fprs - oprs
	return diff

def eval_wt_mo1(fcst: FCST, obs: CleanOBS):
	fwt, owt = fcst.wt, obs.wt

	if (fwt == owt): return 100

	fgroups, ogroups = [], []

	for i, group in enumerate(WEATHER_TYPE_SCORE_GROUPS):
		if (fwt in group): fgroups.append(i)
		if (owt in group): ogroups.append(i)

	common_groups = list(set(fgroups).intersection(set(ogroups)))
	
	if (len(common_groups) == 0): return 0

	common_group: list = WEATHER_TYPE_SCORE_GROUPS[common_groups[0]]

	findex = common_group.index(fwt)
	oindex = common_group.index(owt)
	diff = abs(findex - oindex)

	return 100 * (1 - ( diff / len(common_group)))



def eval_temp_maxmin(fcst: FCST, obs: CleanOBS):
	#if (org == "MO3"): worst_case = MO3_TEMP_UNDEROVER_WORST_CASE
	#if (org == "BBCD"): worst_case = BBCD_TEMP_UDNEROVER_WORSTCASE
	fmax, fmin = fcst.temp_max, fcst.temp_min
	omax, omin = obs.temp_max, obs.temp_min

#	score = 0
	total_diff = 0

	if (omax >= fmax):
		diff = omax - fmax
		
		# use *50, not *100, because we give 50% to each side, min and max.
#		score += max(0, 50 * (1 - (diff / worst_case)))
		total_diff += diff

	if (omin <= fmin):
		diff = fmin - omin

#		score += max(0, 50 * (1 - (diff / worst_case)))
		total_diff += diff
	
	return total_diff

def eval_precip_mo3(fcst: FCST, obs: CleanOBS):
	ftot, fprob, fhprob, fwt = fcst.precip_tot, fcst.precip_prob, fcst.hrain_prob, fcst.wt
	orate, owt, owts = obs.precip_rt, obs.wt, obs.weather_types
	
	rain_type_diff = abs(get_wt_severity_score(fwt) - get_wt_severity_score(owt))
	
	if (orate > 0):
		if (ftot > 0): # didnt rain, none forecast, award low
			confidence_score = 100 - (fprob * 0.5)

		else: # didnt rain, fcsted some, award low
			confidence_score = max(0, 100 - (fprob * 1.5))
		
		if (("heavy rain" in owts) or (owts.count("drizzle") >= 2)):
			confidence_score = min(100, (fhprob * 0.2) + confidence_score)
	
	else: # did rain, award high confidence
		confidence_score = min(100, fprob * 1.5)
	
	return {
		"d_p_type": rain_type_diff,
		"s_p_conf": confidence_score
	}

def eval_wt_group(fcst: FCST, obs: CleanOBS):
	fwt = fcst.wt
	owt = obs.wt
	owts: list = obs.weather_types

	if (fwt == owt): return 100

	if (not fwt in owts): return eval_wt_mo1(fcst, obs)

	return 100 * (0.5 + ((owts.count(fwt) / len(owts)) / 2))


def eval_precip_bbc1(fcst: FCST, obs: CleanOBS):
	fprob = fcst.precip_prob
	orate = obs.precip_rt

	if (orate == 0):
		return {
			"s_p_conf": 100 - (fprob * 0.5)
		}
	
	return {
		"s_p_conf": max(100, fprob * 1.25)
	}



def eval_precip_day_of_obs(fcsts: list[FCST], obss: list[CleanOBS], org: str):
	fcsts.sort(key = lambda x: x.future_time)
	obss.sort(key = lambda x: x.dt)

	# PRECIP
	forecasted_rain = [
		o for o in fcsts if (
			(o.precip_rt != 0 and o.precip_rt != None) or
			(o.precip_tot != 0 and o.precip_tot != None) or 
			o.wt in RAIN_WTS or
			o.precip_prob > PRECIP_PROB_THRESH_TO_COUNT_AS_FCSTED
		)
	]

	observed_rain = [
		o for o in obss if (
			(o.precip_rt != 0 and o.precip_rt != None) or
			o.wt in RAIN_WTS
		)
	]

	if (len(forecasted_rain) == 0 and len(observed_rain) == 0): return {
		"s_p_timing": 100,
		"s_p_rate": 100,
		"s_p_type": 100,
		"s_p_conf": 100
	}


	# look at how many hours match
	fhours = set(o.future_time for o in forecasted_rain)
	ohours = set(o.dt for o in observed_rain)

	unmatched = sum([1 for hour in fhours if (not hour in ohours)]) + sum([1 for hour in ohours if (not hour in fhours)])
	
	timing_score = 0
	if (len(ohours) != 0): timing_score = max(0, 100 * (1 - (unmatched / len(ohours))))

	# look at days difference in weather types (severity and duration, generally)
	f_rain_count = sum([get_wt_severity_score(o.wt) for o in fcsts])
	o_rain_count = sum([get_wt_severity_score(o.wt) for o in obss])
	
	rain_type_diff = f_rain_count - o_rain_count	

	type_score = 0
	if (o_rain_count != 0): type_score = max(0, 100 * (1 - (abs(rain_type_diff) / o_rain_count)))


	# score based on confidence, earlier we scored on rate accuracy.
	# do this no matter the timing (new method)
	confidence_scores = []

	confidences = [(
		min( 100, fcsts[i].precip_prob * ( 1.25 if (obss[i] in observed_rain) else 1 ) )
	) for i in range(len(fcsts))]
	
	confidence_score = 0
	if (len(confidences) > 0): confidence_score = sum(confidences) / len(confidences)

	"""for i in range(len(fcsts)):
		f = fcsts[i]
		try: o = obss[i]
		except IndexError: break # not enough obss

		frate = f.precip_rt
		orate = o.precip_rt
		confidence = f.precip_prob

		if (orate == 0):
			if (frate == 0): # didnt rain, not forecasted any, award low confidence
				score = 100 - (confidence * 0.5) # * 0.5 to be nice
			else: # didnt rain, forecasted some (properly, <15% conf usually = no precip_rate.), shame high confidence or high rate
				# award lower confidence # frain will always be <= 1.
				# dont do rate here, no need, did that before, just confidence.

				score = max(0, 100 - (confidence * 1.5)) # *1.5 to be harsher

		else: # did rain, award greater confidence
			score = min(100, confidence * 1.5) # * 0.5 to be nice
		
		confidence_scores.append(score)
	
	confidence_score = sum(confidence_scores) / len(confidence_scores)"""


	if (org == "M3" and len(observed_rain) > 0):
		max_hrain_prob = max([f.hrain_prob for f in fcsts])
		observed_precip = [o.wt for o in observed_rain]

		if (
			(WT_TO_INT["heavy rain"] in observed_precip) or
			(observed_precip.count(WT_TO_INT["drizzle"]) >= 2)
		):
			confidence_score = min(100, confidence_score * (1 + (max_hrain_prob/200)))


	rate_score = None

	if (org == "M1"):
		# look at sum of rates, whether its good just offset
		forecasted_rates = sum([
			(o.precip_rt or 0)
			for o in fcsts
			if (o != None)
		])

		observed_rates = sum([
			(o.precip_rt or 0)
			for o in obss
			if (o != None)
		])

		rate_diff = forecasted_rates - observed_rates
		
		rate_score = 0
		if (observed_rates != 0): rate_score = max(0, 100 * (1 - (abs(rate_diff) / observed_rates)))
	

	# LEAVING HAIL, SNOW, SFERICS FOR NOW.


	return {
		"s_p_timing": timing_score,
		"s_p_rate": rate_score,
		"s_p_type": type_score,
		"s_p_conf": confidence_score
	}




comparers = {
	"d_scr_temp/M1": eval_temp_mo1,
	"d_scr_temp/M3": eval_temp_maxmin,
	"d_feels_like": eval_feels,
	"precip/M1": eval_precip_mo1,
	"precip/M3": eval_precip_mo3,
	"precip/B1": eval_precip_bbc1,
	"d_wind_s": eval_wind_s,
	"d_wind_d": eval_wind_d,
	"d_wind_g": eval_wind_g,
	"d_hum": eval_hum,
	"d_prs": eval_prs,
	"s_wt/M1": eval_wt_mo1,
	"s_wt/M3": eval_wt_group
}




def get_avg_of_obs(period_t: datetime, real_obs_hr: CleanOBS, interval: list[CleanOBS]):
	if (len(interval) == 0): return None

	obs_3hr = CleanOBS(
		id = -1,
		mid = interval[0].mid,
		dt = period_t,

		_real_obs_hr = real_obs_hr
	)

	values_per_condition = {c: [] for c in OBS_CONDITIONS}

	for obs in interval:
		for condition in OBS_CONDITIONS:
			try:
				v = obs.__getattribute__(condition)	
				if (v == None): continue

				values_per_condition[condition].append(v)
			except: continue
	
	for condition in NON_SPECIAL_CONDITIONS:
		values = values_per_condition.get(condition) or None

		if (values): values = sum(values) / len(values)

		obs_3hr.__setattr__(condition, values)
	
	temps = values_per_condition.get("scr_temp")
	if (temps):
		obs_3hr.__setattr__("temp_min", min(temps))
		obs_3hr.__setattr__("temp_max", max(temps))

		#obs_3hr.__setattr__("temps", temps)

	else:
		obs_3hr.__setattr__("temp_min", None)
		obs_3hr.__setattr__("temp_max", None)

		#obs_3hr.__setattr__("temps", [])
	
	


	precip_rate = values_per_condition.get("precip_rt")
	if (precip_rate):
		obs_3hr.__setattr__("precip_rate_sum", sum(precip_rate))

	else:
		obs_3hr.__setattr__("precip_rate_sum", 0)

	wts = values_per_condition.get("wt")
	obs_3hr.__setattr__("wt", most_common_wt(wts))
	obs_3hr.__setattr__("weather_types", wts)

	return obs_3hr




def get_obs_by_dt(obs: list[CleanOBS], org: str):
	obs_per_instance = {o.dt: o for o in obs}

	if (org != "BD" and org != "M3"): return obs_per_instance
	period = 3 if org == "M3" else 24

	obs_per_3 = {}

	base_t = min(obs_per_instance.keys())

	print("obs provided", len(obs), "hours, days = ", len(obs) // 24)

	for day in range(0, int(len(obs) // 24)):
		for i in range(0, 24, period): # [0,3,6,12,15,18,21] or [0]
			interval = []
			real_obs_hr = None

			period_t = base_t + timedelta(days = day, hours = i)

			for ii in range(period): # every hour in perod
				this_t = period_t + timedelta(hours = ii)
				obs_of_time = obs_per_instance.get(this_t)

				if (not obs_of_time): continue
				if (ii == 0): real_obs_hr = obs_of_time

				interval.append(obs_of_time)

			avg = get_avg_of_obs(period_t, real_obs_hr, interval)
			obs_per_3[period_t] = avg
		
	return obs_per_3
		






def eval_instance(instance: FCST, obs: CleanOBS, org: str):
	ignore = []

	match org:
		case "M1": ignore = MO1_IGNORE_STD
		case "M3": ignore = MO3_IGNORE_STD
		case "B1": ignore = B1_IGNORE_STD
		case "BD": ignore = BD_IGNORE_STD

	final_res = Result(
		fcst_id = instance.id,
		period = 3 if (org == "M3") else 24 if (org == "BD") else 1
	)

	#for k in OBS_CONDITIONS:
	#	print(k, obs.__getattribute__(k))
	
	#print("temp_min", obs.__getattribute__("temp_min"))
	#print("temp_max", obs.__getattribute__("temp_max"))
	#print("weather_types", obs.__getattribute__("weather_types"))
	#print("precip_rate_sum", obs.__getattribute__("precip_rate_sum"))
	
	for i, comparer in comparers.items():
		if (i in ignore): continue

		try:
			r = comparer(instance, obs)
		except: continue

		i = re.sub(r"\/.+$", "", i)

		if (i == "precip"):
			for k,v in r.items():
				final_res.__setattr__(k, v)
			
			continue

		final_res.__setattr__(i, r)
	
	return final_res

		



def eval_day_of_forecast_instances(obs: list[CleanOBS], forecasts: list[FCST], org: str):
	instance_period = 3 if (org == "M3") else 24 if (org == "BD") else 1

	obs_per_instance = get_obs_by_dt(obs, org)
	fcast_per_dt = {fcst.future_time: fcst for fcst in forecasts}

	updates = {}
	new_objs = []

	results_per_condition_template = {c: [] for c in RESULT_CONDITIONS}
	results_per_condition_template["periods"] = []

	results_per_condition = {}

	earliest_fcst = None
	earliest_dt = datetime.fromtimestamp(0)

	hour: FCST
	for hour in forecasts:
		dt: datetime = hour.future_time
		this_obs = obs_per_instance.get(dt)

		if ((not earliest_fcst) or (earliest_dt > dt)):
			earliest_fcst = hour
			earliest_dt = dt


		if (not this_obs): # don't add to average!
			# need this, to differentiate between not processed fcsts and fcsts missing an obs.
			updates[hour] = {"obs_id": -1}
			continue
		

		if (instance_period == 1):
			updates[hour] = {"obs_id": this_obs.id}

		elif (this_obs._real_obs_hr):
			updates[hour] = {"obs_id": this_obs._real_obs_hr.id}
		
		else:
			# need this, to differentiate between not processed fcsts and fcsts missing an obs.
			updates[hour] = {"obs_id": -1}
		
		

		hour_accuracy = eval_instance(hour, this_obs, org)
		new_objs.append(hour_accuracy)

		this_day = dt.date()
		if (not results_per_condition.get(this_day)):
			results_per_condition[this_day] = deepcopy(results_per_condition_template)
		

		for condition in RESULT_CONDITIONS:
			value = hour_accuracy.__getattribute__(condition)
			if (value == None): continue

			value = abs(value) # dont want over/under to cancel out.

			results_per_condition[this_day][condition].append(value)
		
		results_per_condition[this_day]["periods"].append(hour.future_time)


	if (len(forecasts) <= 1 or org == "BD"): # dont do daily summary
		return {
			"updates": updates,
			"objs": new_objs
		}
		
	
	for day, results in results_per_condition.items():
		day = datetime(day.year, day.month, day.day) # day -> date ugh

		if (len(results["periods"]) <= 1): continue

		min_dt = min(results["periods"])

		daily_result = Result(
			fcst_id = fcast_per_dt.get(min_dt).id,
			period = 24 # want this, not number of periods. only trying to distinguish types.
		)

		for condition in RESULT_CONDITIONS:
			value = results.get(condition)
			if ((not value) or (len(value) == 0)): continue

			daily_result.__setattr__(condition, (sum(value) / len(value)))


		

		precip_results = {}

		if (org == "M1" or org == "M3"):
			obs_this_day = get_objs_between_dates_from_list(
				day,
				day + timedelta(days = 1),
				obs
			)

			fcsts_this_day = get_objs_between_dates_from_list(
				day,
				day + timedelta(days = 1),
				forecasts
			)
			
			precip_results = eval_precip_day_of_obs(fcsts_this_day, obs_this_day, org)
		

		for k,v in precip_results.items():
			daily_result.__setattr__(k, v)
		

		new_objs.append(daily_result)


	return {
		"updates": updates,
		"objs": new_objs
	}