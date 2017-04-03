#!/usr/bin/env python3

import os
import sys
import datetime
import time

from peewee import *
import imapclient
import pyzmail
import smtplib

db = SqliteDatabase('quote_tracker.db')
alert_to = ['rreyn@reynoldsman.com', 'dballard@reynoldsman.com']
sent_alerts = [14474]

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

def clear():
	os.system('cls' if os.name == 'nt' else 'clear')

def header_generate():
	print('Currently Open Quotes')
	header = '\n\nQuote Number | Customer | Elapsed Days'
	print(header)
	print("="*len(header))
	for rfq in Rfq.select():
		if not rfq.sent:
			dt = rfq.received
			now = datetime.datetime.now()
			spacer = int(len(rfq.customer))
			spacer_block = int((10 - spacer)/2)
			block = '_'*spacer_block
			elapsed = (now-dt).total_seconds()/86400
			print("{}________|{}{}{}|_____{}".format(rfq.quotenum, block, rfq.customer, block, round(elapsed, 2)))

def alert_mail(quotenumber):
	if quotenumber in sent_alerts:
		pass
	else:
		print("found an untracked quote: {}".format(quotenumber))
		print("sending alert email...")
		outserver = smtplib.SMTP('smtp.gmail.com', 587)
		outserver.ehlo()
		outserver.starttls()
		outserver.login('sales@reynoldsman.com', ' Reynolds')
		outserver.sendmail('sales@reynoldsman.com', alert_to, 'Subject: Untracked Quote Alert. \nThe following quotes were sent without being reported: \n{}'.format(quotenumber))
		print('alert mail successfully sent')
		sent_alerts.append(quotenumber)
		time.sleep(3)

def mail_scraper():
	dt = datetime.datetime.now()
	clear()
	print('Logging in to Imap...')
	server = imapclient.IMAPClient('imap.gmail.com', ssl=True)
	server.login(' sales@reynoldsman.com ', ' Reynolds ')
	print('Successfully Logged In')
	print('Seaching for New RFQ\'s...')
	server.select_folder('[Gmail]/Sent Mail')
	uids = server.gmail_search("after: {}/{}/{} newrfq:".format(dt.year,dt.month,dt.day))
	if uids:
		print("{} New RFQs Received Today. Updating Database...".format(len(uids)))
		for uid in uids:
			rawMessage = server.fetch([uid], ['BODY[]', 'FLAGS'])
			message = pyzmail.PyzMessage.factory(rawMessage[uid][b'BODY[]'])
			subject = message.get_subject()
			quote = subject[8:13]
			customer = subject[14:]
			try:
				Rfq.create(quotenum=quote, customer=customer)
			except IntegrityError:
				pass
	else:
		print('No new rfqs found...')
		time.sleep(2)
	#server.logout()
	#server.Dispose()
#check for finalized quotes
	print('Checking for Finalized/Sent Quotes...')
	server.select_folder('INBOX')
	uids = server.gmail_search("\"Reynolds Manufacturing, Inc. - Quotation #\"")
	previously_recorded = []
	if uids:

		for uid in uids:
			if uid not in previously_recorded:
			
				rawMessage = server.fetch([uid], ['BODY[]', 'FLAGS'])
				message = pyzmail.PyzMessage.factory(rawMessage[uid][b'BODY[]'])
				subject = message.get_subject()
				finished_quote = subject[42:47]
				try:
					placeholder = int(finished_quote)
					query = Rfq.select().where(Rfq.quotenum == finished_quote)
					if query:
						check = Rfq.get().where(Rfq.sent > 0)
						if not check:
							print('Updating table...')
							update = Rfq.update(sent=datetime.datetime.now())
							update.execute()
							print("successfully updated")
							previously_recorded.append(uid)
							print("Quote {} finalized and recorded.".format(finished_quote))
					#else:
						#alert_mail(finished_quote)
				except ValueError:
					print('Oops, found an invalid quote email...skipped')
					previously_recorded.append(uid)
					continue
	else:
		print('No Sent Quotes Detected...')

if __name__ == "__main__":
	initialize()
	while True:
		mail_scraper()
		clear()
		header_generate()
		checktime = datetime.datetime.now()
		if checktime.hour >= 16:
			print('Entering Nighttime Sleep')
			time.sleep(50400)
		else:
			print('\n\nsleeping for 3 minutes')
			print("{}/{}/{} {}:{}".format(checktime.month, checktime.day, checktime.year, checktime.hour, checktime.minute))
			time.sleep(180)
			clear()








