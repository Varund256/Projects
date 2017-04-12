import os
import sys
import signal
import argparse
import getpass
import logging
import base64
from threading import Thread
from datetime import datetime

def begin():
	print("\n")
	print("#"*60)

def end():
	print("#"*60)

def stop_process():
	begin()
	try:
		pid = os.popen('ps -aef | grep -v grep |grep mail_fetch_child.py | awk \'{print $2}\'').read().strip()
		if pid == '':
			raise Exception("Process is not running.")
		os.kill(int(pid), signal.SIGKILL)
		logger.info("Process stop.")


	except Exception as e:
		logger.error("Error in killing process : %s" %e)
	end()

def start_process():
	if not(os.path.isfile(config_file)):
		raise Exception("No config file available.\
				\nPlease add at least one email address via 'python3 mail_fetch.py add' command.\
				\nUse -h/--help option for further explanation.")
	begin()
	try:
		logger.debug("Starting the process.")
		os.system(os.path.join(os.path.dirname((os.path.realpath(__file__))), "mail_fetch_child.py") +' &')
		logger.info("Process started.")
	except Exception as e:
		logger.error("Error in starting process : %s" %e)
	end()

def restart_process():
	stop_process()
	start_process()

def delete(email_id):
	begin()
	tmp_config_file = "%s_temp"%config_file
	try:
		fp = open(config_file,'r')
		lines = fp.readlines()
		fp.close()

		fp = open(tmp_config_file,'w')
		for line in lines:
			if '|'+email_id+'|' not in line:
				fp.write(line)
		fp.close()
		os.rename(tmp_config_file,config_file)
		logger.info("Email Address %s has been deleted." %email_id)
	except Exception as e:
		logger.error("Error while deleting the Email Address. Restoring to previous state.")
		os.remove(tmp_config_file)
			
	end()




def add(domain, port, email_address, password, output_directory):
	begin()
	try:
		if os.path.isfile(config_file):
			for line in open(config_file,'r'):
				if '|'+email_address+'|' in line:
					raise Exception("Email Address already configured.")

		fp = open(config_file,'a')
		fp.write("%s|%s|%s|%s|%s\n"%(domain,port,email_address,base64.b64encode(password.encode('utf-8')).decode('utf-8'),output_directory))
		fp.close()
		logger.info("Email Address %s has been added."%(email_address))
	except Exception as e:
		logger.error("Error while adding Email Address : %s" %e)
	end()



def parse_inputs():
	try:
		parser = argparse.ArgumentParser(description='Look for new mails in user INBOX and store them in files.')

		subparser = parser.add_subparsers(dest = "command")

		stop_parser = subparser.add_parser("stop")
		start_parser = subparser.add_parser("start")
		restart_parser = subparser.add_parser("restart")

		add_parser = subparser.add_parser("add")
		add_parser.add_argument('-d','--domain', action='store', help='IMAP domain server')
		add_parser.add_argument('-p','--port', action='store', help='IMAP port number(default : 993)')
		add_parser.add_argument('-e','--email_address', action='store', help='Email Address')
		add_parser.add_argument('-P','--password', action='store', help='Email account password')
		add_parser.add_argument('-o','--output_directory', action='store', help='Custom directory to store the message files (optional)')
		
		delete_parser = subparser.add_parser("delete")
		delete_parser.add_argument('-e','--email_address', metavar = "EMAIL_ID", action='store', help='Email Address to be deleted.')

		args = parser.parse_args()
		#print (args)
		return args

	except Exception as e:
		logger.error("Invalid inputs given : %s"%e)
		return None




def process(args):
	try:
		if args.command == 'stop':
			stop_process()

		if args.command == 'start':
			start_process()

		if args.command == 'restart':
			restart_process()

		if args.command == 'delete':
			if args.email_address is None:
				args.email_address = input("Email address to be removed : ")
			delete(args.email_address)

		if args.command == 'add':
			if args.domain is None:
				args.domain = input("IMAP Domain server : ")
			if args.port is None:
				args.port = 993
			if args.email_address is None:
				args.email_address = input("Email Address : ")
			if args.password is None:
				args.password = getpass.getpass(prompt = 'Email account password : ')
			if args.output_directory is None:
				args.output_directory = os.path.dirname((os.path.realpath(__file__)))
			else:
				if not(os.path.isdir(args.output_directory)):
					create_dir_flag = input("Output Directory does not exists. Do you want to create it [y/n] : ")
					if create_dir_flag in ('y','Y','Yes','YES','yes'):
						try:
							os.makedirs(args.output_directory)
						except Exception:
							logger.info("Error creating new directory. Saving to default directory!!!")
							args.output_directory = os.path.dirname((os.path.realpath(__file__)))
					else:
						logger.info("Saving to default directory.")
						args.output_directory = os.path.dirname((os.path.realpath(__file__)))

			add( args.domain, args.port, args.email_address, args.password, args.output_directory)



	except Exception as e:
		logger.error("Invalid input given : %s"%e)

def main():
	try:
		args = parse_inputs()
		if args is None:
			raise Exception("Error in parsing the inputs.")
		process(args)


	except Exception as e:
		logger.error("Process Failed : %s"%e)

if __name__ == "__main__":
	try:
		config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.cfg")
		
		log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'logs')
		if not(os.path.isdir(log_dir)):
			os.makedirs(log_dir)

		logger = logging.getLogger('mail_fetch')
		logger.setLevel(logging.DEBUG)

		log_file = os.path.join(log_dir, datetime.now().strftime('%Y%m%d') + '.log')
		file_hdlr = logging.FileHandler(log_file)
		file_hdlr.setLevel(logging.DEBUG)

		console_hdlr = logging.StreamHandler()
		console_hdlr.setLevel(logging.INFO)

		formatter = logging.Formatter('%(asctime)s: {%(name)s} %(levelname)s- %(message)s')
		file_hdlr.setFormatter(formatter)
		console_hdlr.setFormatter(formatter)

		logger.addHandler(file_hdlr)
		logger.addHandler(console_hdlr)
	
		main()

		logger.removeHandler(file_hdlr)
		logger.removeHandler(console_hdlr)
		file_hdlr.flush()
		console_hdlr.flush()
		file_hdlr.close()
		console_hdlr.close()
		del logger,file_hdlr,console_hdlr

	except Exception as e:
		print("ERROR : %s"%e)

