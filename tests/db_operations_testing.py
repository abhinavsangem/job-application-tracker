import pytest

import psycopg2
from psycopg2 import errors

from db_operations import *
from config import db_params

db_name = "test_db"
table_name = "test_table"

@pytest.fixture(scope="function") #function = run once per test function, module = run once per module, session = run once per session
def db_connection():
    db_params["database"] = "postgres"  # Use the test database for testing
    conn = psycopg2.connect(**db_params)
    create_db(conn, db_name)
    conn.close()

    db_params["database"] = db_name  # Use the test database for testing
    conn = psycopg2.connect(**db_params)
    create_table(conn, db_name, table_name)

    yield conn # we will wait until one of the test_ functions has been run before running the stuff after the yield

    conn.rollback() #rollback any aborted states so we can continue the transaction (eg see test_add_duplicate_job which deliberately leaves it in an aborted state)

    cursor = conn.cursor()

    remove_rows = "TRUNCATE {table} RESTART IDENTITY" #restart identity = set the counter for serial columns back to 1
    cursor.execute(sql.SQL(remove_rows).format(table=sql.Identifier(table_name)))

    conn.commit()
    cursor.close()
    conn.close()

#create test database and table - test these too


#verify adding a single job works
#what happens if 2 of the same jobs are added
def test_add_job(db_connection):
    """Validate inserting a job into the database."""
    add_jobs(db_connection, table_name, 'role1', 'company1', 'Applied', 50000, 
                                            'description1', '2023-12-31')

    cursor = db_connection.cursor() #make sure to use the same connection that was used to add the job - if the add fails then everything else does on that connection too and SELECT will see the aborted transaction

    query = "SELECT * FROM {table} WHERE Role=%s AND Company=%s"
    query = sql.SQL(query).format(table = sql.Identifier(table_name))
    cursor.execute(query, ("role1", "company1"))

    result = cursor.fetchone()
    cursor.close()

    assert result is not None
    assert result[1] == "role1" and result[2] == "company1"  # Confirm the correct role and company of the user

#what happens if 2 of the same jobs are added - should get (role, company) dupe error 
def test_add_duplicate_job(db_connection):
    """Validate inserting a duplicate job into the database."""

    with pytest.raises(errors.UniqueViolation, match=f'duplicate key value violates unique constraint "{table_name}_role_company_key"'):
        
        add_jobs(db_connection, table_name, 'role1', 'company1', 'Applied', 50000, 
                                                'description1', '2023-12-31')
        add_jobs(db_connection, table_name, 'role1', 'company1', 'Applied', 600000, 
                                                'description2', '2023-12-31')

#verify updating a job status works
def test_update_job(db_connection):
    """Validate updating jobs in the database."""

    #insert 3 jobs into the test_table
    add_jobs(db_connection, table_name, 'role1', 'company1', 'Applied', 50000, 
                                            'description1', '2023-12-31')
    add_jobs(db_connection, table_name, 'role2', 'company2', 'Applied', 50000, 
                                            'description2', '2024-12-31')
    add_jobs(db_connection, table_name, 'role3', 'company3', 'Applied', 50000, 
                                            'description3', '2025-12-31')

    update_id = 1

    update_job_status(db_connection, table_name, 'Offer', update_id)

    cursor = db_connection.cursor() #make sure to use the same connection 

    query = "SELECT Status FROM {table} WHERE Id=%s"
    query = sql.SQL(query).format(table = sql.Identifier(table_name))

    cursor.execute(query, (update_id,))
    result = cursor.fetchone()
    cursor.close()

    assert result is not None
    assert result[0] == "Offer"  

#what happens if the job to be updated does not exist (check the error message)
def test_update_job_no_job(db_connection):
    """Validate updating jobs in the database with no matching job."""

    #insert 3 jobs into the test_table
    add_jobs(db_connection, table_name, 'role1', 'company1', 'Applied', 50000, 
                                            'description1', '2023-12-31')
    add_jobs(db_connection,table_name, 'role2', 'company2', 'Applied', 50000, 
                                            'description2', '2024-12-31')
    add_jobs(db_connection, table_name, 'role3', 'company3', 'Applied', 50000, 
                                            'description3', '2025-12-31')

    update_id = 87
    
    with pytest.raises(Exception, match=f"Error: No matching Job Id: {update_id} to update"):
        update_job_status(db_connection, table_name, 'Offer', update_id)

#verify deleting a job works
def test_delete_job(db_connection):
    """Validate deleting jobs in the database."""

    #insert 3 jobs into the test_table
    add_jobs(db_connection, table_name, 'role1', 'company1', 'Applied', 50000, 
                                            'description1', '2023-12-31')
    add_jobs(db_connection, table_name, 'role2', 'company2', 'Applied', 50000, 
                                            'description2', '2024-12-31')
    add_jobs(db_connection, table_name, 'role3', 'company3', 'Applied', 50000, 
                                            'description3', '2025-12-31')

    delete_id = 1

    delete_jobs(db_connection, table_name, delete_id)

    cursor = db_connection.cursor() #make sure to use the same connection 

    query = "SELECT Status FROM {table} WHERE Id=%s"
    query = sql.SQL(query).format(table = sql.Identifier(table_name))

    cursor.execute(query, (delete_id,))
    result = cursor.fetchone()
    cursor.close()

    assert result is None

    
#what happens if the job to be deleted does not exist (check the error message)
def test_delete_job_no_job(db_connection):
    """Validate deleting jobs in the database with no matching job."""

    #insert 3 jobs into the test_table
    add_jobs(db_connection, table_name, 'role1', 'company1', 'Applied', 50000, 
                                            'description1', '2023-12-31')
    add_jobs(db_connection, table_name, 'role2', 'company2', 'Applied', 50000, 
                                            'description2', '2024-12-31')
    add_jobs(db_connection, table_name, 'role3', 'company3', 'Applied', 50000, 
                                            'description3', '2025-12-31')

    delete_id = 87
    
    with pytest.raises(Exception, match=f"Error: No matching Job Id: {delete_id} to delete"):
        delete_jobs(db_connection, table_name, delete_id)


