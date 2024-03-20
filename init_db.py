from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)
		
def create_data_base():

	db = SessionLocal()	
	db.drop_all()
	
	models.User.metadata.create(bind=engine)
	models.Quest_One.metadata.create(bind=engine)
	
	db.create_all()
	db.commit()
	db.close()	

	return "project created succefully"
	
if __name__ == "__main__":
    create_data_base()



