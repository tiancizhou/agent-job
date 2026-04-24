import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))


from database import SessionLocal, initialize_database
from models import Employee, User, hash_password


initialize_database()
db = SessionLocal()
try:
    employee = db.query(Employee).filter(Employee.employee_no == "64003").first()
    if not employee:
        db.add(Employee(employee_no="64003", name="管理员", status="active"))

    user = db.query(User).filter(User.employee_no == "64003").first()
    if not user:
        db.add(User(employee_no="64003", password_hash=hash_password("123456"), is_admin=True))

    db.commit()
    print("Admin account ready: 64003")
finally:
    db.close()
