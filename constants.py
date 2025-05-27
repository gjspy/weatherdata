# HAS EVERY VARIABLE NEEDED AS OF 12/05/25

from datetime import timedelta, timezone
from platform import system
from dotenv import load_dotenv
from typing import Callable
import threading
import os

load_dotenv()

DB_U = os.getenv("DB_U")
DB_P = os.getenv("DB_P")
DB_H = os.getenv("DB_H")

CONNECION_URL = f"mysql+mysqlconnector://{DB_U}:{DB_P}@{DB_H}"
CONNECTION_KWARGS = {
	"pool_recycle": 1800, # avoid stale connections (eg after mySQL timeout)
	"pool_pre_ping": True # check if connection is alive before using
}

MO_GS_K = os.getenv("MO_GS_K")
MO_IM_K = os.getenv("MO_IM_K")
MO_IM_ORD = "gb-temp-rainfall"

DP_K = os.getenv("DP_K")
OWM_K = os.getenv("OWM_K")

GOOG_MAPS_API_K = os.getenv("GOOG_MAPS_API_K") # SET REFERRER RESTRICTION!! (IP OR URL)

DC_ONE_WEBHOOK = os.getenv("DC_ONE_WEBHOOK")

BBC_OBS_ENDPOINT = "https://weather-broker-cdn.api.bbci.co.uk/en/observation/rss/{0}"
BBCD_FCST_ENDPOINT = "https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/{0}"
BBC1_FCST_ENDPOINT = "https://weather-broker-cdn.api.bbci.co.uk/en/forecast/aggregated/{0}"

MO_OBS_ENDPOINT = "https://wow.metoffice.gov.uk/api/observations/geojson?timePointSlider=0&mapTime={0}&showWowData=off&showOfficialData=on&showDcnnData=off&showRegisteredSites=off&showSchoolSitesData=off&groups=" # always round UP time.
MO1_FCST_ENDPOINT = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly?excludeParamaterMetadata=true&includeLocationName=true&latitude={lat}&longitude={long}"
MO3_FCST_ENDPOINT = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/three-hourly?excludeParamaterMetadata=true&includeLocationName=true&latitude={lat}&longitude={long}"
MOALT_OBS_ENDPOINT = "https://wow.metoffice.gov.uk/api/observations/geojson?timePointSlider=0&mapTime={0}&showWowData=on&showOfficialData=off&showDcnnData=off&showRegisteredSites=off&showSchoolSitesData=off&groups="

MO_IMINF_ENDPOINT = f"https://data.hub.api.metoffice.gov.uk/map-images/1.0.0/orders/{MO_IM_ORD}/latest/"
MO_IMDATA_ENDPOINT = "https://data.hub.api.metoffice.gov.uk/map-images/1.0.0/orders/{order}/latest/{file_id_urlsafe}/data?includeLand=false&legend=false"

DP_OBS_ENDPOINT = f"http://datapoint.metoffice.gov.uk/public/data/val/wxobs/all/json/all?res=hourly&key={DP_K}"

OWM_OBS_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&appid={key}&units=metric"



RAW_FILE_LOC = "Raw"
NICE_FILE_LOC = "Formatted"
REPORT_FILE_LOC = "Reports"
IMAGE_FILE_LOC = "Images"

SLASH = "\\" if system() == "Windows" else "/"

RAW_FP_FMT = RAW_FILE_LOC + SLASH + "{org}{meth}_{loc}_{batch}_{now}"
NICE_FP_FMT = NICE_FILE_LOC + SLASH + "{batch}{s}{org}{meth}_{loc}_{data_date}.json"
IMG_FP_FMT = IMAGE_FILE_LOC + SLASH + "{batch}{s}{file_id}.png" # removed Raw. now, no cats (not saving formatted)
REPORT_FP_FMT = REPORT_FILE_LOC + SLASH + "{time}.json"

TIMEZONE = timezone.utc
DATE_FMT = "%d%m%yT%H%M%S"

