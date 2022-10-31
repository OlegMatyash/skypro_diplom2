import logging


class HealthCheckFilter(logging.Filter):
    def filter(self, record) -> bool:
        return record.getMessage().find('/ping/') == -1
