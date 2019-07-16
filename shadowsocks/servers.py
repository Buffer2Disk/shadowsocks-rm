#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 mengskysama
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import os
import logging
import thread
import config
import signal
import time

if config.LOG_ENABLE:
    logging.basicConfig(format='%(asctime)s %(filename)s[%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filename=config.LOG_FILE, level=config.LOG_LEVEL)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from shadowsocks import shell, daemon, eventloop, tcprelay, udprelay, \
    asyncdns, manager

import manager
import config
from dbtransfer import DbTransfer


def handler_SIGQUIT():
    return


def main():
    configer = {
        'server': '%s' % config.SS_BIND_IP,
        'local_port': 1081,
        'port_password': {
        },
        'method': '%s' % config.SS_METHOD,
        'manager_address': '%s:%s' % (config.MANAGE_BIND_IP, config.MANAGE_PORT),
        'timeout': 185,  # some protocol keepalive packet 3 min Eg bt
        'fast_open': False,
        'verbose': 1
    }
    try:
        m = manager.get_manager(configer)
        t = thread.start_new_thread(m.run, ())
        time.sleep(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logging.error('manger thread start except:%s' % e)

    # Refer ---> http://www.runoob.com/python/python-multithreading.html
    # create multi threads(number is n) to manage all ports in database user table separately(by wzq)
    # you can modify n to create more threads for better performance

    # whether run in MultiThread Mode
    if config.ManagePort_MultiThread:
        # start from 1
        i = 1
        # thread number
        n = config.ManagePort_ThreadNum
        db_loop_num = config.DbLoopNum
        while i <= n:
            try:
                # str() will convert int to string
                name = "thread-" + str(i) + "-"
                if i == n:
                    limit = "limit 100000 offset " + str((i - 1) * db_loop_num)
                else:
                    limit = "limit " + str(db_loop_num) + " offset " + str((i - 1) * db_loop_num)
                t = thread.start_new_thread(DbTransfer.thread_db_with_parm, (name, limit,))
                i = i + 1
                time.sleep(1)
            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.error('thread start except:%s' % e)
    else:
        t = thread.start_new_thread(DbTransfer.thread_db, ())
        time.sleep(1)

    thread.start_new_thread(DbTransfer.thread_check_not_exist_user, (m,))
    t = thread.start_new_thread(DbTransfer.thread_push, ())

    while True:
        time.sleep(100)


if __name__ == '__main__':
    main()