MO_DEFAULT_DATE_FMT = "%Y-%m-%dT%H:%M%z"
MO_OBS_ENDPOINT_DATE_FMT = "%d/%m/%Y %H:%M" # 21/09/2024 13:59, round UP time. provide in UTC.
MO_OBS_RESP_DATE_FMT = "%Y-%m-%dT%H:%M:%S%z"
DP_OBS_MAIN_DATE_FMT = "%Y-%m-%dT%H:%M:%S%z"
DP_OBS_DAY_DATE_FMT = "%Y-%m-%d%z"
BBC_DEFAULT_DATE_FMT = "%Y-%m-%dT%H:%M:%S%z"
BBC_EXACT_DATE_FMT = "%Y-%m-%dT%H:%M:%S.%f%z"
BBC1FCST_DATE_FMT = "%Y-%m-%d%H:%M"

DAY_DATE_FMT = "%Y%m%d"


MILE_TO_KM = 1.609344 # * by
KNOT_TO_KM = 1.852 # * by
METRE_SEC_TO_KM_HR = 3.6 # * by


MAP_IMG_BKG_800px = "bkg_800x800.png"
IM_WHITE_THRESH = 250
IM_OVERLAY_OPAC = 150 # 0 = invisible (/255)


EVENT_LOOP_EVERY = 10 # minutes
RUN_SLOW_MAX_COOLDOWN = 3

DB_COMMIT_FREQ_SLOW = 1 # seconds
DB_COMMIT_FREQ_FAST = 0.1

MAX_WAIT_FOR_DB_RESP = 9*60

DB_CLEANUP_BUFFER_HOURS = 2 # MUST BE LESS THAN COMPARE_HOUR, NEED CLEAN THINGS!

BBCDFCST_HOUR = 6
COMPARE_HOUR = 3 # MUST BE MORE THAN DB_CLEANUP_BUFFER, NEED CLEAN THINGS!


OBS_CONDITIONS = [
	"scr_temp", "feels_like", "precip_rt",
	"wt", "wind_s", "wind_d",
	"wind_g", "hum", "prs",
	"vis", "snow_tot"
]

NON_SPECIAL_CONDITIONS = ["scr_temp", "feels_like", "wind_s", "wind_d", "wind_g", "hum", "prs"]

RESULT_CONDITIONS = [
	"d_scr_temp", "d_feels_like", "s_wt",
	"d_wind_s", "d_wind_d", "d_wind_g",
	"d_hum", "d_prs", "s_p_timing",
	"s_p_rate", "s_p_type", "s_p_conf"
]

PRECIP_PROB_THRESH_TO_COUNT_AS_FCSTED = 20

