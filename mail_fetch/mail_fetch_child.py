#!/usr/bin/python3
import os
import sys
import json
import logging
import imaplib
import email
import time
import base64
from datetime import datetime
from email.parser import HeaderParser
from urllib.request import Request, urlopen
from email.utils import parsedate_tz, mktime_tz

def create_con(domain, email_address, password, port = 993):
	try:
		conn = imaplib.IMAP4_SSL(domain,port)
		user,password = (email_address,password)
		conn.login(user,password)
		return conn
	except Exception as e:
		mod_logger.debug(sys.exc_info()[1])
		return None


def write_mail(msg, out_dir):
	try:
		mail_subject = msg.get('Subject')[:20].replace(' ','-')
		mail_from = msg.get('From').split(' <')[0].replace(' ','-')
		mail_date = time.strftime('%Y%m%d%H%M%S',time.localtime(mktime_tz(parsedate_tz(msg.get('Date')))))
		filename = os.path.join(out_dir,'%s_%s_%s.msg'%(mail_subject,mail_from,mail_date))

		message_id = msg.get('Message-ID').strip('<>')

		url = "http://127.0.0.1:5000/sendMessage/store"
		headers = {'Content-Type': 'application/json'}
		data = {"filename" : filename, "content" : msg.as_string()}
		json_data = json.dumps(data)
		data_to_post = json_data.encode('utf-8')
		req = Request(url, data_to_post, headers)
		result_obj = urlopen(req)
		result_bin = result_obj.read()
		result = result_bin.decode('utf-8')
		return result
	except Exception as e:
		mod_logger.debug("Error writing mail to file : %s"%e)
		return None

'''
def process_multipart_message(msg,out_dir):
	for part in msg.walk():
		if part.get_content_maintype() == 'multipart':
			continue
		if part.get('Content-Disposition') is None:
			continue
		filename=part.get_filename()
		if filename is not None:
			out_path = os.path.join(out_dir, filename)
			fp = open(out_path, 'wb')
			fp.write(part.get_payload(decode=True))
			fp.close()
'''

def fetch_mail(conn, out_dir):
	try:
		conn.select('INBOX')

		retcode, unseenmsg = conn.search(None, '(UNSEEN)')
		if retcode != 'OK':
			raise Exception ("Error fetching the new mails.")
		unseenmsg_lst = unseenmsg[0].decode('utf-8').split()
		mod_logger.debug("Unread messages : %s "%(str(len(unseenmsg_lst))))

		for num in unseenmsg_lst:
			try:
				mod_logger.debug('Processing message number : %s' %num)
				retcode, data = conn.fetch(num,'(RFC822)')
				msg = email.message_from_bytes(data[0][1])
				'''	
				if msg.get_content_maintype() == 'multipart':
					process_multipart_message(msg,out_dir)
				'''

				retcode, data = conn.store(num,'+FLAGS','\Seen')
				if retcode != 'OK':
					raise Exception ("Error is marking the message to read.")
				filename = write_mail(msg, out_dir)
				if filename is None:
					raise Exception("Error writing mail to file")
				mod_logger.debug("Success %s" %filename)
			except Exception as e:
				mod_logger.debug("Error while processing message : %s" %e)
				retcode, data = conn.store(num,'-FLAGS','\Seen')
				continue

		conn.close()

	except Exception as e:
		mod_logger.debug("ERROR : %s" %e)
		conn.close()



def main():
	while True:
		for line in open(config_file,'r'):
			try:
				inputs = line.split('|')
				conn = create_con(domain = inputs[0],\
						email_address = inputs[2],\
						password = base64.b64decode(inputs[3].encode('utf-8')).decode('utf-8'),\
						port = inputs[1])
				if conn is None:
					raise Exception("Unsuccessful connection!!!")
				mod_logger.debug("Connection Successful to %s"%inputs[2])

				fetch_mail(conn, inputs[4].strip())
			except Exception as e:
				mod_logger.error("Process Failed : %s"%e)
				if conn:
					conn.close()
		time.sleep(30)



if __name__ == "__main__":

	config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.cfg")

	log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'logs')
	if not(os.path.isdir(log_dir)):
		os.makedirs(log_dir)


	mod_logger = logging.getLogger('mail_fetch.child')
	mod_logger.setLevel(logging.DEBUG)

	log_file = os.path.join(log_dir, datetime.now().strftime('%Y%m%d') + '.log')
	file_hdlr = logging.FileHandler(log_file)
	file_hdlr.setLevel(logging.DEBUG)

	console_hdlr = logging.StreamHandler()
	console_hdlr.setLevel(logging.INFO)

	formatter = logging.Formatter('%(asctime)s: {%(name)s} %(levelname)s- %(message)s')
	file_hdlr.setFormatter(formatter)
	console_hdlr.setFormatter(formatter)
	mod_logger.addHandler(file_hdlr)
	mod_logger.addHandler(console_hdlr)

	main()
	
	mod_logger.removeHandler(file_hdlr)
	mod_logger.removeHandler(console_hdlr)
	file_hdlr.flush()
	console_hdlr.flush()
	file_hdlr.close()
	console_hdlr.close()
	del mod_logger,file_hdlr,console_hdlr
