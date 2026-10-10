
"""
JOB TRACKER
1. Create DB and table for jobs
2. View jobs
3. Add job
4. Modify job
5. Delete job
"""

#TO START
# sudo service postgresql start
# sudo -u postgres psql -p 5433

#bug checking
# checks for making sure db and table dont exist (and ask user if thy ewant to delete and recreate)
# what if a job was inserted twice (eg duplication of role and company)
# updating a job that doesnt exist

#fastapi/sqlalchemy/sqlmodel
from sqlalchemy import text, URL
from sqlmodel import Session, SQLModel, create_engine

#config
from config import db_params

database_url = URL.create(
    "postgresql+psycopg2",
    username=db_params["user"],
    password=db_params["password"],
    host=db_params["host"],
    port=db_params["port"],
    database=db_params["database"],
)


# Connect to the PostgreSQL database via sqlalchemy
def custom_create_engine(db_name = "postgres"):
    try:
        #database_url=database_url.set(database=db_name)
        engine = create_engine(database_url.set(database=db_name))
        return engine        

    except Exception as error:
        print(f"Error connecting to database: {error}")




#1. Create the database and table 

# Certain PostgreSQL administrative operations cannot be run inside a transaction block (eg create database) 
# connection.autocommit = True to immediately commit each individual SQL statement as soon as it executes, rather than waiting for a commit() at the end 

#transactions occur when a cmmit() is defined at the end OR it is in a WITH statement

#autocommit = True (use where transactions not allowed and each idividual staement is a commit)
#statement - coomit
#statement1 - coomit
#statement2 - coomit

#autocommit = false (use for transactions)
#statement - not commit
#statement1 - not commit
#statement2 - not commit
#commit() - now commit all 3. the explicit commit() or WITH eithout a commit() makes it a transation

#create new db by default if one doesnt exist at start of session
def create_db(engine, db_name):
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn: #autocommit needed since we are creating DB and that cannot be done in a transaction block
            print("Successfully connected to the postgres database!")

            #check if the database already exists

            check_db_query = text("""
                SELECT 1 as res
                FROM pg_database 
                WHERE datname = :database 
            """
            )
        
            check_db_result = conn.execute(check_db_query, {"database": db_name})
            res = check_db_result.fetchone()

            if res:
                print("Database already exists.")

                # #disconnect all other active connections to the database to allow future use of database (specifically drop, alter, or replace of database) --not needed here?
                # disconnect_query = text("""
                # SELECT pg_terminate_backend(pid) 
                # FROM pg_stat_activity 
                # WHERE datname = :database AND pid <> pg_backend_pid(); """ #pg_backend_pid() is my script's connection to db (ie. disconnect everyone else but me)          
                # )
        
                # conn.execute(disconnect_query, {"database": new_db})

            else:
                print("No DB.. Creating new database..")
                database = engine.dialect.identifier_preparer.quote(db_name) #this will prevent injection
                conn.execute(
                    text(f"CREATE DATABASE {database}"))
                print(f"Database {db_name} created successfully!")


    except Exception as e:
        print(f"Connection failed: {e}")


#..now define the table
#engine will already be connected to the new database if it was created, so we can use the same engine to create tables in the new database

def create_table(engine):
    try:             
        SQLModel.metadata.create_all(engine)  #will create all tables defined in the SQLModel classes (in this case, the Jobs table) if it doesnt exist already.
        print("Jobs table already exists, or created successfully")
    except Exception as error:
        print(f"Error creating table: {error}")
        raise



#2. View Jobs
def view_jobs(conn,table_name):
    try:
        with conn.cursor() as cursor:
                
            # 3. Execute the SQL query
            select_query = "SELECT * FROM {table} ORDER BY applied;"
            
            # Always pass query parameters as a tuple to prevent SQL injection!
            cursor.execute(
                sql.SQL(select_query).format(table = sql.Identifier(table_name))
            )
            
            # 4. Fetch the data using one of the fetch methods
            records = cursor.fetchall()
            
            # 5. Process your data
            print(f"Total rows retrieved: {len(records)}")
            for row in records:
                # Each row is returned as a tuple ordered by your SELECT clause
                print(f"Id: {row[0]} | Role: {row[1]} | Company: {row[2]} | Status: {row[3]} | Salary: {row[4]} | \
                    Description: {row[5]} | Applied: {row[6]} | Closing: {row[7]}")

    except Exception as error:
        print(f"Error viewing {table_name} table:", error)
        raise



#3. Add Jobs potentially avoid duplicates by checking if the role and company already exist
def add_jobs(conn,table_name, role_name, company_name, status_val, salary_val, 
                                            description_text, closing_date):
    try:
        with conn.cursor() as cursor:
            
            # 3. Execute the SQL query
            insert_query = "INSERT INTO {table} (Role, Company, Status, Salary, Description, Closing) \
                            VALUES (%s, %s, %s, %s, %s, %s) RETURNING Id, Role, Company;"
            insert_query = sql.SQL(insert_query).format(table = sql.Identifier(table_name))
            
            # Always pass query parameters as a tuple to prevent SQL injection!
            cursor.execute(insert_query, (role_name, company_name, status_val, salary_val, 
                                        description_text, closing_date))
            
            records = cursor.fetchone()

            conn.commit()  # Commit the transaction to save changes to the database

            print(f"Record Inserted:\nId: {records[0]} | Role: {records[1]} | Company: {records[2]}")
            
    except Exception as error:
        print(f"Error updating {table_name} table:", error)
        raise




#4. Modify Job status
def update_job_status(conn, table_name, update_status, job_id_update):
    try:
        with conn.cursor() as cursor:
            
            # 3. Execute the SQL query
            modify_query = "UPDATE {table} SET Status = %s WHERE Id = %s RETURNING Id, Status;"
            modify_query = sql.SQL(modify_query).format(table = sql.Identifier(table_name))
            
            # Always pass query parameters as a tuple to prevent SQL injection!
            cursor.execute(modify_query, (update_status, job_id_update))

            conn.commit()  # Commit the transaction to save changes to the database

            records = cursor.fetchone()
            if records == None:
                raise Exception(f"Error: No matching Job Id: {job_id_update} to update") #making it an exception so that the test can catch it and validate it 
            else:
                print(f"Status of Job Id {job_id_update} was modified to {update_status}!")

    except Exception as error:
        print(f"Error updating {table_name} table:", error)
        raise  #re-raising it so that the test can catch it and validate it -  the raise will kill the program


#5. DELETE Jobs
def delete_jobs(conn, table_name, job_id_delete):
    try:
        with conn.cursor() as cursor:
            
            # 3. Execute the SQL query
            delete_query = "DELETE FROM {table} WHERE Id = %s RETURNING Id, Status;"
            delete_query = sql.SQL(delete_query).format(table = sql.Identifier(table_name))
            
            # Always pass query parameters as a tuple to prevent SQL injection!
            cursor.execute(delete_query, (job_id_delete,))

            conn.commit()  # Commit the transaction to save changes to the database

            records = cursor.fetchone()
            if records == None:
                raise Exception(f"Error: No matching Job Id: {job_id_delete} to delete")
            else:
                print(f"Job Id {job_id_delete} was deleted!")

    except Exception as error:
        print(f"Error deleting from {table_name} table:", error)
        raise #re-raising it so that the test can catch it and validate it -  the raise will kill the program
