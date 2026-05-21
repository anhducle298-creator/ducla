class PrometheusCollector:
    def __init__(self, base_url):
        self.base_url = base_url

    def query(self, promql):
        raise NotImplementedError("Prometheus query collector will be implemented later")
