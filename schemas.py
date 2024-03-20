from typing import Union, Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr 

#-------------------------
#-------SYSTEM------------
#------------------------- 

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
	username: Union[str, None] = None
	scopes: List[str] = []
	
class User(BaseModel):	
	username: str
	email: EmailStr
	full_name: Union[str, None] = None
	role: List[str] = []
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True	

class UserInDB(User):
    hashed_password: str
	
#-------------------------
#-------QUESTS------------
#------------------------- 

class Quest_One(BaseModel):
	#Opinion features
	opinion_generic: str = "Estudio todos los dias"
	opinion_notchallenge: str = "Estudio todos los dias"
	opinion_challenge: str = "Estudio todos los dias"
	#Parent data
	mother_educ_lavel: str = "primario"
	father_educ_lavel: str = "universitario"
	mother_motivation: str = "nulo"
	father_motivation: str = "medio"
	eco_aid_mother: str = "alto"
	eco_aid_father: str = "medio"
	#Student data
	student_inspiration: str = "a"
	study_group_numb: float = 1
	study_ref_aid: str = "a"
	best_study_hour: str = "a"
	study_time_day: float = 3
	study_frequency: str = "a"
	perc_atention_generic: float = 50
	perc_atention_notchallenge: float = 80
	perc_atention_challenge: float = 30
	study_screen_time_day: float = 2
	leisure_screen_time_day:  float = 6
	study_zone: str = "a"
	#Other data	
	social_group_number: float = 4
	physical_activity_time: float = 1
	transportation: str = "a"
	gender: str = "M"
	family_edutation_criteria: str = "a"
	
	class Config:
		orm_mode = True
		allow_population_by_field_name = True
		arbitrary_types_allowed = True			

class Quest_One_InDB(Quest_One):
	id: str
	date: date	
	
#-------------------------
#-------INPUTS -----------
#------------------------- 

class Date_INPUT(BaseModel):
    date_input: date