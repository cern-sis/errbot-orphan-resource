from errbot import BotPlugin, botcmd
from kubernetes import client, config


class Orphan(BotPlugin):
    def activate(self):
        super().activate()
        config.load_incluster_config()

    @botcmd
    def orphan_resources(self, msg, args):
        api = client.CustomObjectsApi()
        namespaces = client.CoreV1Api().list_namespace().items

        argocd_group = "argoproj.io"
        argocd_version = "v1alpha1"
        argocd_plural = "applicationsets"

        argocd_resources = []
        excluded_namespaces = ["jimil-test"]
        for ns in namespaces:
            if ns.metadata.name not in excluded_namespaces:
                resources = api.list_namespaced_custom_object(
                    group=argocd_group, version=argocd_version, plural=argocd_plural
                )["items"]
                argocd_resources += resources

        k8s_resources = []
        resource_types = [
            "deployments",
            "statefulsets",
            "persistentvolumeclaims",
            "services",
            "cronjobs",
            "jobs",
        ]
        for resource_type in resource_types:
            resources = getattr(client.AppsV1Api(), f"list_{resource_type}")().items
            k8s_resources += resources

        for resource_type in ["configmaps", "secrets"]:
            resources = getattr(client.CoreV1Api(), f"list_{resource_type}")().items
            k8s_resources += resources

        unmanaged_resources = [
            resource
            for resource in k8s_resources
            if (
                not any(
                    resource.metadata.name == argocd_res["metadata"]["name"]
                    for argocd_res in argocd_resources
                )
                and resource.metadata.namespace not in excluded_namespaces
            )
        ]

        output = [
            f"{r.kind}/{r.metadata.name} ({r.metadata.namespace})"
            for r in unmanaged_resources
        ]

        output_resource = "\n".join(output)

        return output_resource
