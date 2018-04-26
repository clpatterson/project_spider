# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TEXT

from project_spider import settings

DeclarativeBase = declarative_base()

def db_connect():
	"""
	Performs databse connection using database settings from settings.py.
	  Returns sqlalchemy engine instance.
	"""

	return create_engine(URL(**settings.DATABASE))

def create_posts_table(engine):
	""""""
	DeclarativeBase.metadata.create_all(engine)

class Posts(DeclarativeBase):
	"""Sqlalchemy spiders model"""
	__tablename__ = "posts"

	id = Column(Integer, primary_key=True)
	cdi = Column('cdi', String)
	title = Column('title', String)
	date = Column('date', DateTime, nullable=True)
	source = Column('source', String, nullable=True)
	text = Column('text', TEXT(length=None,), nullable=True)
	url = Column('url', String)
	screenshot_url = Column('screenshot_url', String)


