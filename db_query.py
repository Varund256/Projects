import os
import argparse
import cx_Oracle
import json
from getpass import getpass
from datetime import datetime
from dicttoxml import dicttoxml
from collections import OrderedDict
from xml.dom.minidom import parseString
from tempfile import NamedTemporaryFile

def datetime_handler(x):
	if isinstance(x, datetime):
		return x.isoformat()
	raise TypeError("Unknow Type")


def create_dbcon(host , port, sid, user, password):
	try:
		tns_string = '%s/%s@%s:%s/%s'%(user,password,host,port,sid)
		con = cx_Oracle.connect(tns_string)
		print ('Connection to DB Successful.')
		return con
	except Exception as e:
		print('Error connecting to Database %s : %s'%(tns_string, e))
		return None

def fetch_data(dbcon, query):
	try:
		cur = dbcon.cursor()
		cur.execute(query)
		return cur
	except Exception as e:
		print('Error fetching data from Database : %s'%e)
		close(cur)
		return None


def close(obj):
	try:
		print("Closing " + str(obj))
		obj.close()
	except Exception as e:
		print ("Error in closing " + str(obj) + " : " + e)

def parse_data(cur):
	try:
		columns = [i[0] for i in cur.description]
		res_lst = [dict(zip(columns, row)) for row in cur]
		close(cur)
		res_dict = OrderedDict([('Tuple%s'%(int(res_lst.index(row))+1),row) for row in res_lst])
		print("Data parseing completed Successfully.")
		return res_dict
	except Exception as e:
		print("Error in parsing the dataset : %s"%e)
		close(cur)
		return None

def generate_result(datacur):
	try:
		res_dict = parse_data(datacur)
		if res_dict is None:
			raise Exception("Error in parsing the dataset")
		json_obj = json.dumps(res_dict, default=datetime_handler)
		print("JSON object generated.")
		my_item_func = lambda x : x
		xml_obj = parseString(dicttoxml(res_dict, custom_root='Table', attr_type=False, item_func=my_item_func)).toprettyxml()
		print("XML generated.")
		return {'JSON':json_obj, 'XML':xml_obj}
	except Exception as e:
		print("Error in generating result : %s"%e)
		return None


def parse_inputs():
	try:
		parser = argparse.ArgumentParser(description='Fetch data from DB and parse it in JSON and XML')
		parser.add_argument('-H','--hostname', action='store', help='Database Hostname')
		parser.add_argument('-p','--port', action='store', help='Database port')
		parser.add_argument('-s','--sid', action='store', help='Database SID')
		parser.add_argument('-u','--user', action='store', help='Database username')
		parser.add_argument('-P','--password', action='store', help='Database password')
		parser.add_argument('-q','--query', action='store', help='Query to be fired (in double quotes). Conflicts with -f option')
		parser.add_argument('-f','--file', action='store', help='Query file. Conflicts with -q option')
		parser.add_argument('-o','--output_directory', action='store', help='Custom directory to store the output files (optional)')

		args = parser.parse_args()
		if args.query is not None and args.file is not None:
			raise Exception ("Conflicting options -q/--query and -f/--file.")
		input_args = interactive_inputs(args)
		if input_args is None:
			raise Exception ("Error while getting interactive inputs")
		return input_args
	except Exception as e:
		print ("Invalid inputs given : %s"%e)
		return None


