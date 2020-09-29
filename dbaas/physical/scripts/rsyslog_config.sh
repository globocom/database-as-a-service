#!/bin/bash


echo "\$EscapeControlCharactersOnReceive off" > /etc/rsyslog.d/dbaaslog.conf
sed -i "\$a \$template db-log, \"<%PRI%>%TIMESTAMP% %HOSTNAME% %syslogtag%%msg%	tags: DBAAS,{{ENGINE|upper}},{{DATABASENAME}}\"" /etc/rsyslog.d/dbaaslog.conf
sed -i "\$a*.*                    @{{ LOG_ENDPOINT }}; db-log" /etc/rsyslog.d/dbaaslog.conf
/etc/init.d/rsyslog restart