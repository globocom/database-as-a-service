from collections import OrderedDict
from operator import itemgetter


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
    step1 = Step('mongodb', 'First step', 1,
        'Please check acls with the team', ('workflow.mongodb.migration.step0',
            'workflow.mongodb.migration.step1'))

    step2 = Step('mongodb', 'First step', 2,
        'Please check acls with the team', ('workflow.mongodb.migration.step2',
            'workflow.mongodb.migration.step3'))

    return (step1, step2)

