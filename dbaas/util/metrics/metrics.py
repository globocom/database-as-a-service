# -*- coding: utf-8 -*-
import urllib3
import logging
import json
import ast

LOG = logging.getLogger(__name__)

URL = "http://graphite.dev.globoi.com/render?from=-{}{}&until=-5minutes&target=statsite.dbaas.{}.{}.{}.{}&format=json"

CPU = {"name": "cpu",
            "series":[
                            { "name": "idle" , "data": "cpu.cpu_idle"},
                            { "name": "wait" , "data": "cpu.cpu_wait"},
                            { "name": "user" , "data": "cpu.cpu_usr"},
                            { "name": "system" , "data": "cpu.cpu_sys"},

                     ],
           "type": "area",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br/>""",
           "y_axis_title": "percent",
           "stacking": 'percent',
           "graph_name": "CPU"
}

MEMORY = {"name": "mem",
                   "series":[
                                   { "name": "used" , "data": "men.men_used"},
                                   { "name": "free" , "data": "men.men_free"},
                                   #{ "name": "cach" , "data": "men.men_cach"},
                                   #{ "name": "buff" , "data": "men.men_buff"},
                   ],
           "type": "area",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br/>""",
           "y_axis_title": "percent",
           "stacking": 'percent',
           "graph_name": "Memory"
}

NETWORK = {"name": "net",
                   "series":[
                                   { "name": "send" , "data": "net.net_send"},
                                   { "name": "recv" , "data": "net.net_recv"},
                   ],
           "type": "line",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
           "y_axis_title": "",
           "stacking": 'normal',
           "graph_name": "Network"
}

DISK_IO = {"name": "io",
                   "series":[
                                   { "name": "read" , "data": "dsk.read"},
                                   { "name": "write" , "data": "dsk.write"},
                   ],
           "type": "line",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
           "y_axis_title": "",
           "stacking": 'normal',
           "graph_name": "Disk I/O"
}


LOAD = {"name": "load",
                   "series":[
                                   { "name": "1m" , "data": "load.1m"},
                                   { "name": "5m" , "data": "load.5m"},
                                   { "name": "15m" , "data": "load.15m"},
                   ],
           "type": "line",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
           "y_axis_title": "",
           "stacking": 'normal',
           "graph_name": "Load"
}

SWAP = {"name": "swap",
                   "series":[
                                   { "name": "used" , "data": "swap.used"},
                                   { "name": "free" , "data": "swap.free"},
                   ],
           "type": "area",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br/>""",
           "y_axis_title": "percent",
           "stacking": 'percent',
           "graph_name": "Swap"
}

DISK = {"name": "disk",
                   "series":[
                                   { "name": "used" , "data": "df.used"},
                                   { "name": "available" , "data": "df.available"},
                   ],
           "type": "area",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br/>""",
           "y_axis_title": "percent",
           "stacking": 'percent',
           "graph_name": "Disk Usage"
}


MONGO_CON = {"name": "mongo_connections",
                   "series":[
                                   { "name": "connections" , "data": "momgodb.connections.current"},
                   ],
           "type": "line",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
           "y_axis_title": "Connections",
           "stacking": 'normal',
           "graph_name": "MongoDB Connections"
}


MONGO_OP = {"name": "mongo_opcounters",
                   "series":[
                                   { "name": "Insert" , "data": "momgodb.opcounters.insert"},
                                   { "name": "Query" , "data": "momgodb.opcounters.query"},
                                   { "name": "Update" , "data": "momgodb.opcounters.update"},
                                   { "name": "Delete" , "data": "momgodb.opcounters.delete"},
                                   { "name": "Getmore" , "data": "momgodb.opcounters.getmore"},
                                   { "name": "Command" , "data": "momgodb.opcounters.command"},
                   ],
           "type": "line",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
           "y_axis_title": "Operations",
           "stacking": 'normal',
           "graph_name": "MongoDB Operations"
}


VM_METRICS = (
             CPU,
              MEMORY,
              NETWORK,
              DISK,
              DISK_IO,
              LOAD,
              SWAP,
              )

MONGODB_METRICS = VM_METRICS + (
          MONGO_CON,
  )

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
        data = format_datapoints(data['datapoints'])
        if not data:
          data = []
        return data
    except KeyError, e:
        LOG.warn("No datapoints received... {}".format(e))
        return None

def get_metric_datapoints_for(engine, db_name, hostname, url):
        datapoints = {}

        if engine=="mongodb":
            graphs = MONGODB_METRICS
        elif engine=="mysql":
            graphs = MYSQL_METRICS
        else:
            graphs = None

        newgraph = []
        for graph in graphs:
          newserie = []
          for serie in graph['series']:

            datapoints = get_graphite_metrics_datapoints('60', "minutes", engine, db_name, hostname, serie['data'], url=url)

            newserie.append({
              'name': serie['name'],
              'data': datapoints
              })

          newgraph.append(
                                        { "name": graph["name"],
                                          "series":str(ast.literal_eval(json.dumps(newserie))),
                                          "type": graph["type"],
                                          "tooltip_point_format": graph["tooltip_point_format"],
                                          "y_axis_title": graph["y_axis_title"],
                                          "stacking": graph["stacking"],
                                          "graph_name": graph["graph_name"],
                                        }
                                    )



        return newgraph
