from fastapi import Enum

import constants

class Descriptions():
	interval = "Time period in hours of each weather/result instance."
	loc_id = "ID of the location to get weather/result instances of."
	count = "Number of instances to return [PER ORG]. (count * interval) / 24 = number of days."
	org = "Weather organisation to get data from. Period type (eg M1 instead of M) required for forecast and result data."

class Interval(Enum):
	hourly = 1
	three_hourly = 3
	daily = 24

class LocId(Enum):
	def __init__(self):
		for loc_id in constants.ALL_LOCIDS:
			setattr(self, loc_id, loc_id)
		
		self.wholeuk = "wholeuk"

class Org(Enum):
	M = "M"
	M1 = "M1"
	M3 = "M3"
	B = "B"
	B1 = "B1"
	BD = "BD"

	
	