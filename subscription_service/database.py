from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    subscriptions = relationship("Subscription", back_populates="user")
    journals = relationship("Journal", back_populates="user")
    posts = relationship("Post", back_populates="user")


class Journal(Base):
    __tablename__ = "journals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="journals")
    posts = relationship("Post", back_populates="journal")
    subscriptions = relationship("Subscription", back_populates="journal")


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    journal_id = Column(Integer, ForeignKey("journals.id"))
    user = relationship("User", back_populates="subscriptions")
    journal = relationship("Journal", back_populates="subscriptions")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journals.id"))
    text = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    journal = relationship("Journal", back_populates="posts")
    user = relationship("User", back_populates="posts")


Base.metadata.create_all(bind=engine)
