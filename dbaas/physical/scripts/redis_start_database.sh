#!/bin/bash

startdatabase()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
    /etc/init.d/redis start
    die_if_error "Error starting database"
}

restart_http()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Restarting httpd"
    /etc/init.d/httpd stop > /dev/null
    die_if_error "Error stoping httpd"
    /etc/init.d/httpd start > /dev/null
    die_if_error "Error starting http"
}

startsentinel()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Starting sentinel"
    /etc/init.d/sentinel start
    die_if_error "Error starting sentinel"
}

{% if ONLY_SENTINEL %}
    startsentinel
{% else %}
    startdatabase
    {% if IS_HA  %}
        startsentinel
    {% endif %}
{% endif %}

restart_http

exit 0