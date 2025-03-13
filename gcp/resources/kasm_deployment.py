from pulumi import Config
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs
from pulumi_kubernetes.core.v1 import Secret
import pulumi
import base64
from time import sleep

config = Config()
data = config.require_object("data")
gcp_config = Config("gcp")


class KasmDeployment:
    def __init__(self, gcp_network, kubernetes_provider, gcp_db):

        helm_zone_config = []
        for zone in data.get("additional_kasm_zone"):
            zone_config = {
                "name": zone["name"],
                "cloudProvider": zone["cloud_provider"],
                "hostName": zone["domain"],
                "loadBalancerIP": zone["load_balancer_ip"]

            }
            helm_zone_config.append(zone_config)


        pulumi.export("test", helm_zone_config)


        self.helm = Release("kasm-helm",
                       ReleaseArgs(
                           chart="../kasm-helm/kasm-single-zone",
                           values={
                               "global": {
                                   "hostname": data.get("domain"),
                                   "pulumiDeployment": {
                                       "cloudProvider": "gcp",
                                       "loadBalancerIP": gcp_network.public_ip_address.name,
                                       "additionalZone": helm_zone_config
                                   },
                                   "standAloneDb": {
                                       "postgresHost": "db.kasm.int"
                                   },
                                   "kasmPasswords": {
                                       "dbPassword": gcp_db.kasm_user.password,
                                   },
                               },
                           },
                           namespace="kasm",
                           skip_await=False,
                           create_namespace=True,
                           timeout=1800
                       ),
                       opts=pulumi.ResourceOptions(
                           provider=kubernetes_provider,
                           depends_on=[gcp_db.kasm_user, gcp_db.kasm_db]
                       )
                       )

        self.kasm_secrets = Secret.get(f'kasm/kasm-secrets',
                                       self.helm.status.status.apply(lambda v: f'kasm/kasm-secrets'),
                                                    opts=pulumi.ResourceOptions(
                                                        depends_on=[self.helm],
                                                        provider=kubernetes_provider,
                                                    )
                                                    )


        self.manager_token = self.kasm_secrets.data["manager-token"].apply(lambda v: base64.b64decode(v).decode('utf-8'))
        pulumi.export("Kasm URL", data.get("domain"))
        pulumi.export("Kasm Admin User:", "admin@kasm.local")
        pulumi.export("Kasm Un-privileged User", "user@kasm.local")
        pulumi.export("Kasm Admin Password", self.kasm_secrets.data["admin-password"].apply(lambda v: base64.b64decode(v).decode('utf-8')))
        pulumi.export("Kasm User Password", self.kasm_secrets.data["user-password"].apply(lambda v: base64.b64decode(v).decode('utf-8')))
        pulumi.export("Kasm DB Password:", self.kasm_secrets.data["db-password"].apply(lambda v: base64.b64decode(v).decode('utf-8')))
        pulumi.export("Kasm Manager Token", self.manager_token)
        pulumi.export("Kasm Service Registration Token", self.kasm_secrets.data["service-token"].apply(lambda v: base64.b64decode(v).decode('utf-8')))
        pulumi.export("Kasm Redis Password", self.kasm_secrets.data["redis-password"].apply(lambda v: base64.b64decode(v).decode('utf-8')))

