# -*- coding:utf-8 -*-
from util.html import render_progress_bar, render_detailed_progress_bar
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from django import template
from django.utils.safestring import mark_safe
import logging

getcontext().rounding = ROUND_HALF_EVEN
ONE = Decimal(10) ** -1
register = template.Library()

LOG = logging.getLogger(__name__)


@register.simple_tag
def render_capacity_html(database):
    try:
        message = "%d of %s (MB)" % (
            database.used_size_in_mb, (database.total_size_in_mb) or 'unlimited')
        return render_progress_bar(database.capacity * 100, message=message)
    except:
        # any error show Unkown message and log error. This avoid break page if there is a problem
        # with some database
        LOG.exception('Error getting capacity of database %s', database)
        return "Unknown"


@register.simple_tag
def xxrender_detailed_capacity_html(database):
    def render(nfsaas_size_in_gb,
               nfsaas_used_size_in_gb,
               used_size_in_gb,
               used_other_in_gb,
               free_space_in_gb,
               other_percent,
               database_percent):

        return render_detailed_progress_bar(
            used_size_in_gb,
            used_other_in_gb,
            free_space_in_gb,
            other_percent=other_percent,
            database_percent=database_percent,
        )

    databaseinfra = database.databaseinfra
    host_attr = databaseinfra.instances.first().hostname.nfsaas_host_attributes.first()
    nfsaas_size_in_gb = (host_attr.nfsaas_size_kb or 0.0) * (1.0 / 1024.0 / 1024.0)
    nfsaas_used_size_in_gb = databaseinfra.disk_used_size_in_gb
    if nfsaas_used_size_in_gb is None:
        free_space_in_gb = nfsaas_size_in_gb - database.used_size_in_gb
        used_other_in_gb = None
        other_percent = 0
    else:
        used_other_in_gb = nfsaas_used_size_in_gb - database.used_size_in_gb
        free_space_in_gb = nfsaas_size_in_gb - nfsaas_used_size_in_gb
        other_percent = float(used_other_in_gb * 100) / nfsaas_size_in_gb
    database_percent = float(database.used_size_in_gb * 100) / nfsaas_size_in_gb
    params = dict(
        nfsaas_size_in_gb=nfsaas_size_in_gb,
        nfsaas_used_size_in_gb=nfsaas_used_size_in_gb,
        used_size_in_gb=database.used_size_in_gb,
        used_other_in_gb=used_other_in_gb,
        free_space_in_gb=free_space_in_gb,
        other_percent=other_percent,
        database_percent=database_percent,
    )

    return '{}'.format(render(**params))


@register.tag
def render_detailed_capacity_html(parser, token):

    try:
        split_contents = token.split_contents()
        obj_name = split_contents[1]
        bar_type = split_contents[2]
    except IndexError:
        raise template.TemplateSyntaxError(
            "%r tag requires 1 argument." % split_contents
        )

    return DetailedProgressBarNode(obj_name, bar_type)


