from enum import Enum

import constants


API_FOR_INTERFACE = {
	"home/pane1": "api/results/24?loc_id=all&org=M1&org=B1&fcst_time=daysago_2&future_time=yesterday&count_per_org=1"
}


class Descriptions():
	interval = "Time period in hours of each weather/result instance."
	loc_id = "ID of the location to get weather/result instances of."
	count = "Number of instances to return [PER ORG, PER MID]. (count * interval) / 24 = number of days."
	org = "Weather organisation to get data from. Period type (eg M1 instead of M) required for forecast and result data."
	fcst_time = "Time that forecast was calculated. Either datetime in ISO8601 format, \"yesterday\" or calc string: \"daysago_X\""
	future_time = "Time of weather instance, alias to dt but in terms of forecasts. If count > 1, this is the base time, and each instance is future_time + (index * interval) Either datetime in ISO8601 format, \"yesterday\" or calc string: \"daysago_X\""
	countback_days = "Number of days to include in the response, counting back from day_date given."
	fcst_time_buffer_days = "Number of days between fcst_time and future_time."


class Interval(Enum):
	hourly = 1
	three_hourly = 3
	daily = 24

class LocId(Enum):
	def __init__(self):
		for loc_id in constants.ALL_LOCIDS:
			setattr(self, loc_id, loc_id)
		
		self.all = "all"

class Org(Enum):
	M = "M"
	M1 = "M1"
	M3 = "M3"
	B = "B"
	B1 = "B1"
	BD = "BD"