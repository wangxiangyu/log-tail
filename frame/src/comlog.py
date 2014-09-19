# -*- coding: utf-8 -*-
'''
Created on May 8, 2012

@author: caiyifeng<caiyifeng@baidu.com>

@modified by: sunchenjiao <sunchenjiao@baidu.com>
@summary: ͳһ��־����,copy��xts log

@note:
 - debug: ������Ϣ
 - info: ����ִ�йؼ��ڵ����Ϣ
 - warning: �����д����Իָ������
 - fatal: ��������жϣ����򺬶������

 - info���ϵ���־�����ǹ����ģ���������������Ϣ��ȡ��ͳ��
 - ��Ļ��� info���ϼ������־
 - ��־�ļ���� ���м������־
 - wf��־�ļ����warning���ϼ������־

@note:
 - �޸���־����Ϊdebug��info��warning��fatal����
'''

import os
import sys
import traceback
import logging
import inspect


# ========= ��ʼ��logging ==========
SUCCESS = 25    # ����INFO, С��WARNING
FATAL = 40
def init_logging():
    # ����һ��SUCCESS�㼶
    logging.addLevelName(SUCCESS, "SUCCESS")

    # ����һ��FATAL�㼶
    logging.addLevelName(FATAL, "FATAL")

# ����ȫ�ֳ�ʼ������
init_logging()
# ========= ��end����ʼ��logging ==========


# ========= ȫ�ֺ��� =========
def update_nest_level(kwargs):
    '''@summary: ����kwargs�е�nest_level��������ھ�+1����������ھ���Ϊ1'''
    if "nest_level" in kwargs:
        kwargs["nest_level"] += 1
    else:
        kwargs["nest_level"] = 1
# ========= (end)ȫ�ֺ��� =========


