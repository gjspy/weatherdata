from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import FileResponse
import random
import os

app = FastAPI()
# uvicorn flasksite.testserver:app

@app.get("/api/v1/test-weather")
def get_weather():
	observations = []
	now = datetime.utcnow()
	
	for i in range(5):
		timestamp = now - timedelta(hours=i)
		observation = {
			"timestamp": timestamp.isoformat() + "Z",
			"temperature_c": round(random.uniform(10, 25), 1),
			"humidity_percent": round(random.uniform(40, 90), 1),
			"wind_speed_kph": round(random.uniform(0, 30), 1),
			"condition": random.choice(["Clear", "Cloudy", "Rain", "Snow", "Fog"])
		}
		observations.append(observation)
	
	return {"observations": list(reversed(observations))}  # Oldest first

@app.get("/debug/logs")
def get_logs():
	files = os.listdir()

	return filter(lambda x: "collection.log" in x, files)

@app.get("/debug/log")
def get_log(file: str = "collection.log"):
	print("this is rlly bad dont do this")
	return FileResponse(file)
