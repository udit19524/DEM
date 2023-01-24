from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
Base = declarative_base()
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String,)
    last_name = Column(String)
    gender = Column(String)
    email = Column(String)
    ip_address = Column(String)
    
class User(Base):
    __tablename__ = "user_transform"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String,)
    valid_email = Column(String)
    valid_ip = Column(String)