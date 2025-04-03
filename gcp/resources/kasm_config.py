from pulumi import Config
from pulumi_kubernetes.batch.v1 import Job, JobSpecArgs
from pulumi_kubernetes.core.v1 import PodTemplateSpecArgs, PodSpecArgs, ContainerArgs, EnvVarArgs, EnvVarSourceArgs, SecretKeySelectorArgs
import pulumi



config = Config()
data = config.require_object("data")
gcp_config = Config("gcp")
secrets = config.require_secret_object("data")
additional_zone = data.get("additional_kasm_zone")


class KasmConfig:
    def __init__(self, kubernetes_provider, kasm_helm, kasm_agent, get_kasm_config_script):

        env_vars = [
                       EnvVarArgs(
                           name=f"{zone['name']}_UPSTREAM_AUTH_ADDRESS",
                           value=zone["domain"]
                       ) for zone in additional_zone
                   ] + [
                       EnvVarArgs(
                           name=f"{zone['name']}_PROXY_HOSTNAME",
                           value=f'{zone["proxy_domain"]}'
                       ) for zone in additional_zone
                   ]

        env_vars.append(EnvVarArgs(
            name="ADDITIONAL_ZONES", value=str(len(additional_zone))
        ))
        env_vars.append(EnvVarArgs(
            name="URL", value=data.get("domain")
        ))
        total_agent = data.get("agent_number")
        for zone in additional_zone:
            total_agent = total_agent+zone["agent_number"]
        env_vars.append(EnvVarArgs(
            name="AGENT_NUMBER", value=str(total_agent)
        ))

        env_vars.append(EnvVarArgs(
            name="ADMIN_PASS", value_from=EnvVarSourceArgs(
                secret_key_ref=SecretKeySelectorArgs(
                    name="kasm-secrets",
                    key="admin-password",
        )
            )
        ))


        self.job = Job(
            "kasm-config",
            metadata={
                "name": "kasm-config",
                "namespace": "kasm"
            },
            spec=JobSpecArgs(
                backoff_limit=4,
                template=PodTemplateSpecArgs(
                    spec=PodSpecArgs(
                        containers=[ContainerArgs(
                            name="bkasm-config-container",
                            image="ubuntu:24.04",
                            command=["/bin/bash", "-c", get_kasm_config_script()],
                            env=env_vars
                        )],
                        restart_policy="Never"
                    )
                ),
            ),
            opts=pulumi.ResourceOptions(provider=kubernetes_provider,
                                        depends_on=[kasm_helm.helm])
        )

