# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from sqlalchemy.orm import sessionmaker
from project_spider.models import Posts, db_connect, create_posts_table


class PostsPipeline(object):
	"""Posts pipeline for storing scraped items from cdi in database"""
	
	def __init__(self):
		"""
		Initializes database connection and sessionmaker.
		  Creates posts table.
		"""
		engine = db_connect()
		create_posts_table(engine)
		self.Session = sessionmaker(bind=engine)
	
	def process_item(self, item, spider):
		"""Save cdi items from spider to database.

		This method is called for every item pipeline component.

		"""
		session = self.Session()
		post = Posts(**item)

		try:
			session.add(post)
			session.commit()
		except:
			session.rollback()
			raise
		finally:
			session.close()
		return item




