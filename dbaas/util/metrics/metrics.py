# -*- coding: utf-8 -*-
import urllib3
import logging
import json
import ast

LOG = logging.getLogger(__name__)

CPU = {"name": "cpu",
       "series": [
           {"name": "idle", "data": "cpu.cpu_idle"},
           {"name": "wait", "data": "cpu.cpu_wait"},
           {"name": "user", "data": "cpu.cpu_usr"},
           {"name": "system", "data": "cpu.cpu_sys"},

       ],
       "type": "area",
       "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br/>""",
       "y_axis_title": "percent",
       "stacking": 'percent',
       "graph_name": "CPU",
       "normalize_series": False
       }

MEMORY = {"name": "mem",
          "series": [
              {"name": "free", "data": "men.men_free"},
              {"name": "used", "data": "men.men_used"},
          ],
          "type": "area",
          "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br/>""",
          "y_axis_title": "percent",
          "stacking": 'percent',
          "graph_name": "Memory",
          "normalize_series": False
          }

NETWORK = {"name": "net",
                   "series": [
                       {"name": "send", "data": "net.net_send"},
                       {"name": "recv", "data": "net.net_recv"},
                   ],
           "type": "line",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
           "y_axis_title": "",
           "stacking": '',
           "graph_name": "Network",
           "normalize_series": False
           }

DISK_IO = {"name": "io",
                   "series": [
                       {"name": "read", "data": "dsk.read"},
                       {"name": "write", "data": "dsk.write"},
                   ],
           "type": "line",
           "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
           "y_axis_title": "",
           "stacking": '',
           "graph_name": "Disk I/O",
           "normalize_series": False
           }


LOAD = {"name": "load",
        "series": [
            {"name": "1m", "data": "load.1m"},
            {"name": "5m", "data": "load.5m"},
            {"name": "15m", "data": "load.15m"},
        ],
        "type": "line",
        "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
        "y_axis_title": "",
        "stacking": '',
        "graph_name": "Load",
        "normalize_series": False
        }

SWAP = {"name": "swap",
        "series": [
            {"name": "free", "data": "swap.free"},
            {"name": "used", "data": "swap.used"},
        ],
        "type": "area",
        "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br/>""",
        "y_axis_title": "percent",
        "stacking": 'percent',
        "graph_name": "Swap",
        "normalize_series": False
        }

DISK = {"name": "disk",
        "series": [
            {"name": "available", "data": "df.available"},
            {"name": "used", "data": "df.used"},
        ],
        "type": "area",
        "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> <br/>""",
        "y_axis_title": "percent",
        "stacking": 'percent',
        "graph_name": "Disk Usage",
        "normalize_series": False
        }


MONGO_CON = {"name": "mongo_connections",
             "series": [
                 {"name": "connections",
                     "data": "momgodb.connections.current"},
             ],
             "type": "line",
             "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
             "y_axis_title": "Connections",
             "stacking": '',
             "graph_name": "MongoDB Connections",
             "normalize_series": False
             }


MONGO_OP = {"name": "mongo_opcounters",
            "series": [
                {"name": "Command", "data": "momgodb.opcounters.command"},
                {"name": "Insert", "data": "momgodb.opcounters.insert"},
                {"name": "Query", "data": "momgodb.opcounters.query"},
                {"name": "Update", "data": "momgodb.opcounters.update"},
                {"name": "Delete", "data": "momgodb.opcounters.delete"},
                {"name": "Getmore", "data": "momgodb.opcounters.getmore"},
            ],
            "type": "line",
            "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
            "y_axis_title": "Operations",
            "stacking": '',
            "graph_name": "MongoDB Operations",
            "normalize_series": True
            }


MONGO_PF = {"name": "mongo_page_faults",
            "series": [
                {"name": "Page Faults",
                    "data": "momgodb.extra_info.page_faults"}
            ],
            "type": "line",
            "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
            "y_axis_title": "Total",
            "stacking": '',
            "graph_name": "MongoDB Page Faults",
            "normalize_series": True
            }

MONGO_IDX = {"name": "mongo_index_counters",
             "series": [
                 {"name": "Accesses",
                     "data": "momgodb.indexCounters.accesses"},
                 {"name": "Hits", "data": "momgodb.indexCounters.hits"},
                 {"name": "Misses", "data": "momgodb.indexCounters.misses"},
                 {"name": "Resets", "data": "momgodb.indexCounters.resets"},
                 {"name": "Miss Ratio",
                     "data": "momgodb.indexCounters.missRatio"},
             ],
             "type": "line",
             "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
             "y_axis_title": "Total",
             "stacking": '',
             "graph_name": "MongoDB Index Counters",
             "normalize_series": True
             }

