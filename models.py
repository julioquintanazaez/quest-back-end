from database import Base
import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Float, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from sqlalchemy.types import TypeDecorator, String
import json

from uuid import UUID, uuid4  

class JSONEncodeDict(TypeDecorator):
	impl = String
	
	def process_bind_param(self, value, dialect):
		if value is not None:
			value = json.dumps(value)
		return value

	def process_result_value(self, value, dialect):
		if value is not None:
			value = json.loads(value)
		return value
		
class User(Base):
	__tablename__ = "user"
	
	username = Column(String(30), primary_key=True, unique=True, index=True) 
	full_name = Column(String(50), nullable=True, index=True) 
	email = Column(String(30), nullable=False, index=True) 
	role = Column(JSONEncodeDict)
	hashed_password = Column(String(100), nullable=True, default=False)	

class Quest_One(Base):  
	__tablename__ = "quest"
	
	id = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)	
	date = Column(DateTime, nullable=True, server_default=func.now())
	#Opinion features
	opinion_generic = Column(String(200), nullable=False, index=True)
	opinion_notchallenge = Column(String(200), nullable=False, index=True)
	opinion_challenge = Column(String(200), nullable=False, index=True)	
	#Parent data
	mother_educ_lavel = Column(String(50), nullable=False, index=True)
	father_educ_lavel = Column(String(50), nullable=False, index=True)
	mother_motivation = Column(String(50), nullable=False, index=True)
	father_motivation = Column(String(50), nullable=False, index=True)
	eco_aid_mother = Column(String(50), nullable=False, index=True)
	eco_aid_father = Column(String(50), nullable=False, index=True)
	#Student data
	student_inspiration = Column(String(50), nullable=False, index=True)
	study_group_numb = Column(Float, nullable=True, default=0)
	study_ref_aid = Column(String(50), nullable=False, index=True)
	best_study_hour = Column(String(50), nullable=False, index=True)
	study_time_day = Column(Float, nullable=True, default=0)
	study_frequency = Column(String(50), nullable=False, index=True)
	perc_atention_generic = Column(Float, nullable=True, default=0)
	perc_atention_notchallenge = Column(Float, nullable=True, default=0)
	perc_atention_challenge = Column(Float, nullable=True, default=0)
	study_screen_time_day = Column(Float, nullable=True, default=0)
	leisure_screen_time_day = Column(Float, nullable=True, default=0)
	study_zone = Column(String(50), nullable=False, index=True)
	#Other data	
	social_group_number = Column(Float, nullable=True, default=0)
	physical_activity_time = Column(Float, nullable=True, default=0)
	transportation = Column(String(50), nullable=False, index=True)
	gender = Column(String(50), nullable=False, index=True)
	family_edutation_criteria = Column(String(50), nullable=False, index=True)
	
