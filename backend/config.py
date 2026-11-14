import os
from dotenv import load_dotenv


#user params
option = 'view' #["create_db_table", "view", "insert", "update", "delete"]


#name params
db_name = 'job_tracker_sql_alchemy'
table_name = 'jobs'


# Define connection credentials to postgres

load_dotenv()

db_params = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"), #connect to the default 'postgres' database
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT") #5432 is the default PostgreSQL port, 5433 in for wsl postgres used here
}


#Insert params
insert_params = {
    "role_name":  'Data Engineer',
    "company_name": 'Youtube',
    "salary_val": 150000,
    "description_text": 'Develop and deploy machine learning solutions' ,
    "status_val": 'Applied',
    "closing_date": '2026-09-30'
}

#Update params
update_params = {
    "update_status": 'Offer', #['Applied', 'Interview', 'Offer', 'Rejected']
    "job_id_update": 2,
}

#Delete params
delete_params = {
    "job_id_delete": 59,
}

