#!/usr/bin/env python3

import os
import sys
import datetime
import time

from peewee import *
import imapclient
import pyzmail
import smtplib
import numpy

#TODO: Change emails to classes

db = SqliteDatabase('quote_tracker.db')
alert_to = ['rreyn@reynoldsman.com', 'dballard@reynoldsman.com']
summary_to = ['rreyn@reynoldsman.com', 'dballard@reynoldsman.com', 'jwheeler@reynoldsman.com', 'dreyn@reynoldsman.com']
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

def average_quote():
	query = Rfq.select().where(Rfq.sent != None)
	timelist = []
	for row in query:
		elapsed = (row.sent - row.received).total_seconds()/86400
		timelist.append(elapsed)

	return round(numpy.mean(timelist), 2)

def received_today():
	today = datetime.date.today()
	count = 0
	query = Rfq.select()
	for x in query:
		received = x.received.date()
		if received == today:
			count += 1
	return count

def sent_today():
	today = datetime.date.today()
	count = 0
	query = Rfq.select()
	for x in query:
		try:
			sent = x.sent.date()
			if sent == today:
				count += 1
		except AttributeError:
			continue
	return count




def normDate(inputdate):
	return "{}/{}/{}".format(inputdate.month, inputdate.day, inputdate.year)

def header_generate():
	now = datetime.datetime.now()
	print('Currently Open Quotes')
	header = '\n\nQuote Number | Customer | Elapsed Days'
	print(header)
	print("="*len(header))
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
			print("{}________|{}{}{}|_____{}".format(rfq.quotenum, block, rfq.customer, block2(), round(elapsed, 2)))
	print("\n\nToday's Summary\n---------------")
	#print total quotes received
	print("\nTotal RFQs Received Today:	{}".format(received_today()))	
	#print total quotes sent
	print("\nTotal Quotes Sent Today: {}".format(sent_today()))
	print("\nAverage Quote Turnaround Time: {} Days".format(average_quote()))

#Email End of Day Report
				
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
	msg += "\nTotal RFQs Received Today: {}".format(received_today())
	#print total quotes sent
	msg += "\nTotal Quotes Sent Today: {}".format(sent_today())
	msg += "\nAverage Quote Turnaround Time: {} Days".format(average_quote())
	return msg

def ack_mail(recip):
	
	avrg = average_quote()
	outserver = smtplib.SMTP('smtp.gmail.com', 587)
	outserver.ehlo()
	outserver.starttls()
	outserver.login('sales@reynoldsman.com', ' Reynolds')
	outserver.sendmail('sales@reynoldsman.com', recip,
	'Subject: RFQ Receipt Acknowledgement\nThank you for your request for quote. Your quote	is being generated, and our	current average quoting time is {} days. If you would like your quote sooner than that, feel free to let us know, and we will do our best to expedite the request.\n\nThank you for your business.\n~The RMI Sales Team'.format(average_quote()))
	print('acknowledgement successfully sent')

def summarymail():
	now = datetime.datetime.now().strftime('%a, %d-%b')
	outserver = smtplib.SMTP('smtp.gmail.com', 587)
	outserver.ehlo()
	outserver.starttls()
	outserver.login('sales@reynoldsman.com', ' Reynolds')
	outserver.sendmail('sales@reynoldsman.com', summary_to, 'Subject: Daily Quote Report-{}.\n{}'.format(now, daily_summary()))
	print('daily summary successfully sent')



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
	#check for new rfqs
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
			try:
				Rfq.create(quotenum=quote, customer=customer)
				if contact:
					ack_mail(contact)
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
	uids = server.gmail_search("\"Reynolds Manufacturing, Inc. - Quotation #\" -Resend")
	previously_recorded = []
	if uids:

		for uid in uids:
			
			
			if uid not in previously_recorded:
			
				rawMessage = server.fetch([uid], ['BODY[]', 'FLAGS'])
				message = pyzmail.PyzMessage.factory(rawMessage[uid][b'BODY[]'])
				subject = message.get_subject()
				finished_quote = subject[42:47]
				print(finished_quote)
				
				try:
					placeholder = int(finished_quote)
					try:
						query = Rfq.get(quotenum=placeholder)
						try:
							check = str(query.sent.date())
							print("already recorded, skipping")
						except AttributeError:			
						
							print('Updating table...')
							dt = datetime.datetime.now()
							query.sent = dt
							query.save()
							print("successfully updated")
							previously_recorded.append(uid)
							print("Quote {} finalized and recorded.".format(finished_quote))
						
					except:
						alert_mail(finished_quote)
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
		if checktime.hour >= 17:
			summarymail()
			print('Entering Nighttime Sleep')
			time.sleep(50400)
		else:
			print('\n\nsleeping for 3 minutes')
			print("{}/{}/{} {}:{}".format(checktime.month, checktime.day, checktime.year, checktime.hour, checktime.minute))
			time.sleep(180)
			clear()








