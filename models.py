from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    """
    User base class
    """
    __tablename__ = "users"
    userid = Column(Integer, primary_key=True)
    username = Column(String)
    mod = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)
    def __repr__(self):
        return f"<User(userid={self.userid}, username={self.username})>"

class Submission(Base):
    """
    Submission base class
    """
    __tablename__ = "submissions"
    submissionid = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, ForeignKey('users.userid'))
    user = relationship("User", backref="submissions")
    url = Column(String)
    appid = Column(Integer, unique=True)
    categoryid = Column(Integer, ForeignKey('categories.categoryid'))
    category = relationship("Category", backref="submissions")
    def __repr__(self):
        return f"<Submission(submissionid={self.submissionid}, userid={self.userid}, url={self.url})>"


class Category(Base):
    """
    Category base class
    """
    __tablename__ = "categories"
    categoryid = Column(Integer, primary_key=True)
    categoryname = Column(String)
    def __repr__(self):
        return f"<Category(categoryid={self.categoryid}, categoryname={self.categoryname})>"
    
class Settings(Base):
    """
    Settings base class
    """
    __tablename__ = "settings"
    settingid = Column(Integer, primary_key=True, autoincrement=True)
    settingname = Column(String)
    settingvalue = Column(String)
    def __repr__(self):
        return f"<Settings(settingid={self.settingid}, settingname={self.settingname}, settingvalue={self.settingvalue})>"