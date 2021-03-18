#!/bin/bash

startdatabase()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
    {{ DATABASE_START_COMMAND }}
    die_if_error "Error starting database"
}

restart_http()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Restarting httpd"
    {{ HTTPD_STOP_COMMAND_NO_OUTPUT }}
    die_if_error "Error stoping httpd"
    {{ HTTPD_START_COMMAND_NO_OUTPUT }}
    die_if_error "Error starting http"
}

startsentinel()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Starting sentinel"
    {{ SECONDARY_SERVICE_START_COMMAND }}
    die_if_error "Error starting sentinel"
}

{% if ONLY_SENTINEL %}
    startsentinel
{% else %}
    startdatabase

    {% if 'redis_sentinel' in DRIVER_NAME %}
        startsentinel
    {% endif %}
{% endif %}

restart_http

exit 0
