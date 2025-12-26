import kubernetes

from src.common.config_lib import app_config

USE_EXTERNAL_CONFIG = app_config.config.get("kubernetes", {}).get("use_external", False)


class KubernetesCustomObjectApi:
    def __init__(self, external: bool | None = False):
        if external:
            kubernetes.config.load_config()
        else:
            kubernetes.config.load_incluster_config()
        self.api = self._get_api()

    def _get_api(self):
        api = kubernetes.client.CustomObjectsApi()
        return api

    def get_api(self):
        return self.api


custom_api = KubernetesCustomObjectApi(external=USE_EXTERNAL_CONFIG)