SITE_INFO = [ # CONVENTION: USE mId for all storage.
	{
		"name":"Hawarden (A'pt)",
		"clean_name":"Hawarden",
		"lat":53.174,
		"long":-2.986,
		"mId":"11004",
		"bId":"6296609", # observer
		"dId":"3321",
        "alt_mId":"890196001"
	},
	{
		"name":"Scilly St Marys",
		"clean_name":"ScillyStMarys",
		"special":"Southernmost",
		"lat":49.913,
		"long":-6.301,
		"mId":"3031",
		"bId":"6943072", # observer
		#"bId": "6296590" airport to match met office
		"dId":"3803",
        "alt_mId":None
	},
	{
		"name":"Bournemouth a'pt",
		"clean_name":"Bournemouth",
		"lat":50.779,
		"long":-1.835,
		"mId":"10007",
		"bId":"6296591", # observer
		"dId":"3862",
        "alt_mId":"867b371d-8bf9-ed11-913a-0003ff7a6da1"
	},
	{
		"name":"Heathrow",
		"clean_name":"Heathrow",
		"lat":51.479,
		"long":-0.4491,
		"mId":"12004",
		"bId":"2647216", # cant find observer
		"dId":"3772",
        "alt_mId":"90be51c3-081c-ee11-913a-201642ba4217"
	},
	{
		"name":"Manston (near Dover)",
		"clean_name":"Manston",
		"lat":51.3422,
		"long":1.3461,
		"mId":"5034",
		#"bId":"2643095"
		"bId":"2633371", # observer, yeovilton nearby
		"dId":"3797",
        "alt_mId": "40959233"
	},
	{
		"name":"Wattisham (A'fd) (near Ipswitch)",
		"clean_name":"Wattisham",
		"lat":52.123,
		"long":0.961,
		"mId":"4023",
		#"bId":"6296656" # airport to match met office
		"bId":"2634663", # observer
		"dId":"3590",
        "alt_mId":"9ea887bf-0249-ea11-b699-0003ff59987e"
	},
	{
		"name":"Coleshill (Birmingham)",
		"clean_name":"Coleshill",
		"lat":52.48,
		"long":-1.689,
		"mId":"3015",
		"bId":"2652582",
		"dId":"3535",
        "alt_mId":"2a09ac88-33a3-e911-b083-0003ff59a71f"
	},
	{
		"name":"Watnall (nottingham)",
		"clean_name":"Watnall",
		"lat":53.005,
		"long":-1.25,
		"mId":"3029",
		"bId":"11902831",
		"dId":"3354",
        "alt_mId":"91443920-6f0c-ef11-a81c-002248a1f654"
	},
	{
		"name":"Waddington (A'pt) (lincoln)",
		"clean_name":"Waddington",
		"lat":53.175,
		"long":-0.521,
		"mId":"6038",
		#"bId":"6296675" airport to match met office
		"bId": "2634923",
		"dId":"3377",
        "alt_mId":"942fa7bd-dc8a-ea11-99e5-0003ff59b198"
	},
	{
		"name":"Shawbury (shrewsbury)",
		"clean_name":"Shawbury",
		"lat":52.794,
		"long":-2.663,
		"mId":"5026",
		"bId":"2638111",
		"dId":"3414",
        "alt_mId":None
	},
	{
		"name":"Brize Norton (near Oxford)",
		"clean_name":"BrizeNorton",
		"lat":51.758,
		"long":-1.576,
		"mId":"7002",
		"bId":"2654659",
		"dId":"3649",
        "alt_mId":"32232337-b82d-eb11-8441-0003ff597f33"
	},
	{
		"name":"Bedford (near Milton Keynes)",
		"clean_name":"Bedford",
		"lat":52.225,
		"long":-0.464,
		"mId":"5006",
		"bId":"2656046",
		"dId":"3560",
        "alt_mId":"dfca94cc-dd4d-e611-9401-0003ff5987fd"
	},
	{
		"name":"St-Athan (A'pt) (cardiff)",
		"clean_name":"StAthan",
		"lat":51.405,
		"long":-3.44,
		"mId":"3034",
		#"bId":"6296584" airport to match met office
		"bId": "2638854",
		"dId":"3716",
        "alt_mId":"34948343"
	},
	{
		"name":"Sennybridge (brecon beacons)",
		"clean_name":"Sennybridge",
		"lat":51.063,
		"long":-3.614,
		"mId":"2042",
		"bId":"2638202",
		"dId":"3507",
        "alt_mId":None
	},
	{
		"name":"Trawsgoed (Aberystwyth)", # !! bbc = aberystwyth only
		"clean_name":"Aberystwyth",
		"lat":52.344,
		"long":-3.947,
		"mId":"6049",
		"bId":"2657782", # NOT AN OBSERVER!! CANT GET OBSERVER ID
		"dId":"3503",
        "alt_mId":"3428d818-73c5-e711-9402-0003ff59823c"
	},
	#{
	#	"name":"Lake Vyrnwy", # no bbc
	#	"lat":52.757,
	#	"long":-3.464,
	#	"mId":"3017"
	#},
	{
		"name":"Valley (Holyhead)",
		"clean_name":"Valley",
		"lat":53.252,
		"long":-4.537,
		"mId":"1033",
		"bId":"2635022", # observer
		"dId":"3302",
        "alt_mId":"91b73390-eeeb-ec11-b5cf-0003ff595eb4"
	},
	{
		"name":"Capel Curig",
		"clean_name":"CapelCurig",
		"lat":53.093,
		"long":-3.941,
		"mId":"7003",
		"bId":"2653850",
		"dId":"3305",
        "alt_mId":None
	},
	{
		"name":"Rhyl",
		"clean_name":"Rhyl",
		"lat":53.259,
		"long":-3.509,
		"mId":"1029",
		"bId":"2639409",
		"dId":"3313",
        "alt_mId":"1fd50d90-460b-ed11-b5cf-0003ff597f35"
	},
	{
		"name":"Crosby",
		"clean_name":"Crosby",
		"lat":53.497,
		"long":-3.056,
		"mId":"8002",
		"bId":"3209584",
		"dId":"3316",
        "alt_mId":None
	},
	{
		"name":"Rostherne (near M'cr A'pt)",
		"clean_name":"Rostherne",
		"lat":53.3598,
		"long":-2.3805,
		"mId":"54059070",
		"bId":"2639108", # not observer
		"dId":"3351",
        "alt_mId":"04756743-b966-ee11-a81c-000d3adf3c9e"
	},
	{
		"name":"Ronaldsway (Isle of Man)",
		"clean_name":"Ronaldsway",
		"lat":54.0849,
		"long":-4.6321,
		"mId":"22580942",
		"bId":"3042189",
		"dId":"3204",
        "alt_mId":"25478447"
	},
	{
		"name":"Walney Island (A'pt) (Barrow-In-Furness, near WIndermere)",
		"clean_name":"WalneyIsland",
		"lat":54.125,
		"long":-3.257,
		"mId":"1035",
		"bId":"6296607", # airport to match met office, cant get observer
		"dId":"3214",
        "alt_mId":"175f0d3a-103d-ef11-a81c-6045bddef696"
	},
	{
		"name":"Albemarle (Newcastle)", # bccs is newcastle only
		"clean_name":"Newcastle",
		"lat":55.02,
		"long":-1.88,
		"mId":"3002",
		"bId":"2641673",
		"dId":"3238",
        "alt_mId":"724926051"
	},
	{
		"name":"Edinburgh",
		"clean_name":"Edinburgh",
		"lat":55.928,
		"long":-3.343,
		"mId":"12009",
		"bId":"2650225",
		"dId":"3166",
        "alt_mId":"b0732fa5-83c7-ef11-a81b-000d3ab96a94"
	},
	{
		"name":"Belfast A'pt",
		"clean_name":"Belfast",
		"lat":54.664,
		"long":-6.224,
		"mId":"5002",
		"bId":"6296569", # best shot at observer, cant get named obsrever, goes to bad if searched
		"dId":"3917",
        "alt_mId":None
	},
	{
		"name":"Aberdeen A'pt",
		"clean_name":"Aberdeen",
		"lat":57.206,
		"long":-2.202,
		"mId":"1",
		"bId":"2657832", # cant get observer
		"dId":"3091",
        "alt_mId":"16b1f54d-35ae-e911-b083-0003ff598cc1"
	},
	{
		"name":"Tulloch Bridge",
		"clean_name":"TullochBridge",
		"lat":56.867,
		"long":-4.708,
		"mId":"30",
		"bId":"2649169", # cant get observer
		"dId":"3047",
        "alt_mId":None
	},
	{
		"name":"Baltasound (Shetland Islands)",
		"special":"Northernmost",
		"clean_name":"Baltasound",
		"lat":60.749,
		"long":-0.854,
		"mId":"3006",
		"bId":"2656431", # observer
		"dId":"3002",
        "alt_mId":"ba53481d-69ae-ee11-a81c-000d3ab7537e"
	}
]