class _comlog(object):
    def __init__(self, logger_name="comlog", tag_name=""):
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self.tag_name = tag_name

        # ������Ա
        self.sh = None
        self.fmt_sh = None
        self.logpath = None

        # �����ܵ�logger level
        self.logger.setLevel(logging.DEBUG)

    def set_tag_name(self, tag_name):
        self.tag_name = tag_name

    # -------- ��Ļ��־���� --------
    def init_stream_handler(self):
        # �ж��Ƿ��ظ�init
        for h in self.logger.handlers:
            if isinstance(h, logging.StreamHandler):
                self.warning("Logger %s already has stream handler, ignore this one", self.logger_name)
                return


        # ��Ļ���info�������ϵ���־
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(logging.INFO)

        # ��Ļ�����־��ʽ
        self.fmt_sh = logging.Formatter("[\033[1;%(colorcode)sm%(levelname)-8s\033[0m %(asctime)s] [%(tagname)s] [%(myfn)s:%(mylno)d:%(myfunc)s] %(message)s", "%m-%d %H:%M:%S")
        sh.setFormatter(self.fmt_sh)

        # ��handler����logger
        self.logger.addHandler(sh)

        # ������Ļ����ľ�����������Ը���
        self.sh = sh

    def set_no_color(self):
        '''@summary: ������Ļ���������ɫ����־'''
        self.fmt_sh = logging.Formatter("[%(levelname)-8s %(asctime)s] [%(tagname)s] [%(myfn)s:%(mylno)d:%(myfunc)s] %(message)s", "%m-%d %H:%M:%S")
        self.sh.setFormatter(self.fmt_sh)

    def set_sh_debug(self):
        '''@summary: ��Ļ���debug��־'''
        self.sh.setLevel(logging.DEBUG)
    # -------- ��end����Ļ��־���� --------

    def set_sh_warning(self):
        '''@summary: ��Ļ���warningfatal��־'''
        self.sh.setLevel(logging.WARNING)

    def set_sh_info(self):
        '''@summary: ��Ļ���info��־'''
        self.sh.setLevel(logging.INFO)

    # -------- ��end����Ļ��־���� --------
    # -------- �ļ���־���� --------
    def init_logger(self, logpath, mode="a", force=False):
        '''@summary: ��ʼ���ļ���־������
        @param mode: 'w' for overwrite, 'a' for append
        @param force: ΪFalseʱ�Ե�һ��Ϊ׼�����Ժ���init��ΪTrueʱ�����һ��Ϊ׼������֮ǰ��init'''
        # �ж��Ƿ��ظ�init
        fhs = [fh for fh in self.logger.handlers if isinstance(fh, logging.FileHandler)]
        if fhs:
            # �Ѿ���file handler��
            if force:
                # ǿ�Ƹ���
                map(self.logger.removeHandler, fhs)
            else:
                # �Ե�һ��Ϊ׼
                self.warning("Logger %s already has file handler\nIgnore this one: %s\nReserve old one: %s", self.logger_name, logpath, self.logpath)
                return


        # ������־Ŀ¼
        logdir = os.path.dirname(logpath)
        if logdir:
            cmd = "mkdir -p " + logdir

        # ��־�ļ�������м������־
        fh = logging.FileHandler(logpath, mode)
        fh.setLevel(logging.DEBUG)

        # �ļ������־��ʽ
        fmt_fh = logging.Formatter("[%(levelname)-8s %(asctime)s] [%(tagname)s] [%(myfn)s:%(mylno)d:%(myfunc)s] %(message)s", "%m-%d %H:%M:%S")
        fh.setFormatter(fmt_fh)

        # ��handler����logger
        self.logger.addHandler(fh)

        # wf��־�ļ����warning�������ϵ���־
        fh_wf = logging.FileHandler(logpath+".wf", mode)
        fh_wf.setLevel(logging.WARNING)

        # �ļ������־��ʽ
        fmt_fh_wf = logging.Formatter("[%(levelname)-8s %(asctime)s] [%(tagname)s] [%(myfn)s:%(mylno)d:%(myfunc)s] %(message)s", "%m-%d %H:%M:%S")
        fh_wf.setFormatter(fmt_fh_wf)

        # ��handler����logger
        self.logger.addHandler(fh_wf)

        # ����logpath������unpickle
        self.logpath = logpath
    # -------- (end)�ļ���־���� --------

    # -------- ��־��ӡ���� --------
    def debug(self, msg, *args, **kwargs):
        self.__update_caller(kwargs)
        msg = self._handle_msg(msg, args, kwargs)
        self._update_kwargs(kwargs, "0")    # ��ɫ
        self.logger.debug(msg, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.__update_caller(kwargs)
        msg = self._handle_msg(msg, args, kwargs)
        self._update_kwargs(kwargs, "36")   # ǳ��ɫ
        self.logger.info(msg, **kwargs)


    def warning(self, msg, *args, **kwargs):
        self.__update_caller(kwargs)
        msg = self._handle_msg(msg, args, kwargs)
        self._update_kwargs(kwargs, "33")   # ��ɫ
        self.logger.warning(msg, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        self.__update_caller(kwargs)
        msg = self._handle_msg(msg, args, kwargs)
        self._update_kwargs(kwargs, "31")   # ��ɫ
        self.logger.error(msg, **kwargs)
    # -------- ��end����־���� --------

    # -------- find caller --------
    def __update_caller(self, kwargs):
        '''@summary: ����kwargs�е�caller��Ϣ
        @attention:
         - ����ֱ�ӱ�debug�Ⱥ�������
         - ���ܱ������д'''
        # ����nest_level
        if "nest_level" in kwargs:
            nest = kwargs["nest_level"]
            del kwargs["nest_level"]
        else:
            nest = 0    # Ĭ��Ϊ0

        # ��ȡ��ȷ��ջ��Ϣ
        try:
            frame = inspect.stack()[2+nest]     # Ĭ��������2�㣺__update_caller <- log functions <- log invoker
            _, fn, lno, func, _, _ = frame
            fn = os.path.basename(fn)
        except Exception:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"

        # ����extra�ֵ�
        if not "extra" in kwargs:
            # kwargs��û��extra�ֵ䣬������
            kwargs["extra"] = {}

        kwargs["extra"]["myfn"] = fn
        kwargs["extra"]["mylno"] = lno
        kwargs["extra"]["myfunc"] = func
    # -------- (end)find caller --------

    # -------- msg�������� --------
    def _handle_msg(self, msg, args, kwargs):
        if args:
            msg = msg % args
        msg = self.__encgb_excinfo(msg, kwargs)

        msg = self.__indent_msg(msg.rstrip(), args)
        return msg

    def __encgb_excinfo(self, msg, kwargs):
        '''@summary: ��kwargs�е�exc_info��ת��Ϊgb18030��merge��msg��
        @attention: exc_infoΪtraceback��Ԫ��ʱ��������ת��'''
        if not "exc_info" in kwargs or not kwargs["exc_info"] or isinstance(kwargs["exc_info"], tuple):
            # kwargs������exc_info
            # ���� exc_infoΪFalse
            # ���� exc_infoΪtuple
            return msg

        # exc_infoΪTrue
        del kwargs["exc_info"]

        s = traceback.format_exc()
        msg = msg + "\n"# + safegb(s)
        return msg

    def __indent_msg(self, msg, args):
        '''@summary: ��msg�ӵ�2�п�ʼindent'''
        msg_lines = msg.splitlines(True)
        if not msg_lines:
            msg_lines = [""]

        msg_indent_lines = []
        msg_indent_lines.append(msg_lines[0])
        msg_indent_lines.extend(["  - " + line for line in msg_lines[1:]] )

        return "".join(msg_indent_lines)
    # -------- (end)msg�������� --------

    # -------- kwargs�������� --------
    def _update_kwargs(self, kwargs, colorcode):
        # ����extra�ֵ�
        kwargs["extra"]["colorcode"] = colorcode

        # ����extra�ֵ��е�tagname
        if "tag_name" in kwargs:
            tagname = kwargs["tag_name"]
            del kwargs["tag_name"]
        else:
            tagname = self.tag_name
        kwargs["extra"]["tagname"] = tagname

        # ����Ƿ���ֵ
        self.__clean_kwargs(kwargs)

    def __clean_kwargs(self, kwargs):
        '''@summary: ���kwargs�еķǷ���ֵ'''
        for key in kwargs.keys():
            if key not in ("exc_info", "extra"):
                del kwargs[key]
    # -------- (end)kwargs�������� --------


class LogProxy(object):
    '''@summary: logger�����࣬ȫ��Ψһ'''
    def __init__(self, inst):
        self.set_instance(inst)

    def set_instance(self, inst):
        self.inst = inst

    def __getattr__(self, name):
        '''@summary: �������ڵĳ�Ա���ʣ�ί�и�self.inst'''
        return getattr(self.inst, name)


# comlog ȫ�־����Ĭ��������Ļ���
comlog = LogProxy(_comlog())
comlog.init_stream_handler()


def _test():
    comlog.init_logger("./../log/test.log")

    comlog.debug("debug ��־")
    comlog.info("info %s ��־\n����")
    try:
        raise Exception, "except �쳣"     # this is a �쳣ע�� !
    except Exception:
        comlog.warning("warning %s", "��־", exc_info=True)
    comlog.fatal("fatal %s��־", "��ʽ�ַ���")

if __name__ == "__main__":
    _test()
