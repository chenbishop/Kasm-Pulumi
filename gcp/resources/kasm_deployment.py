from pulumi import Config
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs
from pulumi_kubernetes.core.v1 import Secret
import pulumi
import base64
from time import sleep

config = Config()
data = config.require_object("data")
gcp_config = Config("gcp")
secrets = config.require_secret_object("data")
cert = secrets.apply(lambda secret_obj: secret_obj.get("cert"))
cert_key = secrets.apply(lambda secret_obj: secret_obj.get("cert_key"))

## setting default cert and key helm values
cert = cert.apply(lambda v: """######    Place public SSL Cert here     ######
######  Leave empty for Helm to generate ######""" if "Leave it as it is for Helm to generate" in v else v)
cert_key = cert_key.apply(lambda v: """######    Place public SSL Key here      ######
######  Leave empty for Helm to generate ######""" if "Leave it as it is for Helm to generate" in v else v)

class KasmDeployment:
    def __init__(self, gcp_network, kubernetes_provider, gcp_db):

        # Load the zone configuration
        helm_zone_config = []
        for zone in data.get("additional_kasm_zone"):
            zone_config = {
                "name": zone["name"],
                "cloudProvider": zone["cloud_provider"],
                "hostName": zone["domain"],
                "loadBalancerIP": zone["load_balancer_ip"]

            }
            helm_zone_config.append(zone_config)

        # Deploying Helm
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
                               "kasmCerts": {
                                   "ingress": {
                                       "cert": cert,
                                       "key": cert_key
                                   }
                               }
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

        # Get the Created Secrets
        self.kasm_secrets = Secret.get(f'kasm/kasm-secrets',
                                       self.helm.status.status.apply(lambda v: f'kasm/kasm-secrets'),
                                                    opts=pulumi.ResourceOptions(
                                                        depends_on=[self.helm],
                                                        provider=kubernetes_provider,
                                                    )
                                                    )

        # Get the Created SSL Cert Secret
        self.kasm_nginx_cert = Secret.get(f'kasm/kasm-nginx-proxy-cert',
                                       self.helm.status.status.apply(lambda v: f'kasm/kasm-nginx-proxy-cert'),
                                       opts=pulumi.ResourceOptions(
                                           depends_on=[self.helm],
                                           provider=kubernetes_provider,
                                       )
                                       )

        # Exporting Secrets
        self.manager_token = self.kasm_secrets.data["manager-token"].apply(lambda v: base64.b64decode(v).decode('utf-8'))
        self.service_token = self.kasm_secrets.data["service-token"].apply(lambda v: base64.b64decode(v).decode('utf-8'))
        self.tls_crt = self.kasm_nginx_cert.data["tls.crt"].apply(lambda v: base64.b64decode(v).decode('utf-8'))
        self.tls_key = self.kasm_nginx_cert.data["tls.key"].apply(lambda v: base64.b64decode(v).decode('utf-8'))
        pulumi.export("Kasm URL", data.get("domain"))
        pulumi.export("Kasm Admin User:", "admin@kasm.local")
        pulumi.export("Kasm Un-privileged User", "user@kasm.local")
        pulumi.export("Kasm Admin Password", self.kasm_secrets.data["admin-password"].apply(lambda v: base64.b64decode(v).decode('utf-8')))
        pulumi.export("Kasm Manager Token", self.manager_token)
        pulumi.export("Kasm Service Registration Token", self.service_token)
        pulumi.export("Kasm Redis Password", self.kasm_secrets.data["redis-password"].apply(lambda v: base64.b64decode(v).decode('utf-8')))
