# -*- coding: utf-8 -*-
import logging

LOG = logging.getLogger(__name__)


def test_bash_script_error():
    return """
      #!/bin/bash

      die_if_error()
      {
            local err=$?
            if [ "$err" != "0" ];
            then
                echo "$*"
                exit $err
            fi
      }"""


def monit_script(option='start'):
    return """
        echo ""; echo $(date "+%Y-%m-%d %T") "- Monit"
        /etc/init.d/monit {}
        """.format(option)