MONGO_LOCK_CURR = {"name": "mongo_current_lock",
                   "series": [
                       {"name": "Total",
                           "data": "momgodb.globalLock.currentQueue.total"},
                       {"name": "Readers",
                           "data": "momgodb.globalLock.currentQueue.readers"},
                       {"name": "Writers",
                           "data": "momgodb.globalLock.currentQueue.writers"},
                   ],
                   "type": "line",
                   "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
                   "y_axis_title": "Total",
                   "stacking": '',
                   "graph_name": "MongoDB Current Lock",
                   "normalize_series": False
                   }

MONGO_LOCK_ACT = {"name": "mongo_active_lock",
                  "series": [
                      {"name": "Total",
                          "data": "momgodb.globalLock.activeClients.total"},
                      {"name": "Readers",
                          "data": "momgodb.globalLock.activeClients.readers"},
                      {"name": "Writers",
                          "data": "momgodb.globalLock.activeClients.writers"},
                  ],
                  "type": "line",
                  "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
                  "y_axis_title": "Total",
                  "stacking": '',
                  "graph_name": "MongoDB Active Sessions Lock",
                  "normalize_series": False
                  }

MONGO_NET_BYTES = {"name": "mongo_net_bytes",
                   "series": [
                       {"name": "in", "data": "momgodb.network.bytesIn"},
                       {"name": "out", "data": "momgodb.network.bytesOut"},
                   ],
                   "type": "line",
                   "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
                   "y_axis_title": "Bytes",
                   "stacking": '',
                   "graph_name": "MongoDB Network In/Out",
                   "normalize_series": True
                   }

MONGO_NET_REQUEST = {"name": "mongo_net_req",
                     "series": [
                         {"name": "requests",
                             "data": "momgodb.network.numRequests"},
                     ],
                     "type": "line",
                     "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
                     "y_axis_title": "Requests",
                     "stacking": '',
                     "graph_name": "MongoDB Network Requests",
                     "normalize_series": True
                     }


MYSQL_OP = {"name": "mysql_opcounters",
            "series": [
                {"name": "select", "data": "mysql.status.com_select"},
                {"name": "insert", "data": "mysql.status.com_insert"},
                {"name": "update", "data": "mysql.status.com_update"},
                {"name": "delete", "data": "mysql.status.com_delete"},
                {"name": "insert/select",
                    "data": "mysql.status.com_insert_select"},
            ],
            "type": "line",
            "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
            "y_axis_title": "Operations",
            "stacking": '',
            "graph_name": "MySQL Operations",
            "normalize_series": True
            }

MYSQL_NET_BYTES = {"name": "mysql_net_bytes",
                   "series": [
                       {"name": "in", "data": "mysql.status.bytes_received"},
                       {"name": "out", "data": "mysql.status.bytes_sent"},
                   ],
                   "type": "line",
                   "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
                   "y_axis_title": "Bytes",
                   "stacking": '',
                   "graph_name": "MySQL Network In/Out",
                   "normalize_series": True
                   }

MYSQL_CON = {"name": "mysql_connections",
                     "series": [
                         {"name": "total",
                             "data": "mysql.status.threads_connected"},
                         {"name": "active",
                             "data": "mysql.status.threads_running"},
                     ],
             "type": "line",
             "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
             "y_axis_title": "Connections",
             "stacking": '',
             "graph_name": "MySQL Connections",
             "normalize_series": False
             }

MYSQL_QUERY_CACHE = {"name": "mysql_query_cache",
                     "series": [
                         {"name": "queries in cache",
                             "data": "mysql.status.qcache_queries_in_cache"},
                         {"name": "inserts",
                             "data": "mysql.status.qcache_inserts"},
                         {"name": "hits", "data": "mysql.status.qcache_hits"},
                         {"name": "noncached queries",
                             "data": "mysql.status.qcache_not_cached"},
                     ],
                     "type": "line",
                     "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
                     "y_axis_title": "Count",
                     "stacking": '',
                     "graph_name": "MySQL Query Cache",
                     "normalize_series": True
                     }

