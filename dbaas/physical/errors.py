
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
