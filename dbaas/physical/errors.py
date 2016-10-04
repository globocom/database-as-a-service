
class NoDiskOfferingError(OverflowError):
    def __init__(self, size):
        msg = 'No disk offering greater than {}kb'.format(size)
        super(OverflowError, self).__init__(msg)
