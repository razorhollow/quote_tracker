import imapclient, pyzmail, re, datetime

server = imapclient.IMAPClient('imap.gmail.com', ssl=True)
server.login(' sales@reynoldsman.com ', ' Reynolds ')

year = ''
month = ''
day = ''

def quote_start():
    dt = datetime.datetime.now()
    dys = datetime.timedelta(days=1)
    yd = dt - dys
    server.select_folder('[Gmail]/Sent')
    uids = server.gmail_search("after:{}/{}/{} newrfq:".format(yd.year,yd.month, yd.day))


