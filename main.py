from fastapi import Depends, FastAPI, HTTPException, status, Response, Security, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from fastapi.responses import StreamingResponse
from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import case
from sqlalchemy import desc, asc
from uuid import uuid4
from pathlib import Path
from typing import Union
from datetime import datetime, timedelta
#---Imported for JWT example-----------
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated
import models
import schemas
from database import SessionLocal, engine 
import init_db
import config
import asyncio
import concurrent.futures
import csv
from io import BytesIO, StringIO

#-------FAKE DB------------------------
#User: _admin_quest:adminQuest+-!? 
#-------------------------------------
models.Base.metadata.create_all(bind=engine)

#Create resources for JWT flow
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
	tokenUrl="token",
	scopes={"admin": "Add, edit and delete information.", "manager": "Create and read information.", "user": "Read information."}
)
#----------------------
#Create our main app
app = FastAPI()

#----SETUP MIDDLEWARES--------------------

# Allow these origins to access the API
origins = [	
	"http://my-app-4bad.onrender.com",
	"https://my-app-4bad.onrender.com",		
	"http://localhost",
	"http://localhost:8080",
	"https://localhost:8080",
	"http://localhost:5000",
	"https://localhost:5000",
	"http://localhost:3000",
	"https://localhost:3000",
	"http://localhost:8000",
	"https://localhost:8000",
]

# Allow these methods to be used
methods = ["GET", "POST", "PUT", "DELETE"]

# Only these headers are allowed
headers = ["Content-Type", "Authorization"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=methods,
	allow_headers=headers,
	expose_headers=["*"]
)

ALGORITHM = config.ALGORITHM	
SECRET_KEY = config.SECRET_KEY
APP_NAME = config.APP_NAME
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES
ADMIN_USER = config.ADMIN_USER
ADMIN_NAME = config.ADMIN_NAME
ADMIN_EMAIL = config.ADMIN_EMAIL
ADMIN_PASS = config.ADMIN_PASS

# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


#------CODE FOR THE JWT EXAMPLE----------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
	db_user = db.query(models.User).filter(models.User.username == username).first()	
	if db_user is not None:
		return db_user 

#This function is used by "login_for_access_token"
def authenticate_user(username: str, password: str,  db: Session = Depends(get_db)):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password): #secret
        return False
    return user
	
#This function is used by "login_for_access_token"
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30) #Si no se pasa un valor por usuario
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
	
#This function is used by "get currecnt active user" dependency security authentication
async def get_current_user(
			security_scopes: SecurityScopes, 
			token: Annotated[str, Depends(oauth2_scheme)],
			db: Session = Depends(get_db)):
	if security_scopes.scopes:
		authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
	else:
		authenticate_value = "Bearer"
		
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username: str = payload.get("sub")
		if username is None:
			raise credentials_exception			
		token_scopes = payload.get("scopes", [])
		token_data = schemas.TokenData(scopes=token_scopes, username=username)
		
	except (JWTError, ValidationError):
		raise credentials_exception
			
		token_data = schemas.TokenData(username=username)
	except JWTError:
		raise credentials_exception
		
	user = get_user(db, username=token_data.username)
	if user is None:
		raise credentials_exception
		
	for user_scope in security_scopes.scopes:
		if user_scope not in token_data.scopes:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Not enough permissions",
				headers={"WWW-Authenticate": authenticate_value},
			)
			
	return user
	
async def get_current_active_user(current_user: Annotated[schemas.User, Security(get_current_user, scopes=["admin"])]):  #, "manager", "user"
	return current_user

#------------------------------------
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
	user = authenticate_user(form_data.username, form_data.password, db)
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password",
			headers={"WWW-Authenticate": "Bearer"},
		)
	access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
	print(form_data.scopes)
	print(user.role)
	access_token = create_access_token(
		data={"sub": user.username, "scopes": user.role},   
		expires_delta=access_token_expires
	)
	return {"detail": "Ok", "access_token": access_token, "token_type": "Bearer"}
	
@app.get("/")
def index():
	return {"Application": "Say hello to my little friend oLo"}
	
@app.get("/get_user_status", response_model=schemas.User)
async def get_user_status(current_user: Annotated[schemas.User, Depends(get_current_user)]):
    return current_user
	
#########################
###   USERS ADMIN  ######
#########################
@app.post("/create_owner", status_code=status.HTTP_201_CREATED)  
async def create_owner(db: Session = Depends(get_db)): #Por el momento no tiene restricciones
	if db.query(models.User).filter(models.User.username == config.ADMIN_USER).first():
		db_user = db.query(models.User).filter(models.User.username == config.ADMIN_USER).first()
		if db_user is None:
			raise HTTPException(status_code=404, detail="User not found")	
		db.delete(db_user)	
		db.commit()
		
	db_user = models.User(
		username=config.ADMIN_USER, 
		full_name=config.ADMIN_NAME,
		email=config.ADMIN_EMAIL,
		role=["admin","manager","user"],
		hashed_password=pwd_context.hash(config.ADMIN_PASS)		
	)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)	
	return {f"User:": "Succesfully created"}
	
@app.post("/create_user/", status_code=status.HTTP_201_CREATED)  
async def create_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				user: schemas.UserInDB, db: Session = Depends(get_db)): 
	if db.query(models.User).filter(models.User.username == user.username).first() :
		raise HTTPException( 
			status_code=400,
			detail="The user with this email already exists in the system",
		)	
	db_user = models.User(
		username=user.username, 
		full_name=user.full_name,
		email=user.email,
		role=user.role,
		hashed_password=pwd_context.hash(user.hashed_password)
	)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)	
	return {f"User: {db_user.username}": "Succesfully created"}
	
