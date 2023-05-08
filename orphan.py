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
        self.log.info("namespaces: ")
        self.log.info(namespaces)
        excluded_namespaces = ["jimil-test"]
        resources = []
        for ns in namespaces:
            self.log.info(ns.metadata.name)
            if ns.metadata.name not in excluded_namespaces:
                api = client.CustomObjectsApi()
                resources += api.list_cluster_custom_object(
                    "argoproj.io", "v1alpha1", ns.metadata.name, "applications"
                )["items"]
        all_resources = api.list_cluster_custom_object("", "", "", "").get("items", [])
        unmanaged_resources = []
        for resource in all_resources:
            if resource not in resources:
                unmanaged_resources.append(resource)
        return "\n".join(
            [f"{r['kind']}/{r['metadata']['name']}" for r in unmanaged_resources]
        )
