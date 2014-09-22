# -*- coding: utf-8 -*-
"""
@author: sunchenjiao@baidu.com
@date: Aug,2014
@summary: UbConfig ½âÎöub conf
@version: 1.0
@copyright: Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
"""
import os
from comlog import comlog
class UbConfig(object):

    def __init__(self,config_file):
        self.bin_diff_config = config_file
        self.conf_dict = {}
        self.conf_info = {}
        self.load()

    def load(self): 
        if self.file2dict() == -1:
            return
        if self.format_check() == -1:
            return
        self.parser_conf()

    def get_conf_info(self):
        return self.conf_info

    def parser_conf(self):
        cur_level1_key = -1
        cur_level2_key = -1
        cur_level3_key = -1
        cur_level1_value = ''
        cur_level2_value = ''
        cur_level3_value = ''

        for (key,value) in self.conf_dict.items():
            if value.find('[') == 0 and value.find('.') != 1 and value.find(']') != -1:
                cur_level1_key = key
                cur_level1_value = value
                self.conf_info[cur_level1_value] = {}

            if value.find('[.') == 0 and value.find('[..') != 0 and value.find(']') != -1:
                cur_level2_key = key
                cur_level2_value = value
                self.conf_info[cur_level1_value][cur_level2_value]={}

            if value.find('[..') == 0 and value.find('[...') != 0 and value.find(']') != -1:
                cur_level3_key = key
                cur_level3_value = value
                self.conf_info[cur_level1_value][cur_level2_value][cur_level3_value]={}

            if value.find('[') <> 0:
                s = value.split(":")
                key_item = ''
                value_item = ''
                if len(s) >= 2:
                    key_item = s[0]
                    value_item = s[1]
                    for inx in range(2, len(s)):
                        value_item +=":"+s[inx]
                cur_par_line = max(cur_level1_key,cur_level2_key,cur_level3_key)
                if cur_par_line == cur_level1_key:
                    self.conf_info[cur_level1_value][key_item] = value_item
                if cur_par_line == cur_level2_key:
                    self.conf_info[cur_level1_value][cur_level2_value][key_item] = value_item
                if cur_par_line == cur_level3_key:
                    self.conf_info[cur_level1_value][cur_level2_value][cur_level3_value][key_item] = value_item

    def file2dict(self):
        if not os.path.isfile(self.bin_diff_config):
            comlog.fatal(self.bin_diff_config+" is not exist!")
            return -1
        conf_file = file(self.bin_diff_config)
        line = conf_file.readline()
        line_num = 0
        while line:
            line = self.f_line(line)
            if len(line) <= 0 or line[0] == '#':
                line = conf_file.readline()
            else:
                self.conf_dict[line_num] = line
                line = conf_file.readline()
                line_num += 1
        return 0

    def f_line(self, line):
        line = line.replace('\t', '')
        line = line.replace('\n', '')
        line = line.replace(' ', '')
        return line

    def format_check(self):
        if self.conf_dict == {}:
            comlog.fatal("Failed to load " + self.bin_diff_config)
            return -1
        if (self.conf_dict[0].find('[') != 0 or self.conf_dict[0].find('.') == 1 or self.conf_dict[0].find(']') == -1):
            comlog.fatal("Wrong conf format: " + self.conf_dict[0])
            return -1
        base_level = 0
        for i in range(0,len(self.conf_dict.keys())):
            if self.conf_dict[i].find('[') == 0: 
                num = self.conf_dict[i].count('.')
                if (num == 0 and base_level in [0,1,2]) or \
                   (num == 1 and base_level in [0,1,2]) or \
                   (num == 2 and base_level in [1,2]):
                    base_level = num
                    pass
                else:
                    comlog.fatal("Wrong conf format: " + self.conf_dict[i])
                    return -1
        return 0
if __name__ == "__main__":
    ub_conf = UbConfig("./../conf/log_tail.conf")
    print ub_conf.conf_info