@app.get("/read_users/", status_code=status.HTTP_201_CREATED) 
async def read_users(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
		skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    	
	db_users = db.query(models.User).offset(skip).limit(limit).all()    
	return db_users

@app.delete("/delete_user/{username}", status_code=status.HTTP_201_CREATED) 
async def delete_user(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				username: str, db: Session = Depends(get_db)):
	db_user = db.query(models.User).filter(models.User.username == username).first()
	if db_user is None:
		raise HTTPException(status_code=404, detail="User not found")	
	if username != "_admin_quest" and username != current_user.username:
		db.delete(db_user)	
		db.commit()
	return {"Deleted": "Delete User Successfuly"}
	
#######################
#### QUESTIONARY ######
#######################

@app.post("/add_questionary/", status_code=status.HTTP_201_CREATED)
async def create_project(quest: schemas.Quest_One, db: Session = Depends(get_db)):	
	try:
		db_quest = models.Quest_One(
			date=func.now(),			
			#Opinion features
			opinion_generic = quest.opinion_generic,
			opinion_notchallenge = quest.opinion_notchallenge,
			opinion_challenge = quest.opinion_challenge,
			#Parent data
			mother_educ_lavel = quest.mother_educ_lavel,
			father_educ_lavel = quest.father_educ_lavel,
			mother_motivation = quest.mother_motivation,
			father_motivation = quest.father_motivation,
			eco_aid_mother = quest.eco_aid_mother,
			eco_aid_father = quest.eco_aid_father,
			#Student data
			student_inspiration = quest.student_inspiration,
			study_group_numb = quest.study_group_numb,
			study_ref_aid = quest.study_ref_aid,
			best_study_hour = quest.best_study_hour,
			study_time_day = quest.study_time_day,
			study_frequency = quest.study_frequency,
			perc_atention_generic = quest.perc_atention_generic,
			perc_atention_notchallenge = quest.perc_atention_notchallenge,
			perc_atention_challenge = quest.perc_atention_challenge,
			study_screen_time_day = quest.study_screen_time_day,
			leisure_screen_time_day =  quest.leisure_screen_time_day,
			study_zone = quest.study_zone,
			#Other data	
			social_group_number = quest.social_group_number,
			physical_activity_time = quest.physical_activity_time,
			transportation = quest.transportation,
			gender = quest.gender,
			family_edutation_criteria = quest.family_edutation_criteria,
		)
		db.add(db_quest)
		db.commit()
		db.refresh(db_quest)	
		return db_quest
	except SQLAlchemyError as e: 
		raise HTTPException(status_code=405, detail="Unexpected error when creating project")

@app.get("/read_questionaries/", status_code=status.HTTP_201_CREATED)
async def read_questionaries(current_user: Annotated[schemas.User, Security(get_current_active_user, scopes=["admin"])],
				skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	questionaries = db.query(models.Quest_One).offset(skip).limit(limit).all()    
	return questionaries
	
@app.get("/read_questionaries/{date_input}", status_code=status.HTTP_201_CREATED)
async def read_questionaries_by_date(current_user: Annotated[schemas.User, Security(get_current_active_user, scopes=["admin"])],
				date_input: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):    
	
	filter_questionaries = db.query(
		models.Quest_One
	).group_by(
		models.Quest_One.date
	).filter(
		models.Quest_One.date >= date_input
	).all()	
	
	return filter_questionaries
	
def create_csv(query, columns_names):

	csvtemp = ""	
	
	header = [i for i in columns_names]
	csvtemp = ",".join(header) + "\n"
	
	for row in query:		
		csvtemp += (str(row)).replace("(", "").replace(")", "").replace("'", "") + "\n"		
		
	return StringIO(csvtemp)
	
@app.get("/student_questionary_to_csv")
async def student_questionary_to_csv(current_user: Annotated[schemas.User, Depends(get_current_active_user)],
				db: Session = Depends(get_db)):
	
	query_questionaries = db.query(
		models.Quest_One.id,
		models.Quest_One.date,
		models.Quest_One.opinion_generic,
		models.Quest_One.opinion_notchallenge,
		models.Quest_One.opinion_challenge,
		models.Quest_One.mother_educ_lavel,
		models.Quest_One.father_educ_lavel,
		models.Quest_One.mother_motivation,
		models.Quest_One.father_motivation,
		models.Quest_One.eco_aid_mother,
		models.Quest_One.eco_aid_father,
		models.Quest_One.student_inspiration,
		models.Quest_One.study_group_numb,
		models.Quest_One.study_ref_aid,
		models.Quest_One.best_study_hour,
		models.Quest_One.study_time_day,
		models.Quest_One.study_frequency,
		models.Quest_One.perc_atention_generic,
		models.Quest_One.perc_atention_notchallenge,
		models.Quest_One.perc_atention_challenge,
		models.Quest_One.study_screen_time_day,
		models.Quest_One.leisure_screen_time_day,
		models.Quest_One.study_zone,
		models.Quest_One.social_group_number,
		models.Quest_One.physical_activity_time,
		models.Quest_One.transportation,
		models.Quest_One.gender,
		models.Quest_One.family_edutation_criteria
	).all()	
	
	myfile = create_csv(query_questionaries, models.Quest_One.__table__.columns.keys())
	
	headers = {'Content-Disposition': 'attachment; filename="data.csv"'} 
	return StreamingResponse(iter([myfile.getvalue()]), media_type="application/csv", headers=headers)
	
	
