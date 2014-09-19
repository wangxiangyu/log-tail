# -*- coding: utf-8 -*-
"""
@author: sunchenjiao@baidu.com
@date: Aug,2014
@summary: Main 函数
@version: 0.4.0
@copyright: Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
"""

import os
import datetime
import sched
import sys
import time
import json
from kafka.client import KafkaClient
from kafka.producer import SimpleProducer
from kazoo.client import KazooClient

from comlog import comlog
from pygtail_mv import PygtailMv
from pygtail_slice import PygtailSlice
from pygtail_mtime import PygtailMtime
from ub_conf import UbConfig 

class Main(object):
    def __init__(self):
        comlog.init_logger("./../log/vdata.log")
        self.ub_conf = UbConfig("./../conf/vmonitor_tail.conf")
        self._conf_info = self.ub_conf.get_conf_info()
        self._file_path = self._conf_info["[LOG_FILE_CONF]"]["file_path"]
        self._file_name = self._conf_info["[LOG_FILE_CONF]"]["file_name"]
        self._log_max_length = int(self._conf_info["[LOG_FILE_CONF]"]["log_max_length"])
        self._topic_name = self._conf_info["[KAFKA]"]["topic_name"]
        self._interval_time = self._conf_info["[TIME_INTERVAL]"]["interval"]
        self._match_str = self._conf_info["[LOG_FILE_CONF]"]["match_str"]
        self._log_type = self._conf_info["[LOG_TYPE]"]["type"]

        self.init_data_file()
        self.s = sched.scheduler(time.time, time.sleep)
        if self._conf_info["[KAFKA]"].has_key('broker_list'):
            self.broker_list=self._conf_info["[KAFKA]"]["broker_list"]
        elif self._conf_info["[KAFKA]"].has_key('zookeeper'):
            self.broker_list=','.join(self.get_broker_list(self._conf_info["[KAFKA]"]['zookeeper']))
        else:
            raise ValueError, " zookeeper and broker_list are both null in config file" 
        self.client = KafkaClient(self.broker_list)
        self.producer = SimpleProducer(self.client)

        #拼接json格式message，先动态生成的token，再固定的一些string，最后log
    #token前面部分
        self.token_pre = 'token='
    #tags
        self.tags = {}
        for key in self._conf_info["[JPAAS_ENV]"]:
            self.tags[key]=self._conf_info["[JPAAS_ENV]"][key]

    def init_data_file(self):
        if not os.path.isdir("./../data"):
            os.mkdir("./../data")

    def gen_message_final_str(self,message,token):
        message_final={}
        message_final["message"]=message
        message_final["token"]=token
        message_final["timestamp"]=time.time()
        message_final["tags"]=self.tags
        message_final_str=json.dumps(message_final)
        return message_final_str

    def event_func_mv(self):
        token = int(time.time()) * 10000
        if os.path.isfile(self._file_path + self._file_name):
            pygtail = PygtailMv(self._file_path, self._file_name, self._match_str, paranoid=True, copytruncate=True)
            for line in pygtail:
                message_final_str=self.gen_message_final_str(line, token)
                message_lenth = len(message_final_str)
                if message_lenth > self._log_max_length:
                    comlog.warning("The message is too long:" + str(message_lenth))
                    continue
                try:
                    self.producer.send_messages(self._topic_name, message_final_str)
                    token = token + 1
                except Exception,data:
                    comlog.fatal(str(Exception))
                    comlog.fatal(str(data))
                    sys.exit()

            # print 'resched:', time.time()


    def event_func_mtime(self):
        token = int(time.time()) * 10000
        pygtail = PygtailMtime("/home/work/vmonitor-tail/vdata/testdata", "test\.log.*", offset_file=None, paranoid=True, copytruncate=True)
        for line in pygtail:
            message_final_str=self.gen_message_final_str(line, token)
            message_lenth = len(message_final_str)
            if message_lenth > self._log_max_length:
                comlog.warning("The message is too long:" + str(message_lenth))
                continue
            try:
                self.producer.send_messages(self._topic_name, message_final_str)
                token = token + 1
            except Exception,data:
                comlog.fatal(str(Exception))
                comlog.fatal(str(data))
                sys.exit()

        # print 'resched:', time.time()



    def get_broker_list(self,zookeeper):
        try:
            zookeeper = KazooClient(zookeeper)
            zookeeper.start()
            broker_list=[]
            for id in zookeeper.get_children("/brokers/ids"):
                broker_info=json.loads(zookeeper.get("/brokers/ids/"+str(id))[0])
                host=broker_info["host"]
                port=broker_info["port"]
                broker_list.append(str(host)+':'+str(port))
            zookeeper.stop()
            return broker_list
        except Exception,data:
            comlog.fatal(str(Exception))
            comlog.fatal(str(data))
            sys.exit()

    def event_func_slice(self):
        token = int(time.time()) * 10000
        token_fol = ':' + self.unchanged_str[:-1] + ' - - - '
        pygtail = PygtailSlice(self._file_path, self._file_name, self._match_str, paranoid=True, copytruncate=True)
        for line in pygtail:
            message =  self.token_pre + str(token) + token_fol + line[:-1] 
            message_lenth = len(message)
            if message_lenth > self._log_max_length:
                comlog.warning("The message is too long:" + str(message_lenth))
                continue
            try:
                self.producer.send_messages(self._topic_name, message)
                # print self.token_pre + str(token) + token_fol + line[:-1]
                token = token + 1
            except Exception,data:
                comlog.fatal(str(Exception))
                comlog.fatal(str(data))
                sys.exit()

        print 'resched:', time.time()
    def perform(self,inc):
        self.s.enter(inc, 0, self.perform, (inc,))
        if self._log_type == "rotation_file_slice":
            self.event_func_slice()
        elif self._log_type == "rotation_file_mv":
            self.event_func_mv()
        elif self._log_type == "rotation_file_mtime":
            self.event_func_mtime()
        else:
            comlog.fatal("ERROR CONF: " + self._log_type)
            sys.exit()


    def start(self,inc=10):
        inc=int(self._interval_time)
        self.s.enter(0, 0, self.perform, (inc,))
        self.s.run()


if __name__ == "__main__":
    main = Main()
    main.start()
    
    

