from sqlalchemy import Column, Integer, ForeignKeyConstraint, UniqueConstraint, PrimaryKeyConstraint, ForeignKey, and_, Engine, func, text, or_
from sqlalchemy.dialects.mysql import DATETIME, FLOAT, TINYINT, SMALLINT, CHAR, INTEGER, BOOLEAN
from sqlalchemy.orm import Session, declarative_base, relationship, Mapped, selectinload

from datetime import datetime, timedelta
from typing import Callable, Any

from constants import *
import string_queries as squeries

Base = declarative_base()

class DirtyOBS(Base):
	__tablename__ = 'DIRTYOBS'
	__name__ = "DirtyOBS"

	mid = Column("MID", Integer, nullable=False)
	org = Column("ORG", CHAR(2), nullable=False)
	dt = Column("DT", DATETIME, nullable=False)
	scr_temp = Column("SCR_TEMP", FLOAT)
	#temp_min = Column(FLOAT)
	#temp_max = Column(FLOAT)
	feels_like = Column("FEELS_LIKE", FLOAT)
	precip_rt = Column("PRECIP_RT", FLOAT)
	precip_tot = Column("PRECIP_T", FLOAT)
	wt = Column("WT", TINYINT)
	wind_s = Column("WIND_S", FLOAT)
	wind_d = Column("WIND_D", FLOAT)
	wind_g = Column("WIND_G", FLOAT)
	hum = Column("HUM", FLOAT)
	prs = Column("PRS", FLOAT)
	vis = Column("VIS", INTEGER(unsigned=True))
	snow_tot = Column("SNOW", SMALLINT)
	has_cleaned = Column("HAS_CLEANED", BOOLEAN) # NULL = not attempted, TRUE = is included, FALSE = cleanobs created before this existed, not included

	__table_args__ = (
        PrimaryKeyConstraint("MID", "ORG", "DT"), # INDEXES ARE INCORECT, CHECK IN MSQL WB
    )


class CleanOBS(Base): # MUST HAVE ROW WITH ID -1, FOR FCST WITHOUT OBS.
	__tablename__ = 'CLEANOBS'
	__name__ = "CleanOBS"

	id = Column("ID", Integer, primary_key=True, autoincrement=True)
	mid = Column("MID", Integer, nullable=False)
	dt = Column("DT", DATETIME, nullable=False)
	scr_temp = Column("SCR_TEMP", FLOAT)
	feels_like = Column("FEELS_LIKE", FLOAT)
	precip_rt = Column("PRECIP_RT", FLOAT)
	wt = Column("WT", TINYINT)
	wind_s = Column("WIND_S", FLOAT)
	wind_d = Column("WIND_D", FLOAT)
	wind_g = Column("WIND_G", FLOAT)
	hum = Column("HUM", FLOAT)
	prs = Column("PRS", FLOAT)
	vis = Column("VIS", INTEGER(unsigned=True))
	snow_tot = Column("SNOW", SMALLINT)

	# if changing, change OBS_CONDITIONS constant.

	__table_args__ = (
		UniqueConstraint('MID', 'DT'), # INDEXES ARE INCORECT, CHECK IN MSQL WB
	)

	_real_obs_hr = None
	temp_min = None
	temp_max = None
	precip_rate_sum = None
	weather_types = None


class FCST(Base):
	__tablename__ = 'FCST'
	__name__ = "FCST"

	id = Column("ID", Integer, primary_key=True, autoincrement=True)
	obs_id = Column("OBS_ID", Integer, ForeignKey('CLEANOBS.ID'), nullable=True) # KEEP THIS, allocate when comparing!!
	mid = Column("MID", Integer, nullable=False)
	org = Column("ORG", CHAR(2), nullable=False)
	fcst_time = Column("FCST_TIME", DATETIME, nullable=False)
	future_time = Column("FUTURE_TIME", DATETIME, nullable=False)
	scr_temp = Column("SCR_TEMP", FLOAT)
	temp_min = Column("TEMP_MIN", FLOAT)
	temp_max = Column("TEMP_MAX", FLOAT)
	feels_like = Column("FEELS_LIKE", FLOAT)
	precip_rt = Column("PRECIP_RT", FLOAT)
	precip_tot = Column("PRECIP_T", FLOAT)
	precip_prob = Column("PRECIP_PROB", SMALLINT)
	wt = Column("WT", TINYINT)
	wind_s = Column("WIND_S", FLOAT)
	wind_d = Column("WIND_D", FLOAT)
	wind_g = Column("WIND_G", FLOAT)
	hum = Column("HUM", FLOAT)
	prs = Column("PRS", FLOAT)
	vis = Column("VIS", INTEGER(unsigned=True))
	#uv = Column(FLOAT)
	snow_tot = Column("SNOW", SMALLINT)
	snow_prob = Column("SNOW_PROB", SMALLINT)
	hsnow_prob = Column("HSNOW_PROB", SMALLINT)
	rain_prob = Column("RAIN_PROB", SMALLINT)
	hrain_prob = Column("HRAIN_PROB", SMALLINT)
	hail_prob = Column("HAIL_PROB", SMALLINT)
	sferics_prob = Column("SFERICS_PROB", SMALLINT)

	# if changing, edit FCST_CONDIITONS constant.

	obs = relationship("CleanOBS")

	__table_args__ = (
		UniqueConstraint('MID', 'ORG', 'FCST_TIME', 'FUTURE_TIME'), # INDEXES ARE INCORECT, CHECK IN MSQL WB
	)


