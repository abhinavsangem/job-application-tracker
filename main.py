from config \
import option, db_name, table_name, \
insert_params, update_params, delete_params

from db_operations \
import connect_to_postgres, create_db, \
create_table, view_jobs, add_jobs, update_job_status, delete_jobs 


if option == "create_db_table":
    conn = connect_to_postgres() #default = "postgres" database
    create_db(conn, db_name)
    conn.close()

    conn = connect_to_postgres(db_name) 
    create_table(conn, db_name, table_name)
    conn.close()
else:
    conn = connect_to_postgres(db_name)
    if option == "view":
        view_jobs(conn, table_name)
    elif option == "insert":
        add_jobs(conn, table_name, **insert_params)
    elif option == "update":
        update_job_status(conn, table_name, **update_params)
    elif option == "delete":
        delete_jobs(conn, table_name, **delete_params)
    conn.close()
