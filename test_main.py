from fastapi.testclient import TestClient
import pytest
from main import app, get_session

from db_operations import custom_create_engine, \
create_db, create_table, database_url

from sqlmodel import Session, SQLModel, create_engine

from models import JobsInsert, Jobs

from decimal import Decimal
from datetime import datetime, date


db_name = "test_db_fastapi"

@pytest.fixture(name="session")
def session_fixture():
    # engine = create_engine(
    #     "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    # )
    # SQLModel.metadata.create_all(engine)

    postgres_engine = custom_create_engine() #this is similar to "conn" in pyscopg2. engine is based off default postgres db
    create_db(postgres_engine, db_name) #create db_name from default postgres db (if it doesnt already exist)

    #global new_db_engine
    new_db_engine = custom_create_engine(db_name=db_name) #create a new engine connected to the new database
    create_table(new_db_engine) #create table in new db

    with Session(new_db_engine) as session:
        yield session

    #the session fixture ends (ie. this code runs) after the client fixture ends
    SQLModel.metadata.drop_all(new_db_engine) #drop all tables in db_name if they exist 
    postgres_engine.dispose()
    new_db_engine.dispose()



@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


#verify viewing a job works
def test_view_jobs(client: TestClient, session: Session):
    """Validate updating jobs in the database."""

    job_1 = JobsInsert(
               role = 'role1', 
               company = 'company1', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_2 = JobsInsert(
               role = 'role2', 
               company = 'company2', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    
    db_job_1 = Jobs.model_validate(job_1)
    session.add(db_job_1)
    session.commit()
    session.refresh(db_job_1)

    db_job_2 = Jobs.model_validate(job_2)
    session.add(db_job_2)
    session.commit()
    session.refresh(db_job_2)

    response = client.get("/jobs/?limit=1") #only getting 1 job
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1

    assert data[0]["id"] == db_job_1.id
    assert data[0]["role"] == db_job_1.role
    assert data[0]["company"] == db_job_1.company
    assert data[0]["status"] == db_job_1.status
    assert Decimal(data[0]["salary"]) == db_job_1.salary
    assert datetime.fromisoformat(data[0]["applied"]) == db_job_1.applied
    assert date.fromisoformat(data[0]["closing"]) == db_job_1.closing
    assert data[0]["description"] == db_job_1.description

    #if limit = 2
    # assert data[1]["id"] == db_job_2.id
    # assert data[1]["role"] == db_job_2.role
    # assert data[1]["company"] == db_job_2.company
    # assert data[1]["status"] == db_job_2.status
    # assert Decimal(data[1]["salary"]) == db_job_2.salary
    # assert datetime.fromisoformat(data[1]["applied"]) == db_job_2.applied
    # assert date.fromisoformat(data[1]["closing"]) == db_job_2.closing
    # assert data[1]["description"] == db_job_2.description




#verify adding a single job works (excluding optional columns)
def test_add_job(client: TestClient):
    """Validate inserting a job into the database."""

    response = client.post(
        "/jobs/", json={"role": "role1",
                        "status": "Applied",
                        "description": "data science role",
                        "salary": 50}
    )
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["role"] == "role1"
    assert data["status"] == "Applied"
    assert data["description"] == "data science role"
    assert data["salary"] == '50'

#what happens if 2 of the same jobs are added (ie. duped role and company) - uniqueness error should be raised from db
def test_add_duplicate_job(client: TestClient):
    """Validate inserting a duplicate job into the database."""
    response1 = client.post(
    "/jobs/", json={"role": "role1",
                    "company": "company1",
                    "status": "Applied",
                    "description": "data science role",
                    "salary": 50}
    )

    response2 = client.post(
    "/jobs/", json={"role": "role1",
                    "company": "company1",
                    "status": "Applied",
                    "description": "data analyst role",
                    "salary": 50}
    )

    assert response2.status_code == 409
    assert response2.json() == {"detail": "A job with this role and company already exists."}

#verify updating a job status works
def test_update_job(client: TestClient, session: Session):
    """Validate updating jobs in the database."""

    job_1 = JobsInsert(
               role = 'role1', 
               company = 'company1', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_2 = JobsInsert(
               role = 'role2', 
               company = 'company2', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_3 = JobsInsert(
               role = 'role3', 
               company = 'company3', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')

    db_job_1 = Jobs.model_validate(job_1)
    session.add(db_job_1)
    session.commit()
    session.refresh(db_job_1)

    db_job_2 = Jobs.model_validate(job_2)
    session.add(db_job_2)
    session.commit()
    session.refresh(db_job_2)
        
    db_job_3 = Jobs.model_validate(job_3)
    session.add(db_job_3)
    session.commit()
    session.refresh(db_job_3)


    response = client.patch(f"/jobs/{db_job_2.id}", json={"status": "Offer"})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == db_job_2.status


#verify updating a job status returns the correct when there is no matching job
def test_update_job_no_job(client: TestClient, session: Session):
    """Validate updating jobs in the database."""

    job_1 = JobsInsert(
               role = 'role1', 
               company = 'company1', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_2 = JobsInsert(
               role = 'role2', 
               company = 'company2', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_3 = JobsInsert(
               role = 'role3', 
               company = 'company3', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')

    db_job_1 = Jobs.model_validate(job_1)
    session.add(db_job_1)
    session.commit()
    session.refresh(db_job_1) #not needed for the id, but included anyway for safety

    db_job_2 = Jobs.model_validate(job_2)
    session.add(db_job_2)
    session.commit()
    session.refresh(db_job_2)
        
    db_job_3 = Jobs.model_validate(job_3)
    session.add(db_job_3)
    session.commit()
    session.refresh(db_job_3)


    response = client.patch(f"/jobs/{db_job_3.id + 1}", json={"status": "Offer"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


#verify deleting a job works
def test_delete_job(client: TestClient, session: Session):
    """Validate updating jobs in the database."""

    job_1 = JobsInsert(
               role = 'role1', 
               company = 'company1', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_2 = JobsInsert(
               role = 'role2', 
               company = 'company2', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_3 = JobsInsert(
               role = 'role3', 
               company = 'company3', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')

    db_job_1 = Jobs.model_validate(job_1)
    session.add(db_job_1)
    session.commit()
    session.refresh(db_job_1)

    db_job_2 = Jobs.model_validate(job_2)
    session.add(db_job_2)
    session.commit()
    session.refresh(db_job_2)
        
    db_job_3 = Jobs.model_validate(job_3)
    session.add(db_job_3)
    session.commit()
    session.refresh(db_job_3)


    response = client.delete(f"/jobs/{db_job_2.id}")
    db_val = session.get(Jobs, db_job_2.id)

    assert db_val is None
    assert response.status_code == 200
    assert response.json() == {"ok": True}

#verify deleting a job works when no matching id
def test_delete_job_no_job(client: TestClient, session: Session):
    """Validate updating jobs in the database."""

    job_1 = JobsInsert(
               role = 'role1', 
               company = 'company1', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_2 = JobsInsert(
               role = 'role2', 
               company = 'company2', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')
    job_3 = JobsInsert(
               role = 'role3', 
               company = 'company3', 
               status = 'Applied',
               salary = 50000,
               description = 'description',
               closing = '2026-10-14')

    db_job_1 = Jobs.model_validate(job_1)
    session.add(db_job_1)
    session.commit()
    session.refresh(db_job_1)

    db_job_2 = Jobs.model_validate(job_2)
    session.add(db_job_2)
    session.commit()
    session.refresh(db_job_2)
        
    db_job_3 = Jobs.model_validate(job_3)
    session.add(db_job_3)
    session.commit()
    session.refresh(db_job_3)


    response = client.delete(f"/jobs/{db_job_3.id + 1}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}





