from constants import most_common

MO_WEATHER_TYPES = {
	#NA: not available, never seen
	-1: 2, #trace rain, never seen
	0: 2,
	1: 2,#1,
	2: 3,
	3: 3,
	4: None, #not used
	5: 16,
	6: 17,
	7: 4,
	8: 5,
	9: 6, # (shower)
	10: 6, #(shower)
	11: 7,
	12: 6,
	13: 8, # (shower),
	14: 8, # (shower)
	15: 8,
	16: 15, # (shower)
	17: 15, # (shower)
	18: 15,
	19: 14, # (shower)
	20: 14, # (shower)
	21: 14,
	22: 12, # (shower)
	23: 12, # (shower)
	24: 12,
	25: 13,  # (shower)
	26: 13,  # (shower)
	27: 13,
	28: 10,
	29: 10,
	30: 11
}

BBCD_WEATHER_TYPES = {
	"Not available": None,
	"Clear Sky": 2,
	"Sunny Intervals": 2,#1,
	"Sunny": 2,#1,
	"Partly Cloudy": 3,
	"Light Cloud": 3,
	"Thick Cloud": 5,
	"Sleet": 15,
	"Sleet Showers": 15,
	"Drizzle": 7,
	"Light Rain": 6,
	"Light Rain Showers": 6,
	"Heavy Rain": 8,
	"Fog": 17,
	"Mist": 16,
	"Light Snow": 12,
	"Thundery Showers": 10
}

BBC1_WEATHER_TYPES = {
	0: 2, # Clear Sky
	1: 2,#1, # Sunny
	2: 3, # Partly Cloudy
	3: 2,#1, # Sunny Intervals
	4: None, # Sandstorm day
	5: 16, # Mist day
	6: 17, # Fog day
	7: 3, # Light Cloud day
	8: 5, # Thick Cloud day
	9: 6, # Light Rain Showers night
	10: 6, # Light Rain Showers day
	11: 7, # Drizzle day
	12: 6, # Light Rain day,
	13: 8, # Heavy Rain Shower night,
	14: 8, # Heavy Rain Shower day
	15: 8, # Heavy Rain day
	16: 15, # Sleet Shower night
	17: 15, # Sleet Shower day
	18: 15, # Sleet day
	19: 14, # Hail Shower night
	20: 14, # Hail Shower day
	21: 14, # Hail day
	22: 12, # Light Snow Shower night
	23: 12, # Light Snow Shower day
	24: 12, # Light Snow day
	25: 13, # Heavy Snow Shower night,
	26: 13, # Heavy Snow Shower day
	27: 13, # Heavy Snow day
	28: 10, # Thunder Shower night
	29: 10, # Thunder Shower day
	30: 11, # Thunder day
	31: None, # Tropical Storm day
	32: None, # Hazy day
	33: None, # Sandstorm night
	34: 16, # Mist night
	35: 17, # Fog night
	36: 3, # Light Cloud night
	37: 5, # Thick Cloud night
	38: 7, # Drizzle night
	39: 6, # Light Rain night
	40: 8, # Heavy Rain night
	41: 15, # Sleet night
	42: 14, # Hail night
	43: 12, # Light Snow night
	44: 13, # Heavy Snow night
	45: 11, # Thunder night
	46: None, # Tropical Storm night
	47: None, #Hazy night
}

class OWMTypes():
	ThunderShower = [200, 201, 202, 230, 231, 232]
	Thunder = [210, 211, 212]

	LightRain = [500, 520, 300, 310]
	Drizzle = [501, 521, 301, 311, 313, 321]
	HeavyRain = [502, 503, 504, 522, 531, 302, 312, 314]
	Sleet = [511,  611, 612, 613, 614, 615, 616]

	LightSnow = [600, 620]
	HeavySnow = [601, 602, 621, 622]

	Mist = [701, 721]
	IsFog = 741
	
	IsClear = 800

	PartlyCloudy = [801]
	Cloudy = [802, 803]
	Overcast = [804]

	# NO HAIL!


