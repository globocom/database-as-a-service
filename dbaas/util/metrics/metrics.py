import urllib3
import json
import logging
import re

LOG = logging.getLogger(__name__)

URL = "http://graphite.dev.globoi.com/render?from=-{}{}&until=now&target=statsite.dbaas.{}.{}.{}.{}&format=json"

VM_METRICS = ("cpu.cpu_idle",
                         "cpu.cpu_wait",
                         "cpu.cpu_usr",
                         "cpu.cpu_sys",
                         )

MONGODB_METRICS = () +VM_METRICS

MYSQL_METRICS = () + VM_METRICS


def make_request(url):
    LOG.info("Requesting {}".format(url))
    http = urllib3.PoolManager()
    response = http.request(method="GET", url=url)
    return response


def format_url(*args, **kwargs):
    LOG.debug("Formating url. ARGS: {} | KWARGS: {}".format(str(args), kwargs))
    return kwargs['url'].format(*args)

def format_datapoints(datapoints):
    return [ [dp[1]*1000,dp[0]] for dp in datapoints if dp[0] is not None]

def get_graphite_metrics_datapoints(*args, **kwargs):
    url = format_url(*args, **kwargs)

    response = make_request(url)

    try:
        data = json.loads(response.data)
        data = data[0]
    except IndexError, e:
        LOG.warn("No data received... {}".format(e))
        return None

    try:
        return format_datapoints(data['datapoints'])
    except KeyError, e:
        LOG.warn("No datapoints received... {}".format(e))
        return None

def get_metric_datapoints_for(engine, db_name, hostname, url):
        datapoints = {}

        if engine=="mongodb":
            metrics = MONGODB_METRICS
        elif engine=="mysql":
            metrics = MYSQL_METRICS
        else:
            metrics = None

        for metric in metrics:
            datapoint = get_graphite_metrics_datapoints('120', "minutes", engine, db_name, hostname, metric, url=url)
            datapoints[metric] = datapoint

        return datapoints
