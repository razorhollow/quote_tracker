import imapclient, pyzmail, re, datetime, os, smtplib, csv, time
from tabulate import tabulate

server = imapclient.IMAPClient('imap.gmail.com', ssl=True)
open_quotes = {}
tattletail_list = []
ticker = 0
uids = []
def imap_login():
    clearscreen()
    print('logging in to IMAP')
    if ticker < 1:
        server.login(' sales@reynoldsman.com ', ' Reynolds ')
        print('successfully logged in')
        global ticker
        ticker += 1
    else:
        pass
def new_quote():
    imap_login()
    dt = datetime.datetime.now()
    print('searching for newly submitted rfqs')
    server.select_folder('[Gmail]/Sent Mail')
    uids = server.gmail_search("after:{}/{}/{} newrfq:".format(dt.year,dt.month, dt.day))
    for uid in uids:
        rawMessage = server.fetch([uid], ['BODY[]', 'FLAGS'])
        message = pyzmail.PyzMessage.factory(rawMessage[uid][b'BODY[]'])
        subject = message.get_subject()
        quote = subject[8:13]
        customer = subject[14:]
        if quote in open_quotes.keys():
            pass
        else:
            open_quotes[quote] = (customer, dt, uid)
    #check inbox for sent quotes
    server.select_folder('INBOX')
    uids = server.gmail_search("Reynolds Manufacturing, Inc. - Quotation #")
    if bool(uids):
        for key in open_quotes:
            quote_stop(key)

def clearscreen():
    os.system("cls" if os.name == "nt" else "clear")

def quote_stop(quote):
    dt = datetime.datetime.now()
    for uid in uids:
        rawMessage = server.fetch([uid], ['BODY[]', 'FLAGS'])
        message = pyzmail.PyzMessage.factory(rawMessage[uid][b'BODY[]'])
        subject = message.get_subject()
        finished_quote = subject[42:47]
        if finished_quote in open_quote.keys():
            #pop quote to csv append
            csvline = open_quote.pop(open_quote.index(finished_quote))
            outputFile = open('completed_quotes.csv', 'w', newline='')
            outputWriter = csv.writer(outputFile)
            outputWriter.writerow(finished_quote, csvline[0], csvline[1], datetime.datetime.now())
            outputFile.close()
        else:
            #send an email alert
            tattletail_list.append(finished_quote)
    global tattletail_list
    if len(tattletail_list) > 0:
        print('sending snitch mail...')
        outserver = smtplib.SMTP('smtp.gmail.com', 587)
        outserver.ehlo()
        outserver.starttls()
        outserver.login('sales@reynoldsman.com', ' Reynolds')
        outserver.sendmail('sales@reynoldsman.com', ['rreyn@reynoldsman.com', 'dballard@reynoldsman.com'], 'Subject: Untracked Quote Alert. \nThe following quotes were sent without being reported: \n{}'.format(tattletail_list))
        print('snitch mail successfully sent')
        tattletail_list = []

def imap_logout():
    print('logging out...')
    print('successfully logged out')
    time.sleep(2)
    

#testing
while True:
    imap_login()
    new_quote()
    print(open_quotes)
    time.sleep(10)
