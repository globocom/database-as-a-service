# -*- coding: utf-8 -*-
from collections import OrderedDict
from operator import itemgetter
from workflow import settings


class Step(tuple):

    'Step(engine, status, description, order, warning, step_classes)'

    __slots__ = ()

    _fields = ('engine', 'status', 'description',
               'order', 'warning', 'step_classes')

    def __new__(_cls, engine, status, description, order, warning, step_classes):
        'Create new instance of Step(engine, status, description, order, warning, step_classes)'
        return tuple.__new__(_cls, (engine, status, description, order, warning, step_classes))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new Step object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 5:
            raise TypeError('Expected 6 arguments, got %d' % len(result))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return 'Step(engine=%r, status=%r, \
                     description=%r, order=%r, warning=%r, step_classes=%r)' % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values'
        return OrderedDict(zip(self._fields, self))

    def _replace(_self, **kwds):
        'Return a new Step object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('engine', 'status', 'description',
                                            'order', 'warning', 'step_classes'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        'Return self as a plain tuple. Used by copy and pickle.'
        return tuple(self)

    __dict__ = property(_asdict)

    def __getstate__(self):
        'Exclude the OrderedDict from pickling'
        pass

    engine = property(itemgetter(0), doc='Alias for field number 0')
    status = property(itemgetter(1), doc='Alias for field number 1')
    description = property(itemgetter(2), doc='Alias for field number 2')
    order = property(itemgetter(3), doc='Alias for field number 3')
    warning = property(itemgetter(4), doc='Alias for field number 4')
    step_classes = property(itemgetter(5), doc='Alias for field number 5')


def get_flipeerfox_migration_steps():
    step1 = Step('mysql', 'Ready to start Migration!',
                 'Create new instances', 0,
                 '',
                 settings.MYSQL_FLIPPER_FOX_MIGRATION_1)

    step2 = Step('mysql', 'New instances created!',
                 'Switch DNS', 1,
                 'Please, check replication and ACL',
                 settings.MYSQL_FLIPPER_FOX_MIGRATION_2)

    step3 = Step('mysql', 'DNS switched!',
                 'Clean old instances', 2,
                 'Please, check aplication and monitoring',
                 settings.MYSQL_FLIPPER_FOX_MIGRATION_3)

    step4 = Step('mysql', 'Database migrated!',
                 'There is not next step. Database migrated', 3,
                 'Please, check aplication and monitoring',
                 settings.MYSQL_FLIPPER_FOX_MIGRATION_4)

    return (step1, step2, step3, step4)
