# -*- coding:utf-8 -*-
from util.html import render_progress_bar
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from collections import Iterable
from django import template
from django.utils.safestring import mark_safe
import logging
from logical.models import MB_FACTOR, GB_FACTOR

getcontext().rounding = ROUND_HALF_EVEN
TWO = Decimal(10) ** -2
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


@register.tag
def render_detailed_capacity_html(parser, token):
    '''
    Usage: {% render_detailed_progress_bar database_obj type %}
    params:
        - database_obj: Logical Database object
        - type: type of bar. can be: disk or memory

    Ex. For physical disk bar:
        {% render_detailed_progress_bar database disk %}
    Ex. For physical momery bar:
        {% render_detailed_progress_bar database memory %}
    '''

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
    COLORS = {
        'blue': '#409fdf',
        'grey': '#949398',
        'green': '#70bf45',
    }

    def __init__(self, obj_name, bar_type):
        self.obj_name = obj_name
        self.bar_type = bar_type
        self.bars = []

    def _get_master_instances(self):
        masters = self.database.driver.get_master_instance()
        if not isinstance(masters, Iterable):
            masters = [masters]

        return masters

    def _init_vars(self, database):
        self.html = ''
        self.disk_parts = []
        self.memory_parts = []
        self.database = database
        self.databaseinfra = database.databaseinfra
        self.master_instances = self._get_master_instances()
        self.is_in_memory = database.engine.engine_type.is_in_memory
        self.is_persisted = database.plan.has_persistence

    @staticmethod
    def normalize_number(n):
        n = Decimal(round(n, 2))
        return n.quantize(TWO)

    def render_bar(self):
        func = getattr(self, "render_{}_bar".format(self.bar_type))
        return func() if func else ''

    def render(self, context):
        obj = context.get(self.obj_name)
        if obj is None:
            return ''
        self._init_vars(obj)

        html = ''
        for instance in self.master_instances:
            self.instance = instance
            self.host_attr = instance.hostname.nfsaas_host_attributes.filter(is_active=True).first()
            try:
                html += self.render_bar()
            except Exception, e:
                LOG.error(
                    'Could not render bar for database {}. error: {}'.format(
                        self.database.id, e)
                )
                html = '<div>Could not render bar</div>'

        return mark_safe(html)

    @property
    def total_disk_in_gb(self):
        return self.normalize_number(self.host_attr.nfsaas_size_kb * MB_FACTOR)

    @property
    def used_disk_in_gb(self):
        if self.host_attr.nfsaas_used_size_kb is not None:
            total_disk_in_gb = (self.host_attr.nfsaas_used_size_kb) * MB_FACTOR
            return self.normalize_number(total_disk_in_gb)
        return

    @property
    def used_database_in_gb(self):
        used_size = self.instance.used_size_in_bytes
        if used_size is None:
            return
        return self.normalize_number(used_size * GB_FACTOR)

    @property
    def used_other_in_gb(self):
        if self.used_disk_in_gb is None:
            return None
        else:
            used_other_in_gb = self.used_disk_in_gb - self.used_database_in_gb
            return self.normalize_number(used_other_in_gb)

    @property
    def free_disk_in_gb(self):
        if self.used_disk_in_gb is None:
            free_disk_in_gb = self.total_disk_in_gb - self.used_database_in_gb
        else:
            free_disk_in_gb = self.total_disk_in_gb - self.used_disk_in_gb

        return self.normalize_number(free_disk_in_gb)

    @property
    def database_percent(self):
        if self.total_disk_in_gb:
            database_percent = (self.used_database_in_gb * 100) / self.total_disk_in_gb
        else:
            database_percent = 0.0

        return self.normalize_number(database_percent)

    @property
    def disk_percent(self):
        if self.total_disk_in_gb:
            used_disk = self.used_disk_in_gb or Decimal(0)
            disk_percent = (used_disk * 100) / self.total_disk_in_gb
        else:
            disk_percent = 0.0

        return self.normalize_number(disk_percent)

    @property
    def other_percent(self):
        if not self.total_disk_in_gb or self.is_in_memory:
            other_percent = 0
        else:
            other_percent = (self.used_other_in_gb * 100) / self.total_disk_in_gb

        return self.normalize_number(other_percent)

    @property
    def free_percent(self):
        free_percent = 100 - (self.database_percent + self.other_percent)

        return self.normalize_number(free_percent)

    @property
    def free_disk_percent(self):
        free_percent = 100 - (self.disk_percent + self.other_percent)

        return self.normalize_number(free_percent)

    def render_disk_bar(self):
        if self.used_database_in_gb is None or self.used_disk_in_gb is None:
            return ''
        is_in_memory_and_not_persisted = (self.is_in_memory and
                                          not self.is_persisted)
        not_in_memory_and_used_disk_none = (self.used_disk_in_gb is None and
                                            not self.is_in_memory)

        if is_in_memory_and_not_persisted or not_in_memory_and_used_disk_none:
            return ''

        parts = [{
            'name': 'database',
            'label': 'Used' if self.is_in_memory else 'Database',
            'percentage': self.disk_percent if self.is_in_memory else self.database_percent,
            'used_space': self.used_disk_in_gb if self.is_in_memory else self.used_database_in_gb,
            'color': self.COLORS['blue']
        }]
        if self.used_other_in_gb is not None and not self.is_in_memory:
            parts.append({
                'name': 'other',
                'label': 'Others',
                'percentage': self.other_percent,
                'used_space': self.used_other_in_gb,
                'color': self.COLORS['grey']
            })
        parts.append({
            'name': 'free',
            'label': 'Free',
            'percentage': self.free_disk_percent if self.is_in_memory else self.free_percent,
            'used_space': self.free_disk_in_gb,
            'color': self.COLORS['green']
        })

        return self.render_template(parts, 'disk')

    @property
    def total_db_memory_in_gb(self):
        return self.normalize_number(self.instance.total_size_in_bytes * GB_FACTOR)

    @property
    def used_db_memory_in_gb(self):
        used_size = self.instance.used_size_in_bytes
        if used_size is None:
            return
        return self.normalize_number(used_size * GB_FACTOR)

    @property
    def used_db_memory_percent(self):
        used_memory_percent = 0
        if self.total_db_memory_in_gb:
            used_memory_percent = (self.used_db_memory_in_gb * 100) / self.total_db_memory_in_gb

        return self.normalize_number(used_memory_percent)

    @property
    def free_db_memory_percent(self):
        return self.normalize_number(100 - self.used_db_memory_percent)

    @property
    def free_db_memory_size_in_gb(self):
        return self.total_db_memory_in_gb - self.used_db_memory_in_gb

    def render_memory_bar(self):
        if self.used_db_memory_in_gb is None:
            return ''
        parts = [{
                'name': 'database',
                'label': 'Used',
                'percentage': self.used_db_memory_percent,
                'used_space': self.used_db_memory_in_gb,
                'color': self.COLORS['blue']},
            {
                'name': 'free',
                'label': 'Free',
                'percentage': self.free_db_memory_percent,
                'used_space': self.free_db_memory_size_in_gb,
                'color': self.COLORS['green']
        }]

        return self.render_template(parts, 'memory')

    def render_template(self, parts, bar_type):
        t = template.loader.get_template('progress_bar/progress_bar.html')
        c = template.Context({
            'bars': parts,
            'bar_type': bar_type,
            'hostname': self.instance.dns
        })
        return t.render(c)
