from sqlalchemy import Column, Integer, ForeignKeyConstraint, UniqueConstraint, PrimaryKeyConstraint, ForeignKey, and_, Engine
from sqlalchemy.dialects.mysql import DATETIME, FLOAT, TINYINT, SMALLINT, CHAR, INTEGER, BOOLEAN
from sqlalchemy.orm import Session, declarative_base, relationship, Mapped

from datetime import datetime, timedelta
from typing import Callable, Any

from constants import *
import string_queries as squeries

Base = declarative_base()

class DirtyOBS(Base):
	__tablename__ = 'DIRTYOBS'

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
        PrimaryKeyConstraint("MID", "ORG", "DT"),
    )




class CleanOBS(Base): # MUST HAVE ROW WITH ID -1, FOR FCST WITHOUT OBS.
	__tablename__ = 'CLEANOBS'

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
		UniqueConstraint('MID', 'DT'),
	)

	_real_obs_hr = None
	temp_min = None
	temp_max = None
	precip_rate_sum = None
	weather_types = None


class FCST(Base):
	__tablename__ = 'FCST'

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

	obs = relationship("CleanOBS")

	__table_args__ = (
		UniqueConstraint('MID', 'ORG', 'FCST_TIME', 'FUTURE_TIME'),
	)

class Result(Base):
	__tablename__ = "RESULTS"

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
		UniqueConstraint('FCST_ID', 'PERIOD'),
	)


class Queries():

	def query(query: Callable[[Session], Any], session_constructor: Callable[[], Session]):
		session = session_constructor()

		return query(session)
		

	# api queries

	def get_recent_obs_urgent(mid: int | None = None) -> Callable[[Session], int | None]:
		if (mid and mid != "wholeuk"): return (
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

	def get_results(interval: int, mid: int, orgs: list[str], count_per_org: int) -> Callable[[Session], list]:
		return (
			lambda session:
				session.query(Result) \
					.join(Result) \
					.filter(
						Result.period == interval,
						FCST.mid == mid,
						FCST.org.in_(orgs)
					)# \
					#.order_by(Result.org, Result.)
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
				DirtyOBS.dt < datetime.now() - timedelta(hours = DB_CLEANUP_BUFFER_HOURS),
				DirtyOBS.has_cleaned.is_(None),
				CleanOBS.id.is_(None),
				#DirtyOBS.mid == 3002, # TESTING
			) \
			.order_by(DirtyOBS.dt.desc(), DirtyOBS.mid) \
			.limit(1000) \
			.all()
	

	def get_fcsts_to_eval(session: Session) -> list:
		return session.query(FCST) \
			.filter(
				FCST.fcst_time <= datetime.now() - timedelta(days = 1, hours = COMPARE_HOUR),
				FCST.future_time < datetime.now() - timedelta(hours = COMPARE_HOUR), # NOT inclusive. 24 hours = midnight -> 11pm.
				FCST.obs_id.is_(None),
				#FCST.org == "M3", # TESTING
				#FCST.mid == 3002, # TESTING
				#FCST.fcst_time == datetime(2025, 5, 5) # TESTING
			) \
			.order_by(FCST.fcst_time.asc(), FCST.mid, FCST.future_time.asc()) \
			.all() # dont limit at all, eval is very quick.
	

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
