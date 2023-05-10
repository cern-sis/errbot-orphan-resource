from errbot import BotPlugin, botcmd
from kubernetes import client, config


class Orphan(BotPlugin):
    def activate(self):
        super().activate()
        config.load_incluster_config()

    @botcmd
    def orphan_resources(self, msg, args):
        namespaces = client.CoreV1Api().list_namespace().items
        excluded_namespaces = ["jimil-test"]
        k8s_resources = []
        app_types = ["deployment", "stateful_set"]
        core_types = ["config_map", "secret", "persistent_volume_claim", "service"]
        batch_types = ["cron_job", "job"]

        for ns in namespaces:
            if ns.metadata.name not in excluded_namespaces:
                for resource_type in app_types:
                    resources = getattr(
                        client.AppsV1Api(), f"list_namespaced_{resource_type}"
                    )(namespace=ns.metadata.name).items
                    k8s_resources += resources

                for resource_type in core_types:
                    resources = getattr(
                        client.CoreV1Api(), f"list_namespaced_{resource_type}"
                    )(namespace=ns.metadata.name).items
                    k8s_resources += resources

                for resource_type in batch_types:
                    resources = getattr(
                        client.BatchV1Api(), f"list_namespaced_{resource_type}"
                    )(namespace=ns.metadata.name).items
                    k8s_resources += resources
        unmanaged_resources = [
            resource
            for resource in k8s_resources
            if (
                not resource.metadata.labels
                or (
                    "argocd.argoproj.io/instance" not in resource.metadata.labels
                    and resource.metadata.namespace not in excluded_namespaces
                )
            )
        ]

        output = [
            f"{r.kind} {r.metadata.name} ({r.metadata.namespace})"
            for r in unmanaged_resources
        ]

        output_resource = "\n".join(output)

        return output_resource
