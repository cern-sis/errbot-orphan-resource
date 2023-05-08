from errbot import BotPlugin, botcmd
from kubernetes import client, config


class Orphan(BotPlugin):
    def activate(self):
        super().activate()
        config.load_incluster_config()

    @botcmd
    def orphan_resources(self, msg, args):
        api = client.CoreV1Api()
        namespaces = api.list_namespace().items
        # self.log.info("namespaces: ")
        # self.log.info(namespaces)
        excluded_namespaces = ["jimil-test"]
        resources = []
        for ns in namespaces:
            if ns.metadata.name not in excluded_namespaces:
                api = client.CustomObjectsApi()
                resources += api.list_cluster_custom_object(
                    group="argoproj.io",
                    version="v1alpha1",
                    plural="applicationsets",
                )["items"]
        all_resources = api.list_cluster_custom_object("", "", "", "").get("items", [])
        unmanaged_resources = [
            resource for resource in all_resources if resource not in resources
        ]
        return "\n".join(
            [
                f"{r['kind']}/{r['metadata']['name']} ({r.get('metadata', {}).get('namespace')})"
                for r in unmanaged_resources
            ]
        )
