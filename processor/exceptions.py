
class UnknownMonitorException(Exception):
    def __init__(self, monitor_id):
        self.monitor_id = monitor_id