SITES_BY_ID = {o["mId"]: o for o in SITE_INFO}
SITES_BY_DID = {o["dId"]: o for o in SITE_INFO}
ALL_LOCIDS = [v["mId"] for v in SITE_INFO]

TRACKING_STR_LEN = max([len(v["mId"]) for v in SITE_INFO]) + 6 + 1

COMPASS = [
	'north', 'northnortheast', 'northeast', 'eastnortheast',
	'east', 'eastsoutheast', 'southeast', 'southsoutheast',
	'south', 'southsouthwest', 'southwest', 'westsouthwest',
	'west', 'westnorthwest', 'northwest', 'northnorthwest'
]

BBCD_DB_CONDITION_NAMES = {
	"Temperature": "scr_temp",
	"Wind Direction": "wind_d",
	"Wind Speed": "wind_s", # mph -> km/h
	"Humidity": "hum",
	"Pressure": "prs", # mb
	"Visibility": "vis",

	# specifically forecast
	"Minimum Temperature": "temp_min",
	"Maximum Temperature": "temp_max",
	#"UV Risk": "uv",
	#"Pollution": "pollution",
	#"Sunrise": "sunrise",
	#"Sunset": "sunset"
}

MOO_DB_CONDITION_NAMES = {
	"dt": "scr_temp",
	"drr": "precip_rt", # mm/h
	"dra": "precip_tot", # mm
	#"dwc": "weather_type_2", # deprecated?
	"dwt": "wt",
	"dws": "wind_s", # kn/h -> km/h
	"dwd": "wind_d",
	"dh": "hum",
	"dm": "prs", # hPa (=== mb)
	#"dap": "prs_2", # hPa (=== mb)
	"ds": "snow_tot"
}

