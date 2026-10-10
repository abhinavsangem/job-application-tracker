from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, func, Column, CheckConstraint, UniqueConstraint

#Standard Types
from decimal import Decimal
from datetime import datetime, date


#This will hold all fields except id and timestamp
class JobsInsert(SQLModel):
    role: str = Field(max_length = 50)
    company: str | None = Field(index = True, default = None, max_length = 50)
    status:  str = Field(max_length = 10)
    salary: Decimal | None = Field(default = None)
    description: str = Field(max_length = 50)
    closing: date | None = Field(default = None)  

#This will hold all fields and is the main table
class Jobs(JobsInsert, table = True):
    id: int | None = Field(default=None, primary_key=True) #the db already knows this is an autoincrement col since it is an integer primary key (when defined like this in sql model)
    applied: datetime | None = Field(default = None,
        sa_column=Column(DateTime, server_default=func.now(), nullable=False) #sa = sql alchemy feature 
    ) #nullable = False enforces aq NOT NULL in the db, whereas default=None and |None are pythoon side. 
     #sa_column (sql alchemy) is used to define specific db side features like server_default, nullable, etc. that are not available in the SQLModel Field class.
    __table_args__  = (
        UniqueConstraint("role", "company", name="uq_role_company"),
        CheckConstraint("status IN ('Applied', 'Interview', 'Offer', 'Rejected')", name="check_status_valid"),
    )

#Assign all the JobsInsert fields to none as they can be optionally updated by user. 
# We will update and return only the ones the user specifically declared using unset parameter.
class JobsUpdate(SQLModel): #note we dont need to inherit from the JobsInsert since were redifining eveything
    role: str | None = None
    company: str | None = None
    status:  str | None = None
    salary: Decimal | None = None
    description: str | None = None
    closing: date | None = None

