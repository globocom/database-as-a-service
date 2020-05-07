class RequiredNumberOfInstances(Exception):
    pass


class ReadOnlyHostsLimit(Exception):
    pass


class ManagerNotFound(Exception):
    pass


class ManagerInvalidStatus(Exception):
    pass


class DatabaseNotAvailable(Exception):
    pass


class DatabaseIsNotHA(Exception):
    pass


class DatabaseUpgradePlanNotFound(Exception):
    pass


class HostIsNotReadOnly(Exception):
    pass
