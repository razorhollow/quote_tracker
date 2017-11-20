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

def average_quote():
	query = Rfq.select().where(Rfq.sent != None)
	timelist = []
	for row in query:
		elapsed = (row.sent - row.received).total_seconds()/86400
		timelist.append(elapsed)

	return round(numpy.mean(timelist), 2)



def daily_summary():
	msg = ""
	now = datetime.datetime.now()
	msg +='Currently Open Quotes'
	header = '\n\nQuote Number | Customer | Elapsed Days\n'
	msg += header

	msg += "="*len(header)
	for rfq in Rfq.select():
		if not rfq.sent:
			dt = rfq.received
			
			spacer = int(len(rfq.customer))
			spacer_block = int((10 - spacer)/2)
			block = '_'*spacer_block
			def block2():
				if spacer % 2 == 1:
					return block + '_'
				else:
					return block
			elapsed = (now-dt).total_seconds()/86400
			msg += ("\n{}________|{}{}{}|_____{}".format(rfq.quotenum, block, rfq.customer, block2(), round(elapsed, 2)))
	msg += ("\n\nToday's Summary\n---------------")
	#print total quotes received
	query = Rfq.select().where(Rfq.sent != None)
	
	count = 0
	today = datetime.date.today()
	for x in query:
		sentdate = x.received.date()
		if sentdate == today:
			count += 1
	msg += "\nTotal RFQs Received Today: {}".format(count)
	#print total quotes sent
	count = 0
	for x in query:
		sentdate = x.sent.date()
		if sentdate == today:
			count += 1
	msg += "\nTotal Quotes Sent Today: {}".format(count)
	msg += "\nAverage Quote Turnaround Time: {} Days".format(average_quote())
	return msg


def summarymail():
	
	outserver = smtplib.SMTP('smtp.gmail.com', 587)
	outserver.ehlo()
	outserver.starttls()
	outserver.login('sales@reynoldsman.com', ' Reynolds')
	outserver.sendmail('sales@reynoldsman.com', 'rreyn@reynoldsman.com', 'Subject: Daily Quote Report.\n{}'.format(daily_summary()))
	print('daily summary successfully sent')

sendmail()



