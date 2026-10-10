from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, \
select

from db_operations import custom_create_engine, \
create_db, create_table, database_url

from models import JobsInsert, Jobs, JobsUpdate

from config \
import db_name

#session -> cursor
#engine -> connection

postgres_engine = custom_create_engine() #this is similar to "conn" in pyscopg2. engine is based off default postgres db
create_db(postgres_engine, db_name) #create db_name from default postgres db (if it doesnt already exist)

new_db_engine = custom_create_engine(db_name=db_name) #create a new engine connected to the new database
create_table(new_db_engine) #create table in new db


#yield session object to be used in the FastAPI endpoints
#since we are using a context manager it automatically handles cleanup
def get_session():
    with Session(new_db_engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI()


#insert a JobInsert objct 
#@app.post("/jobs/") 
def create_job(job: JobsInsert, session: SessionDep):
    try:
        db_job = Jobs.model_validate(job) #this will turn job into a Jobs object (ie. ). The default values for the cols not provided will default to None (see models.py)
        session.add(db_job) #add to database
        session.commit() #save changes
        session.refresh(db_job) #update db_job integrating db changes (ie. autoincrement column, add timestamp)

        print(f"Record Inserted:\nId: {db_job.id} | Role: {db_job.role} | Company: {db_job.company}") #see inserted job (in python)
        
        return db_job
    except Exception as error:
        print(f"Error inserting into Jobs table:", error)
        #raise not raising for now since it doesnt need to be caught elsewhere. The error is already printed to the console and the full output is long


# j = JobsInsert(role = 'data analyst', 
#                company = 'cde123', 
#                status = 'Applied',
#                salary = 150000,
#                description = 'Develop and deploy',
#                closing = '2026-09-30')


# s = SessionDep


#create_job(j, Session(new_db_engine))


#view jobs in table 
#@app.get("/jobs/") 
def view_jobs(session: SessionDep, limit: Annotated[int, Query(le=20)] = 20):
    try:
        jobs = session.exec(select(Jobs).limit(limit)).all()
        print(jobs)
        return jobs        
    except Exception as error:
        print(f"Error viewing Jobs table:", error)


#view_jobs(Session(new_db_engine))



#update jobs in table 
#@app.patch("/jobs/{job_id}") 
def update_job(job_id: int, job: JobsUpdate, session: SessionDep):
    try:
        db_job = session.get(Jobs, job_id) #get job in db to update
        job_data = job.model_dump(exclude_unset=True) #user passes in only the fields they want to update (excluding defaults) -> this returns a dict
        db_job.sqlmodel_update(job_data) #update db value with new value
        session.add(db_job)
        session.commit()
        session.refresh(db_job)

        print("Updated Job:", job_data)

        return db_job    
    except Exception as error:
        print("Error updating Jobs table:", error)

#update_job(1, JobsUpdate(role="Senior Data Analyst"), Session(new_db_engine))


#@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, session: SessionDep):
    try:
        job = session.get(Jobs, job_id)
        session.delete(job)
        session.commit()
        return {"ok": True}
    except Exception as error:
        print("Error deleting from Jobs table:", error)

#delete_job(1, Session(new_db_engine))