def interactive_inputs(args):
	try:
		if args.hostname is None:
			args.hostname = input("DB hostname : ")
			if args.hostname == '':
				raise Exception ("Hostname can not be empty.")
		if args.port is None:
			args.port = input("DB port : ")
			if args.port == '':
				raise Exception ("Port can not be empty.")
		if args.sid is None:
			args.sid = input("DB SID : ")
			if args.sid == '':
				raise Exception ("SID can not be empty.")
		if args.user is None:
			args.user = input("DB username : ")
			if args.user == '':
				raise Exception ("Username can not be empty.")
		if args.password is None:
			args.password = getpass(prompt='DB password : ')
			if args.password == '':
				raise Exception ("Password can not be empty.")
		if args.query is None and args.file is None:
			args.query = input("SQL query (Enter for skip): ")
			if args.query == '':
				args.file = input("SQL query file (Enter to skip): ")
				if args.file == '' or not(os.path.exists(args.file)) or os.stat(args.file).st_size == 0:
					raise Exception (" SQL query or query file required.\nPlease ensure that the file has been given with correct absolute path and it is not empty.")
		if args.output_directory is None:
			args.output_directory = os.path.dirname((os.path.realpath(__file__)))
		else:
			if not(os.path.isdir(args.output_directory)):
				create_dir_flag = input("Output Directory does not exists. Do you want to create it [y/n] : ")
				if create_dir_flag in ('y','Y','Yes','YES','yes'):
					try:
						os.makedirs(args.output_directory)
					except Exception:
						print("Error creating new directory. Saving to default directory!!!")
						args.output_directory = os.path.dirname((os.path.realpath(__file__)))
				else:
					print("Saving to default directory.")
					args.output_directory = os.path.dirname((os.path.realpath(__file__)))
		return args

	except Exception as e:
		print ("Invalid inputs given : %s"%e)
		return None
	

def main():
	try:

		inputs = parse_inputs()
		if inputs is None:
			raise Exception("Invalid inputs!!!")
#		print (inputs)
		dbcon = create_dbcon(host = inputs.hostname, port = inputs.port, sid = inputs.sid, user = inputs.user, password = inputs.password)
		if dbcon is None:
			raise Exception("Unsuccessful connection!!!")

		if inputs.query != '' and inputs.query is not None:
			dataset = fetch_data(dbcon, inputs.query)
			if dataset is None:
				raise Exception("Nothing fetched!!!")
			result_dict = generate_result(dataset)
			if result_dict is None:
				raise Exception ("Error while creating JSON or XML file.")
			with NamedTemporaryFile(suffix='.json', dir = inputs.output_directory, mode='w+t', delete=False) as f:
				f.write(result_dict['JSON'])
			print('JSON file stored in \033[95m%s\033[0m'%f.name)
			f.close()
			with NamedTemporaryFile(suffix='.xml', dir = inputs.output_directory, mode='w+t', delete=False) as f:
				f.write(result_dict['XML'])
			print('XML file stored in \033[95m%s\033[0m'%f.name)
			f.close()

		else:
			composit_result_dict = {'JSON':[], 'XML':[]}
			for query in open (inputs.file, 'r'):
				dataset = fetch_data(dbcon, query)
				if dataset is None:
					print ("Error in getting result for query : %s"%query)
					composit_result_dict['JSON'].append("ERROR\n")
					composit_result_dict['XML'].append("ERROR\n")
					continue
				result_dict = generate_result(dataset)
				if result_dict is None:
					print ("Error in creating JSON or XML for query : %s"%query)
					composit_result_dict['JSON'].append("ERROR\n")
					composit_result_dict['XML'].append("ERROR\n")
					continue
				composit_result_dict['JSON'].append("%s\n"%(result_dict['JSON']))
				composit_result_dict['XML'].append("%s\n"%(result_dict['XML']))

			with NamedTemporaryFile(suffix='.json', dir = inputs.output_directory, mode='w+t', delete=False) as f:
				f.writelines(composit_result_dict['JSON'])
			print('JSON file stored in \033[95m%s\033[0m'%f.name)
			f.close()
			with NamedTemporaryFile(suffix='.xml', dir = inputs.output_directory, mode='w+t', delete=False) as f:
				f.writelines(composit_result_dict['XML'])
			print('XML file stored in \033[95m%s\033[0m'%f.name)
			f.close()

		close(dbcon)

	except Exception as e:
		print("Process Failed : %s"%e)
		close(dbcon)

if __name__=="__main__":
	main()
