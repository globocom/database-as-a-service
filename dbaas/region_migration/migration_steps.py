from collections import OrderedDict
from operator import itemgetter
from workflow import settings
import re


class Step(tuple):
    'Step(engine, description, order, msg, step_classes)'

    __slots__ = ()

    _fields = ('engine', 'description', 'order', 'msg', 'step_classes')

    def __new__(_cls, engine, description, order, msg, step_classes):
        'Create new instance of Step(engine, description, order, msg, step_classes)'
        return tuple.__new__(_cls, (engine, description, order, msg, step_classes))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new Step object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 5:
            raise TypeError('Expected 5 arguments, got %d' % len(result))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return 'Step(engine=%r, description=%r, order=%r, msg=%r, step_classes=%r)' % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values'
        return OrderedDict(zip(self._fields, self))

    def _replace(_self, **kwds):
        'Return a new Step object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('engine', 'description', 'order', 'msg', 'step_classes'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)

    __dict__ = property(_asdict)

    def __getstate__(self):
        'Exclude the OrderedDict from pickling'
        pass

    engine = property(itemgetter(0), doc='Alias for field number 0')
    description = property(itemgetter(1), doc='Alias for field number 1')
    order = property(itemgetter(2), doc='Alias for field number 2')
    msg = property(itemgetter(3), doc='Alias for field number 3')
    step_classes = property(itemgetter(4), doc='Alias for field number 4')

def get_mongodb_steps():
    step1 = Step('mongodb', 'Ready to start migration', 0,
         '', settings.MONGODB_REGION_MIGRATION_1)

    step2 = Step('mongodb', 'Create new instances', 1,
        'Please, check replication and ACL', settings.MONGODB_REGION_MIGRATION_2)

    step3 = Step('mongodb', 'Switch primary instance', 2,
        'Please, check if the application is ok', settings.MONGODB_REGION_MIGRATION_3)

    step4 = Step('mongodb', 'Switch DNS', 3,
        'Please, check aplication and monitoring', settings.MONGODB_REGION_MIGRATION_4)

    step5 = Step('mongodb', 'Clean old instances', 4,
        'Please, check aplication and monitoring', settings.MONGODB_REGION_MIGRATION_5)

    step6 = Step('mongodb', 'There is not next step. Database migrated', 5,
        '', settings.MONGODB_REGION_MIGRATION_6)

    return (step1, step2, step3, step4, step5, step6)

def get_mysql_steps():
   pass

def get_redis_steps():
    pass

def get_engine_steps(engine):
    engine = engine.lower()
    if re.match(r'^mongo.*', engine):
        return get_mongodb_steps()
    elif re.match(r'^mysql.*', engine):
        return get_mysql_steps()
    elif re.match(r'^redis.*', engine):
        return get_redis_steps()


