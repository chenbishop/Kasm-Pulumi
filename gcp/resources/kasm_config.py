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
    def __init__(self, gcp_cluster, kasm_helm, kasm_agent, get_kasm_config_script):

        # upstream_auth_address and proxy_hostname environmental variables for different zones
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

        # number of additional zones environmental variables
        env_vars.append(EnvVarArgs(
            name="ADDITIONAL_ZONES", value=str(len(additional_zone))
        ))

        # primary zone domain URL environmental variables
        env_vars.append(EnvVarArgs(
            name="URL", value=data.get("domain")
        ))

        # total number of agents environmental variables
        total_agent = data.get("agent_number")
        for zone in additional_zone:
            total_agent = total_agent+zone["agent_number"]
        env_vars.append(EnvVarArgs(
            name="AGENT_NUMBER", value=str(total_agent)
        ))

        # admin password environmental variables, using secret ref
        env_vars.append(EnvVarArgs(
            name="ADMIN_PASS", value_from=EnvVarSourceArgs(
                secret_key_ref=SecretKeySelectorArgs(
                    name="kasm-secrets",
                    key="admin-password",
        ))))

        # all agents' IP addresses environmental variable
        all_agent_list = []
        for agent in kasm_agent.agent_vm:
            all_agent_list.append(agent.network_interfaces[0].network_ip)
        for zone in list(kasm_agent.additional_zone_agents.values()):
            for agent in zone:
                all_agent_list.append(agent.network_interfaces[0].network_ip)
        env_vars.append(
            EnvVarArgs(
                name="AGENT_LIST",
                value=pulumi.Output.all(*all_agent_list).apply(
                    lambda *args: " ".join(str(item) for item in args)  # Convert each item to string before joining
                )
        ))

        # Kuberentes job to configure Kasm, this includes enable agents, configuring zones and group settings
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
            opts=pulumi.ResourceOptions(provider=gcp_cluster.cluster_provider,
                                        depends_on=[kasm_helm.helm])
        )