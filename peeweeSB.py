#!python3
#peeweeSB.py - sandbox for testing peewee queries

import datetime
import time

from peewee import *
import numpy
import smtplib

db = SqliteDatabase('quote_tracker.db')

class Rfq(Model):
	quotenum = CharField(primary_key=True,max_length=5, unique=True)
	customer = CharField(max_length=100)
	received = DateTimeField(default=datetime.datetime.now)
	sent = DateTimeField(null=True)

	class Meta:
		database = db

def initialize():
	"""Create the database and table if they don't exist"""
	db.connect()
	db.create_tables([Rfq], safe=True)

def received_today():
	today = datetime.date.today()
	count = 0
	query = Rfq.select()
	for x in query:
		received = x.received.date()
		if received == today:
			count += 1
	print(count)

received_today()





		