class DetailedProgressBarNode(template.Node):
    '''
    Static class receive an array with contains dicts.
    Witch index that array means a part of the bar.
    This dicts must have the keys:
        - name: used to name the css class on template;
        - label: will be appers on label;
        - percentage: percentage of the part;
        - used_space: space used;
        - space_metric: Bytes, KB, MB, GB;
        - color: color of bar part;

    Ex. if i wanna make a bar with 2 part ill pass:
        DetailedProgressBar([{
            'name': 'database',
            'label': 'Database',
            'percentage': 10,
            'used_space': 1.0,
            'space_metric': 'GB',
            'color': '#409fdf'},
            {'name': 'free',
             'label': 'Free',
             'percentage': 90.0,
             'used_space': 9.0,
             'space_metric': 'GB',
             'color': '#949398'
             ''}])

        And that class will return the rendered html.
    '''

    COLORS = {
        'blue': '#409fdf',
        'grey': '#949398',
        'green': '#70bf45',
    }

    def __init__(self, obj_name, bar_type):
        self.obj_name = obj_name
        self.bar_type = bar_type
        self.bars = []

    def _init_vars(self, database):
        self.html = ''
        self.disk_parts = []
        self.memory_parts = []
        self.database = database
        self.databaseinfra = self.database.databaseinfra
        self.instance = self.databaseinfra.instances.first()
        self.is_memory = self.database.engine.engine_type.is_in_memory

    @staticmethod
    def normalize_number(n):
        n = Decimal(round(n, 2))
        return n.quantize(ONE)

    def render(self, context):
        obj = context.get(self.obj_name)
        self._init_vars(obj)
        if obj is None:
            return ''

        if self.bar_type == 'disk':
            html = self.render_disk_bar()
        else:
            html = self.render_memory_bar()

        return mark_safe(html)

    def _make_disk_part(self, **kw):
        self.disk_parts.append(kw)

    def _make_memory_part(self, **kw):
        self.memory_parts.append(kw)

    def render_disk_bar(self):
        self.host_attr = self.instance.hostname.nfsaas_host_attributes.first()
        nfsaas_size_in_gb = (self.host_attr.nfsaas_size_kb or 0.0) * (1.0 / 1024.0 / 1024.0)
        nfsaas_used_size_in_gb = self.databaseinfra.disk_used_size_in_gb
        if nfsaas_used_size_in_gb is None:
            free_space_in_gb = nfsaas_size_in_gb - self.database.used_size_in_gb
            used_other_in_gb = None
            other_percent = 0
        else:
            used_other_in_gb = nfsaas_used_size_in_gb - self.database.used_size_in_gb
            free_space_in_gb = nfsaas_size_in_gb - nfsaas_used_size_in_gb
            other_percent = float(used_other_in_gb * 100) / nfsaas_size_in_gb
        database_percent = float(self.database.used_size_in_gb * 100) / nfsaas_size_in_gb
        self._make_disk_part(**{
            'name': 'database',
            'label': 'Database',
            'percentage': self.normalize_number(database_percent or 0),
            'used_space': self.normalize_number(self.database.used_size_in_gb),
            'color': self.COLORS['blue']
        })
        if used_other_in_gb is not None:
            self._make_disk_part(**{
                'name': 'other',
                'label': 'Others',
                'percentage': self.normalize_number(other_percent or 0),
                'used_space': self.normalize_number(used_other_in_gb),
                'color': self.COLORS['grey']
            })
            self._make_disk_part(**{
                'name': 'free',
                'label': 'Free',
                'percentage': self.normalize_number(100 - (database_percent + other_percent)),
                'used_space': self.normalize_number(free_space_in_gb),
                'color': self.COLORS['green']
            })
        else:
            self._make_disk_part(**{
                'name': 'free',
                'label': 'Free',
                'percentage': self.normalize_number(100 - (database_percent + other_percent)),
                'used_space': self.normalize_number(free_space_in_gb),
                'color': self.COLORS['grey']
            })
        return self.render_template(self.disk_parts, 'disk')

    def render_memory_bar(self):
        total_size_in_gb = self.database.total_size_in_gb
        used_size_in_gb = self.database.used_size_in_gb
        used_percent = float(used_size_in_gb * 100) / total_size_in_gb
        free_size_in_gb = total_size_in_gb - used_size_in_gb
        self._make_memory_part(**{
            'name': 'database',
            'label': 'Database',
            'percentage': self.normalize_number(used_percent or 0),
            'used_space': self.normalize_number(used_size_in_gb),
            'color': self.COLORS['blue']
        })
        self._make_memory_part(**{
            'name': 'free',
            'label': 'Free',
            'percentage': self.normalize_number(100 - (used_percent)),
            'used_space': self.normalize_number(free_size_in_gb),
            'color': self.COLORS['grey']
        })

        return self.render_template(self.memory_parts, 'memory')

    def render_template(self, parts, bar_type):
        t = template.loader.get_template('progress_bar/progress_bar.html')
        c = template.Context({
            'bars': parts,
            'bar_type': bar_type
        })
        return t.render(c)
