#raises the appropriate HTTPException based on the IntegrityError raised by the db/sqlalchemy
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def raise_integrity_error(error: IntegrityError):
    error_msg = error.orig.args[0]
    if "role" in error_msg:
        raise HTTPException( #raised by FASTAPI rather than db
            status_code=409,
            detail="A job with this role and company already exists."
        )

    elif "status" in error_msg:
        raise HTTPException( #error raised by FASTAPI
            status_code=400,
            detail="Check contraint for status violated"
        ) 
    elif "salary" in error_msg:
        raise HTTPException( #error raised by FASTAPI
            status_code=400,
            detail="Check contraint for salary violated"
        ) 