class Result(Base):
	__tablename__ = "RESULTS"
	__name__ = "Result"

	id = Column("ID", Integer, primary_key=True, autoincrement=True)
	fcst_id = Column("FCST_ID", Integer, ForeignKey("FCST.ID"), nullable=False)
	period = Column("PERIOD", TINYINT)
	d_scr_temp = Column("SCR_TEMP_DIFF", FLOAT)
	d_feels_like = Column("FEELS_LIKE_DIFF", FLOAT)
	s_wt = Column("WT_SCORE", FLOAT)
	d_wind_s = Column("WIND_S_DIFF", FLOAT)
	d_wind_d = Column("WIND_D_DIFF", FLOAT)
	d_wind_g = Column("WIND_G_DIFF", FLOAT)
	d_hum = Column("HUM_DIFF", FLOAT)
	d_prs = Column("PRS_DIFF", FLOAT)
	s_p_timing = Column("PTIMING_SCORE", FLOAT)
	s_p_rate = Column("PRATE_SCORE", FLOAT)
	s_p_type = Column("PTYPE_SCORE", FLOAT)
	s_p_conf = Column("PCONF_SCORE", FLOAT)

	# if changing, edit RESULT_CONDITIONS constant

	fcst: Mapped[FCST] = relationship("FCST")

	__table_args__ = (
		UniqueConstraint('FCST_ID', 'PERIOD'), # INDEXES ARE INCORECT, CHECK IN MSQL WB
	)

	def jsonify(self): 
		return {
			"i": self.fcst.mid,
			"o": self.fcst.org,
			"p": self.period,
			"fc": self.fcst.fcst_time,
			"ft": self.fcst.future_time,
			"r": {
				"t": self.d_scr_temp,
				"f": self.d_feels_like,
				"wt": self.s_wt,
				"ws": self.d_wind_s,
				"wd": self.d_wind_d,
				"wg": self.d_wind_g,
				"h": self.d_hum,
				"p": self.d_prs,
				"pti": self.s_p_timing,
				"pr": self.s_p_rate,
				"pty": self.s_p_type,
				"pc": self.s_p_conf
			}
		}





