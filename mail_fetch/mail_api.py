import os
import json
import logging
from flask import Flask, abort, jsonify, request

app = Flask(__name__)

@app.route('/sendMessage/findMail/<msgid>',methods=['GET'])
def getEmp(msgid):
	abs_file_name = None
	for line in open(INDEX_FILE,'r'):
		if msgid+',' in line:
			abs_file_name = line.split(',')[1].strip()
			break
	if abs_file_name is None:
		return jsonify({"MESSAGE CANNOT BE TRACKED" : msgid})
	if not os.path.isfile(abs_file_name):
		return jsonify({"MESSAGE NOT AVAILABLE" : abs_file_name})
	fp = open(abs_file_name,'r')
	lines = fp.readlines()
	fp.close()
	return json.dumps(lines)


@app.route('/sendMessage/store', methods=['POST'])
def newMessage():
	abs_file_name = os.path.join(DATA_DIR,request.json['filename'])
	fp = open(abs_file_name,'w')
	fp.write(request.json['content'])
	fp.close()

	if not os.path.isfile(INDEX_FILE):
		last_line_pos = 0
	else:
		for line in open(INDEX_FILE,'r'):
			if ','+ abs_file_name + '\n' in line:
				return jsonify
		ifp = open(INDEX_FILE,'rb')
		file_lenght = ifp.seek(0,2)
		if file_lenght == 0:
			ifp.close()
			last_line_pos = 0
		else:
			block_size = 1024
			if file_lenght < 1024:
				block_size = file_lenght
			ifp.seek(-block_size,2)
			buff = ifp.read(block_size)
			last_line_pos_buff = buff.decode('utf-8').rfind('\n', 0, buff.decode('utf-8').rfind('\n'))
			if last_line_pos_buff == -1:
				return jsonify({"ERROR" : "ERROR"})
			last_line_pos = file_lenght - (block_size - last_line_pos_buff)
			ifp.close()
	
	new_id = 1
	if last_line_pos != 0:
		ifp = open(INDEX_FILE, 'r')
		ifp.seek(last_line_pos+1,0)
		last_line = ifp.readline()
		ifp.close()
		last_id = int(last_line.split(',')[0])
		new_id = last_id + 1

	ifp = open(INDEX_FILE, 'a')
	ifp.write("%s,%s\n" %(new_id, abs_file_name))
	ifp.close()

	return jsonify({"Message_ID" : new_id})




if __name__ == "__main__":
	HOME_DIR = os.path.dirname(os.path.realpath(__file__))
	DATA_DIR = os.path.join(HOME_DIR, 'data')
	LOG_DIR = os.path.join(HOME_DIR, 'logs')
	INDEX_FILE = os.path.join(DATA_DIR, 'index.txt')

	log = logging.getLogger('werkzeug')
	log.setLevel(logging.DEBUG)
	log_file = os.path.join(LOG_DIR,"mail_api.log")
	file_hdlr = logging.FileHandler(log_file)
	file_hdlr.setLevel(logging.DEBUG)
	log.addHandler(file_hdlr)

	app.run()