MOF1_DB_CONDITION_NAMES = {
	"time": "future_time",
	"screenTemperature": "scr_temp",
	"minScreenAirTemp": "temp_min", # NEW
	"maxScreenAirTemp": "temp_max", # NEW
	"feelsLikeTemperature": "feels_like",
	"windSpeed10m": "wind_s", # m/s
	"windDirectionFrom10m": "wind_d",
	"windGustSpeed10m": "wind_g", # m/s
	"visibility": "vis", # m
	"screenRelativeHumidity": "hum",
	"mslp": "prs", # pa -> hpa (===mb)
	"uvIndex": "uv",
	"significantWeatherCode": "wt",
	"precipitationRate": "precip_rt", # mm/h
	"totalPrecipAmount": "precip_tot", # mm
	"totalSnowAmount": "snow_tot", # mm over one hr
	"probOfPrecipitation": "precip_prob" # %
}

MOF3_DB_CONDITION_NAMES = {
	"time": "future_time",
	#screenTemperature not present
	"minScreenAirTemp": "temp_min",
	"maxScreenAirTemp": "temp_max",
	"feelsLikeTemp": "feels_like",
	"windSpeed10m": "wind_s",
	"windDirectionFrom10m": "wind_d", # degrees
	"windGustSpeed10m": "wind_g",
	"visibility": "vis", # m
	"screenRelativeHumidity": "hum",
	"mslp": "prs",
	"uvIndex": "uv",
	"significantWeatherCode": "wt",
	# precipitationRate not present
	"totalPrecipAmount": "precip_tot",
	"totalSnowAmount": "snow_tot", # mm over 3 hours
	"probOfPrecipitation": "precip_prob", # %

	"probOfSnow": "snow_prob", # %
	"probOfHeavySnow": "hsnow_prob", # %
	"probOfRain": "rain_prob", # %
	"probOfHeavyRain": "hrain_prob", # %
	"probOfHail": "hail_prob", # %
	"probOfSferics": "sferics_prob" # %
}

DP_DB_CONDITION_NAMES = {
	"G":"wind_g",
	"T":"scr_temp",
	"V":"vis",
	"D":"wind_d",
	"S":"wind_s",
	"W":"wt",
	"P":"prs",
	"H":"hum"
}

