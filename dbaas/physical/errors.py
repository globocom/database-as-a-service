from __future__ import absolute_import
from system.models import Configuration


class NoDiskOfferingError(OverflowError):
    def __init__(self, typo, size):
        msg = 'No disk offering {} than {}kb'.format(typo, size)
        super(OverflowError, self).__init__(msg)


class NoDiskOfferingGreaterError(NoDiskOfferingError):
    def __init__(self, size):
        super(NoDiskOfferingGreaterError, self).__init__('greater', size)


class NoDiskOfferingLesserError(NoDiskOfferingError):
    def __init__(self, size):
        super(NoDiskOfferingLesserError, self).__init__('lesser', size)


class DiskOfferingMaxAutoResize(OverflowError):
    def __init__(self):
        auto_resize_gb = Configuration.get_by_name_as_int(
            name='auto_resize_max_size_in_gb', default=100
        )
        msg = 'Disk auto resize can not be greater than {}GB'.format(
            auto_resize_gb
        )
        super(OverflowError, self).__init__(msg)
