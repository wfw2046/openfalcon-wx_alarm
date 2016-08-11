#!/usr/bin/env python
# coding:utf-8
import sys
import urllib2
import time
import os
import json
import requests
import MySQLdb
reload(sys)
sys.setdefaultencoding('utf-8')



class Token(object):
	# 获取token
	def __init__(self, corpid, corpsecret):
		self.baseurl = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={0}&corpsecret={1}'.format(
			corpid, corpsecret)
		self.expire_time = sys.maxint
	def get_token(self):
		if self.expire_time > time.time():
			request = urllib2.Request(self.baseurl)
			response = urllib2.urlopen(request)
			ret = response.read().strip()
			ret = json.loads(ret)
			if 'errcode' in ret.keys():
				print >> ret['errmsg'], sys.stderr
				sys.exit(1)
			self.expire_time = time.time() + ret['expires_in']
			self.access_token = ret['access_token']
		return self.access_token

def send_msg(content):
	# 发送消息
	num = 1
	con = ""
	title = "System Monitor Alarm"
	corpid = ""  # 填写自己应用的id
	corpsecret = "" # 填写自己应用的认证码
	qs_token = Token(corpid=corpid, corpsecret=corpsecret).get_token()
	url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={0}".format(
		qs_token)
	for i,key in content.items():
		for j in key:
			con = con + str(num) + ":" + j + "\r\n"
			num += 1
		num = 1
		#part = "\"" + str(i) + "\""
		payload = {
			"toparty": str(i),
			"msgtype": "text",
			"agentid": "1",
			"text": {
						"content": "Title:{0}\n 内容:\n{1}".format(title, con)
			},
			"safe": "0"
		}
		con = ""
	#ret = requests.post(url, data=json.dumps(payload, ensure_ascii=False))
		data=json.dumps(payload, ensure_ascii=False)
		print data
		con = ""
		ret = requests.post(url, data)
		print ret.json()
def get_alarm():
	r = json.loads(os.popen("curl http://127.0.0.1:9912/alarm -s").read())
	#print r.items()
	if ( r > 0 ):
		n = 0
		dic = dict()
		#dic2 = dict()
		li = []
		for i,key in r.items():
			title = key["endpoint"] + "[" +  key["status"] + "]" + "[" + str(key["priority"]) + "]" + key["note"]
			#dic["templateId"] = key["templateId"]
			#dic["content"] = title
			li.append({"templateId":key["templateId"],"content":title})
		#print li
		#print li
		dic = {}
		for i in  sorted(li,key = lambda x:x["templateId"]):
			if n != i["templateId"]:
				m = []
			m.append(i["content"])
			dic[i["templateId"]] = m
			n = i["templateId"]
		return dic	
	else:
		return 0
def pre_mess():
	ll = []
	n = 0
	db = MySQLdb.connect("databaseurl","username","userpassword","falcon_portal" )
	cursor = db.cursor()
	try:
	# 执行SQL语句
		for i,key in get_alarm().items():
			sql = "SELECT w.teamid_wx from wx_dep as w WHERE  find_in_set(w.t_name,(SELECT a.uic  FROM action as a where a.id=(SELECT t.action_id FROM tpl as t WHERE t.id=%d)))" % (i)
			cursor.execute(sql)
	# 获取所有记录列表
			results = cursor.fetchall()
			for row in results:
				wid = int(row[0])
				ll.append({"depid":wid,"content":key})
			dic = {}
		for j in  sorted(ll,key = lambda x:x["depid"]):
			if n != j["depid"]:
				m = []
			m.extend(j["content"])
			dic[j["depid"]] = m
			n = j["depid"]
		return  dic
	except:
		return 0
	db.close()

if __name__ == '__main__':
	pm = pre_mess()
	if pm != 0:
		send_msg(pm)