OWM_DB_CONDITION_NAMES = {
	"main_temp":"scr_temp",
	"main_feels_like":"feels_like",
	#"main_temp_min":"temp_min",
	#"main_temp_max":"temp_max",
	"main_pressure":"prs",
	"main_humidity":"hum",
	
	"visibility":"vis", # m -> km
	
	"wind_speed":"wind_s", # ms-1 -> kmh-1
	"wind_deg":"wind_d",
	"wind_gust":"wind_g",
	
	"rain_1h":"precip_rt", # mm/h
	"snow_1h":"snow_tot",

	"weather_id":"wt"
}


BBC1_DB_CONDITION_NAMES = {
	#"localDate": "date",
	#"timeslot": "time_",
    #"ISSUE_DATE": "issuetime_",

	"temperatureC": "scr_temp",
	"feelsLikeTemperatureC": "feels_like",
	"windSpeedKph": "wind_s",
	"windDirectionFull": "wind_d",
	"gustSpeedKph": "wind_g",
	"visibility": "vis",
	"humidity": "hum",
	"pressure": "prs",
	"weatherType": "wt",
	"precipitationProbabilityInPercent": "precip_prob"
}




class TerminalColours:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    

class ThreadThatReturns(threading.Thread):
	def __init__(self, target: Callable, name: str = "", args: list = [],
				 kwargs: dict = {}, daemon: bool = False):
		
		super().__init__(None, target, name, args, kwargs, daemon = daemon)

		self._args = args
		self._kwargs = kwargs
		self._target = target
		self._return = None

	def run(self):
		self._return = self._target(*self._args, **self._kwargs)
	
	def join(self, timeout: float | None = None):
		threading.Thread.join(self, timeout)

		return self._return




WEATHER_CONDITION_PRIORITIES = {
	"scr_temp": ["M", "D", "O", "B"],
	#"temp_min":[],
	#"temp_max":[], # dont do min/max, owm(only) response not useful.
	"feels_like": ["O"],
	"precip_rt": ["O"],
	#"precip_tot": [],
	"wt": ["O","M","D","B"],
	"wind_s":["O","B","MO","D"],
	"wind_d": ["M", "D", "O", "B"],
	"wind_g": ["O", "D"],
	"hum": ["M", "D", "B", "O"],
	"prs": ["M", "D", "B", "O"],
	"vis": ["M", "D", "O", "B"],
	#"uv": [],
	"snow_tot": ["O"]
}





def bbc_convert_vis_str_to_int(vis: str):
	match vis:
		case "Very Poor": return 1
		case "Poor": return 3
		case "Moderate": return 7
		case "Good": return 15
		case "Very Good": return 30
		case "Excellent": return 45

	print("WHAT IS THIS BBC VIS?", vis)
	return None


def strorg_to_dborg(str_org: str):
	match str_org:
		case "MO":   return "M"
		case "BBC":  return "B"
		case "OWM":  return "O"
		case "DP":   return "D"

		case "MO1":  return "M1"
		case "MO3":  return "M3"
		case "BBC1": return "B1"
		case "BBCD": return "BD"


def most_common(ls: list[int]):
	"""Finds most common item in list.
	ls should be a list of int or str.
	when dealing with numerous values of the same count [1,1,1]:
		list[int]: sorted ascending by ls value, returns smallest.
		list[str]: gives median value in order of ls.
	"""
	i_counts = [(v, ls.count(v)) for v in ls]

			
	most = [(-1, -1)]

	for count in i_counts:
		if (count[1] == most[0][1]):
			most.append(count)
			continue

		if (count[1] > most[0][1]):
			most = [count]
	
	if (len(most) > 1): # [1,1,1], take median severe.
		#if (type(ls[0]) == int): most.sort(key=lambda x: x[0])
		if (type(ls[0]) == str): most.sort(key=lambda x: ls.index(x[0]))
	
	return most[len(most) // 2][0] # median!!