OWM_WEATHER_TYPES = OWMTypes()

WEATHER_TYPE_SCORE_GROUPS = [
	[
		#1,
		2,
		3,
		4,
		5
	],
	[
		6,
		7,
		8,
		10
	],
	[ # can have wt in multiple groups to match with different things.
		11,
		10
	],
	[
		12,
		13,
		14,# doesnt matter which way wrong. if other is guessed then always 25% here.
		15
	]
] # if in group, give score based on different of indexes.
# if out out of group, give 0%
# if wt goes not have a group, give 0% [mist, fog]

WT_TO_INT = {
	"sunny": 2,
	"clear": 2,
	"partly cloudy": 3,
	"cloudy": 4,
	"overcast": 5,
	"light rain": 6,
	"drizzle": 7,
	"heavy rain": 8,
	"thunder shower": 10,
	"thunder": 11,
	"light snow": 12,
	"heavy snow": 13,
	"hail": 14,
	"sleet": 15,
	"mist": 16,
	"fog": 17
}

RAIN_WTS = [
	WT_TO_INT["light rain"],
	WT_TO_INT["light snow"],
	WT_TO_INT["hail"],
	WT_TO_INT["sleet"],

	WT_TO_INT["drizzle"],

	WT_TO_INT["heavy rain"],
	WT_TO_INT["thunder shower"],
	WT_TO_INT["heavy snow"]
]

def get_wt_severity_score(wt: str):
	match wt:
		case 6 | 12 | 14 | 15: return 1
		case 7: return 2
		case 8 | 10 | 13: return 3
		case _: return 0

def convert_wt_to_common(org: str, wt:str|int):
	if (wt == None): return None

	if (not "B" in org): wt = int(wt)

	if (org == "O"):
		if (wt in OWM_WEATHER_TYPES.ThunderShower): return 10
		
		if (wt in OWM_WEATHER_TYPES.Thunder): return 11

		if (wt in OWM_WEATHER_TYPES.LightRain): return 6
		if (wt in OWM_WEATHER_TYPES.Drizzle): return 7
		if (wt in OWM_WEATHER_TYPES.HeavyRain): return 8
		

		if (wt in OWM_WEATHER_TYPES.LightSnow): return 12
		if (wt in OWM_WEATHER_TYPES.HeavySnow): return 13
		if (wt in OWM_WEATHER_TYPES.Sleet): return 15

		if (wt in OWM_WEATHER_TYPES.Mist): return 16
		if (wt == OWM_WEATHER_TYPES.IsFog): return 17

		if (wt == OWM_WEATHER_TYPES.IsClear): return 2

		if (wt in OWM_WEATHER_TYPES.PartlyCloudy): return 3
		if (wt in OWM_WEATHER_TYPES.Cloudy): return 4
		if (wt in OWM_WEATHER_TYPES.Overcast): return 5

		print("WHAT IS THIS WT?", wt, org)
		raise Exception
	
	
	types = None
	if ("M" in org or org == "D"): types = MO_WEATHER_TYPES
	elif (org == "B" or org == "BD"): types = BBCD_WEATHER_TYPES
	elif (org == "B1"): types = BBC1_WEATHER_TYPES

	v = types.get(wt)

	if ((not v) and (wt not in types.keys())): # v can be None (BBC["Not available"])
		print("WHAT IS THIS WT?", wt, org, v)
		raise Exception
	
	return v


def most_common_wt(wts: list[int]):
	if (wts == None): return None

	# list[list[str]], for each wt, all possible lists.
	groups = [[group for group in WEATHER_TYPE_SCORE_GROUPS if wt in group] for wt in wts]
	groups_which_have_all_wts = [group[0] for group in groups if len(group) > 0 and all([wt in group[0] for wt in wts])]

	if (len(groups_which_have_all_wts) > 0): # [2,1 or 1,1,1 all in group]
		group = groups_which_have_all_wts[0]
		indexes = [group.index(wt) for wt in wts] 
		indexes.sort() # get in ascending order of severity
		
		return group[most_common(indexes)]

	return most_common(wts)