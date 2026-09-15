
"""
JOB TRACKER
1. Create DB and table for jobs
2. View jobs
3. Add job
4. Modify job
5. Delete job
6. Exit
"""

#TO START
# sudo service postgresql start
# sudo -u postgres psql -p 5433

#bug checking
# checks for making sure db and table dont exist (and ask user if thy ewant to delete and recreate)
# what if a job was inserted twice (eg duplication of role and company)
# updating a job that doesnt exist

#Rule
#only do create and closing of conenctions in the main.py
# with cursor() as curson - automatically closes the cursor
# with connection() - does not close the connection automatically

import psycopg2
from psycopg2 import sql

from config import db_params

# Connect to the PostgreSQL server via pyscopg2
def connect_to_postgres(db_name = "postgres"):
    try:
        db_params["database"] = db_name  #change the database to the newly created one
        conn = psycopg2.connect(**db_params) #this also makes it a transation without needing a commit() (context manager). automatically closes the connection.
        print("Connection to PostgreSQL successful!")
        
        return conn        

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


def create_db(conn, db_name):
    
    conn.autocommit = True  #needs this avoid making it a transaction (which happens by default when autocommit=False and cur.execute is run)

    try:
        cursor = conn.cursor()

        #force to avoid db being access by other users issue, forcefully terminate all open connections to job_tracker

        disconnect_query = sql.SQL("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = {database} AND pid <> pg_backend_pid(); """ #pg_backend_pid() is my script's connection to db (ie. disconnect everyone else but me)
            
        ).format(database = sql.Literal(db_name))
    
        cursor.execute(disconnect_query)
        print("Terminated all other active connections.")

        cursor.execute(
            sql.SQL("DROP DATABASE IF EXISTS {database};").format(
            database=sql.Identifier(db_name))
        )

        cursor.execute(
            sql.SQL("CREATE DATABASE {database};").format(
            database=sql.Identifier(db_name))
        )
        #cursor.execute(f"CREATE DATABASE {db_name};") dont do this (to avoid injections)
        print(f"Database {db_name} created successfully!")

        cursor.close()

    except Exception as error:
        print(f"Error creating database {db_name}: {error}") #will error if db doesnt exist
        raise #re-raise the error


#..now define the table

def create_table(conn, db_name, table_name):
    try:             
        # 2. Open a cursor to perform database operations
        with conn.cursor() as cursor: #this will automatically close the cursor at the end of the block

            cursor.execute(
                sql.SQL("DROP TABLE IF EXISTS {table}").format(
                table=sql.Identifier(table_name))
            )

            create_table_query = """
                CREATE TABLE {table} (
                    Id SERIAL PRIMARY KEY, 
                    Role VARCHAR(50) NOT NULL,
                    Company VARCHAR(50),
                    Status VARCHAR(10) CHECK (Status IN ('Applied', 'Interview', 'Offer', 'Rejected')),
                    Salary DECIMAL,
                    Description VARCHAR(50) NOT NULL,
                    Applied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    Closing DATE,
                    UNIQUE (Role, Company) 
                ); 
            """

            cursor.execute(
                sql.SQL(create_table_query).format(
                table=sql.Identifier(table_name))
            )

            conn.commit() # Commit the transaction to save changes to the database, otherwise it will rollback by default

            print(f"Table {db_name}.{table_name} created successfully!")


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