MYSQL_QUERY_CACHE_MEM = {"name": "mysql_query_cache_mem",
                         "series": [
                             {"name": "free",
                                 "data": "mysql.status.qcache_free_memory"},
                             {"name": "total",
                                 "data": "mysql.variables.query_cache_size"},
                         ],
                         "type": "area",
                         "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
                         "y_axis_title": "Count",
                         "stacking": '',
                         "graph_name": "MySQL Query Cache Memory",
                         "normalize_series": False
                         }

REDIS_MEMORY = {"name": "redis_mem",
                "series": [
                    {"name": "used memory", "data": "redis.used_memory"},
                ],
                "type": "area",
                "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
                "y_axis_title": "Count",
                "stacking": '',
                "graph_name": "Redis Used Memory",
                "normalize_series": False
                }

REDIS_CON = {"name": "redis_connections",
             "series": [
                 {"name": "clients", "data": "redis.connected_clients"},
             ],
             "type": "line",
             "tooltip_point_format": """ <span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> <br/>""",
             "y_axis_title": "Connections",
             "stacking": '',
             "graph_name": "Redis Connections",
             "normalize_series": False
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
    MONGO_OP,
    MONGO_PF,
    MONGO_IDX,
    MONGO_LOCK_CURR,
    MONGO_LOCK_ACT,
    MONGO_NET_BYTES,
    MONGO_NET_REQUEST,
)

MYSQL_METRICS = VM_METRICS + (
    MYSQL_OP,
    MYSQL_NET_BYTES,
    MYSQL_CON,
    MYSQL_QUERY_CACHE,
    MYSQL_QUERY_CACHE_MEM,
)

REDIS_METRICS = VM_METRICS + (
    REDIS_MEMORY,
    REDIS_CON,
)


def make_request(url):
    LOG.info("Requesting {}".format(url))
    http = urllib3.PoolManager()
    response = http.request(method="GET", url=url)
    return response


def format_url(*args, **kwargs):
    LOG.debug("Formating url. ARGS: {} | KWARGS: {}".format(str(args), kwargs))
    return kwargs['url'].format(*args)


def format_datapoints(datapoints, normalize_series):
    if normalize_series:
        dp_list = [[dp[1] * 1000, 0] if index == 0 else [dp[1] * 1000,
                                                         dp[0] - datapoints[index - 1][0]] for index,
                   dp in enumerate(datapoints) if dp[0] is not None and datapoints[index - 1][0] is not None]
    else:
        dp_list = [[dp[1] * 1000, dp[0]]
                   for dp in datapoints if dp[0] is not None]
    return dp_list


def get_graphite_metrics_datapoints(*args, **kwargs):
    url = format_url(*args, **kwargs)

    response = make_request(url)

    try:
        LOG.debug('URL: {}'.format(url))
        data = json.loads(response.data)
        data = data[0]
        data = format_datapoints(
            data['datapoints'], kwargs['normalize_series'])
        if not data:
            data = []
        return data
    except Exception as e:
        LOG.warn("No data received... {}".format(e))
        return None


def get_metric_datapoints_for(engine, db_name, hostname, url, metric_name=None,
                              granurality=None, from_option=None):
    datapoints = {}

    if engine == "mongodb":
        graphs = MONGODB_METRICS
    elif engine == "mysql":
        graphs = MYSQL_METRICS
    elif engine == "redis":
        graphs = REDIS_METRICS
    else:
        graphs = None

    newgraph = []
    for graph in graphs:
        newserie = []

        if metric_name is None:
            zoomtype = ''
        elif graph['name'] != metric_name:
            continue
        else:
            zoomtype = 'x'

        for serie in graph['series']:

            datapoints = get_graphite_metrics_datapoints(from_option,
                                                         engine, db_name,
                                                         hostname, serie[
                                                             'data'],
                                                         granurality,
                                                         url=url,
                                                         normalize_series=graph['normalize_series'])

            if datapoints:
                newserie.append({
                    'name': serie['name'],
                    'data': datapoints})
            else:
                newserie.append({
                    'name': serie['name'],
                    'data': []})

        newgraph.append({
            "name": graph["name"],
            "series": str(ast.literal_eval(json.dumps(newserie))),
            "type": graph["type"],
            "tooltip_point_format": graph["tooltip_point_format"],
            "y_axis_title": graph["y_axis_title"],
            "stacking": graph["stacking"],
            "graph_name": graph["graph_name"],
            "zoomtype": zoomtype,
            "normalize_series": graph['normalize_series']
        })

    return newgraph