class Queries():

	def query(query: Callable[[Session], Any], session_constructor: Callable[[], Session], close_session: bool = True):
		session = session_constructor()

		resp = query(session)

		if (close_session):
			session.close()
			return resp
		
		return resp, session
		


	# api queries

	def get_recent_obs_urgent(mid: int | None = None) -> Callable[[Session], int | None]:
		if (mid and mid != "all"): return (
			lambda session:
				session.query(DirtyOBS.wt) \
					.filter(DirtyOBS.mid == mid) \
					.order_by(DirtyOBS.dt.desc()) \
					.limit(1)
					.all()
			)

		return (
			lambda session:
				session.execute(squeries.GET_MOST_RECENT_AVG_WT_NATIONWIDE) \
					.fetchall()
			)


	def get_daily_summaries(min_future_time_inc: datetime, max_future_time_exc: datetime, fcst_time_buffer_days: int, loc_id: int | None) -> Callable[[Session], list | None]:
		"""
		gets the daily summary for every location/org for every day between given dates.

		select * from results
		join fcst on fcst.ID=results.FCST_ID
		where results.period = 24
		and fcst.fcst_time = SUBTIME(fcst.future_time, '1 00:00:00')
		and fcst.future_time >= '2025-04-23 00:00:00'
		and fcst.future_time < '2025-04-30 00:00:00'
		and mid=11004
		order by fcst.org, fcst.mid, fcst.FCST_TIME asc, fcst.future_time asc;
		"""

		if (loc_id and loc_id != "all"):
			return (
				lambda session:
					session.query(Result) \
						.options(selectinload(Result.fcst)) # join now, not lazy load, so can access Result.fcst immediately.
						.filter(
							FCST.id == Result.fcst_id, # join ON this
							Result.period == 24,
							FCST.fcst_time == func.DATE_SUB(
								FCST.future_time,
								text(f"INTERVAL {fcst_time_buffer_days} DAY") # timedelta(days = x)
							),
							FCST.future_time >= min_future_time_inc,
							FCST.future_time < max_future_time_exc,
							FCST.mid == loc_id
						)
						.order_by(FCST.org, FCST.fcst_time.asc(), FCST.future_time.asc())
						.all()
				)


		return (
			lambda session:
				session.query(Result) \
					.options(selectinload(Result.fcst)) # join now, not lazy load, so can access Result.fcst immediately.
					.filter(
						FCST.id == Result.fcst_id, # join ON this
						Result.period == 24,
						FCST.fcst_time == func.DATE_SUB(
							FCST.future_time,
							text(f"INTERVAL {fcst_time_buffer_days} DAY") # timedelta(days = x)
						),
						FCST.future_time >= min_future_time_inc,
						FCST.future_time < max_future_time_exc
					)
					.order_by(FCST.org, FCST.mid, FCST.fcst_time.asc(), FCST.future_time.asc())
					.all()
			)
	

	def get_daily_summaries_of_future(future_time: datetime, loc_id: int | None) -> Callable[[Session], list | None]:
		"""
		gets all summaries of accuracy for a future time.

		select * from results
		join fcst on fcst.ID=results.FCST_ID
		where results.period = 24
		and fcst.future_time=future_time
		and mid=11004
		order by fcst.org, fcst.mid, fcst.FCST_TIME asc, fcst.future_time asc;
		"""

		if (loc_id and loc_id != "all"):
			return (
				lambda session:
					session.query(Result) \
						.options(selectinload(Result.fcst)) # join now, not lazy load, so can access Result.fcst immediately.
						.filter(
							FCST.id == Result.fcst_id, # join ON this
							Result.period == 24,
							or_(FCST.future_time == future_time, FCST.future_time == future_time + timedelta(hours=1)), # stupid bbc1fcst, starts 1am
							FCST.mid == loc_id
						)
						.order_by(FCST.org, FCST.fcst_time.asc(), FCST.future_time.asc())
						.all()
				)

		return (
			lambda session:
				session.query(Result) \
					.options(selectinload(Result.fcst)) # join now, not lazy load, so can access Result.fcst immediately.
					.filter(
						FCST.id == Result.fcst_id, # join ON this
						Result.period == 24,
						or_(FCST.future_time == future_time, FCST.future_time == future_time + timedelta(hours=1)), # stupid bbc1fcst, starts 1am
					)
					.order_by(FCST.org, FCST.mid, FCST.fcst_time.asc(), FCST.future_time.asc())
					.all()
			)


	def get_fcsts_of_day(mId: int, day_date: datetime, days: int = 1) -> Callable[[Session], list | None]:
		return (
			lambda session:
				session.query(FCST)
					.filter(
						FCST.mid == mId,
						FCST.future_time >= day_date,
						FCST.future_time < day_date + timedelta(days = days)
					)
					.all()
			)


	# collection queries

	def get_default_obs(session: Session) -> list:
		return session.query(CleanOBS) \
			.filter(
				CleanOBS.id == -1
			).all()


	def get_dirtyobs_older_than_buffer(session: Session) -> list:
		return session.query(DirtyOBS) \
			.outerjoin(
				CleanOBS,
				and_(
					DirtyOBS.dt == CleanOBS.dt,
					DirtyOBS.mid == CleanOBS.mid
				)
			) \
			.filter(
				DirtyOBS.dt < get_datetime_today(), #(datetime.now(**TIMEZONE**) - timedelta(hours = DB_CLEANUP_BUFFER_HOURS)),
				DirtyOBS.has_cleaned.is_(None),
				CleanOBS.id.is_(None),
			) \
			.order_by(DirtyOBS.dt.desc(), DirtyOBS.mid) \
			.all()
			
	

	def get_fcsts_to_eval(session: Session) -> list:
		return session.query(FCST) \
			.filter(
				FCST.fcst_time <= get_datetime_today() - timedelta(days = 1), #datetime.now(**TIMEZONE**) - timedelta(days = 1, hours = COMPARE_HOUR),
				FCST.future_time < get_datetime_today(), #datetime.now(**TIMEZONE**) - timedelta(hours = COMPARE_HOUR), # NOT inclusive. 24 hours = midnight -> 11pm.
				FCST.obs_id.is_(None),
				#FCST.org == "M3", # TESTING
				#FCST.mid == 3002, # TESTING
				#FCST.fcst_time == datetime(2025, 5, 5) # TESTING
			) \
			.order_by(FCST.fcst_time.asc(), FCST.mid, FCST.future_time.asc()) \
			.all() # dont limit at all, eval is very quick. X but still dont limit
	

	def get_obs_between_times(earliest_inc: datetime, latest_exc: datetime, mid: int) -> Callable[[Session], list]:
		return (
			lambda session:
				session.query(CleanOBS).filter(
					CleanOBS.dt >= earliest_inc,
					CleanOBS.dt < latest_exc,
					CleanOBS.mid == mid
				).order_by(CleanOBS.dt.asc()).all()
		)
			

	def get_obs(mid: int, dt: datetime) -> Callable[[Session], list]:
		return (
			lambda session: 
				session.query(CleanOBS).filter(
					CleanOBS.mid == mid,
					CleanOBS.dt == dt
				)
		)
	







def get_objs_between_dates_from_list(earliest_inc: datetime, latest_exc: datetime, objs: list[FCST | CleanOBS]):
	def filter_key(obj):
		dt = (obj.future_time if (type(obj) == FCST) else obj.dt)
		return earliest_inc <= dt < latest_exc

	return list(filter(filter_key, objs))