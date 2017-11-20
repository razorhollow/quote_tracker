#!python3
#peeweeSB.py - sandbox for testing peewee queries

import datetime
import time

from peewee import *
import numpy
import smtplib
import imapclient
import pyzmail

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

#generate acknowledgement email
def rfq_ack():
	dt = datetime.datetime.now()
	print('Logging in to Imap...')
	server = imapclient.IMAPClient('imap.gmail.com', ssl=True)
	server.login(' rob@razorhollow.com ', ' 2924201Cfi ')
	print('Successfully Logged In')
	print('Seaching for New RFQ\'s...')
	server.select_folder('[Gmail]/Sent Mail')
	uids = server.gmail_search("after: {}/{}/{} newrfq:".format(dt.year,dt.month,dt.day))
	if uids:
		print("{} New RFQs Received Today. Updating Database...".format(len(uids)))
		for uid in uids:
			rawMessage = server.fetch([uid], ['BODY[]', 'FLAGS'])
			message = pyzmail.PyzMessage.factory(rawMessage[uid][b'BODY[]'])
			subject = message.get_subject().replace(' ', '').split(':')
			quote = subject[1]
			customer = subject[2]
			try:
				contact = subject[3]
			except IndexError:
				contact = None
				print('No contact specified, skipping ack email')
			print(quote)
			print(customer)
			if contact:
				print(contact)
			





def ack_mail(recip):
	
	outserver = smtplib.SMTP('smtp.gmail.com', 587)
	outserver.ehlo()
	outserver.starttls()
	outserver.login('sales@reynoldsman.com', ' Reynolds')
	outserver.sendmail('sales@reynoldsman.com', recip, 'Subject: RFQ Receipt Acknowledgement\nThank you for your request for quote. Your quote is being generated, and our current average quoting time is 3 days. If you would like your quote sooner than that, feel free to let us know, and we will do our best to expedite the request.\n\nThank you for your business.\n~The RMI Sales Team')
	print('daily summary successfully sent')

mail_scraper()



