from pulumi import Config
from pulumi_gcp.compute import Network, Subnetwork, Router, RouterNat, GlobalAddress, Firewall, Address
from pulumi_gcp.dns import ManagedZone, ManagedZonePrivateVisibilityConfigArgs, \
    ManagedZonePrivateVisibilityConfigNetworkArgs
from pulumi_gcp.servicenetworking import Connection
import pulumi

config = Config()
data = config.require_object("data")


class SetupGcpNetwork:
    def __init__(self):
        # Create an VPC
        self.vpc = Network(
            f"kasm",
            name=f"kasm",
            auto_create_subnetworks=False,
        )

        # Create Subnet
        self.subnet = Subnetwork(f"kasm-{data.get("region")}-subnet",
                                 name=f"kasm-{data.get("region")}-subnet",
                                 ip_cidr_range="10.0.1.0/24",
                                 region=f"{data.get('region')}",
                                 network=self.vpc.id,
                                 )

        # Create a Cloud Router
        self.router = Router(f"kasm-{data.get("region")}-router",
                             name=f"kasm-{data.get("region")}-router",
                             network=self.vpc.id,
                             region=data.get('region')
                             )
        # Create a Cloud NAT
        self.nat = RouterNat(f"kasm-{data.get("region")}-nat",
                             name=f"kasm-{data.get("region")}-nat",
                             router=self.router.name,
                             nat_ip_allocate_option="AUTO_ONLY",
                             source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",
                             region=data.get('region'),
                             log_config={
                                 "enable": True,
                                 "filter": "ERRORS_ONLY"
                             })

        # Firewall for SSH
        if data.get("agent_enable_ssh")=="true":
            self.compute_ssh_firewall = Firewall(
                f"kasm-enable-ssh-firewall",
                name=f"kasm-enable-ssh-firewall",
                network=self.vpc.self_link,
                allows=[{
                    "protocol": "tcp",
                    "ports": ["22"]
                }],
                source_ranges=["0.0.0.0/0"]
            )

        # Firewall for HTTPS
        self.compute_https_firewall = Firewall(
            f"kasm-enable-https-firewall",
            name=f"kasm-enable-https-firewall",
            network=self.vpc.self_link,
            allows=[{
                "protocol": "tcp",
                "ports": ["443"]
            }],
            source_ranges=["0.0.0.0/0"]
        )

        # # Firewall for HTTP
        # self.compute_http_firewall = Firewall(
        #     f"kasm-enable-http-firewall",
        #     name=f"kasm-enable-http-firewall",
        #     network=self.vpc.self_link,
        #     allows=[{
        #         "protocol": "tcp",
        #         "ports": ["80"]
        #     }],
        #     source_ranges=["0.0.0.0/0"]
        # )

        # self.compute_firewall = Firewall(
        #     f"firewall-{gcp_config.get('region')}-nfs",
        #     name=f"enable-nfs-{gcp_config.get('region')}",
        #     network=self.vpc.self_link,
        #     allows=[FirewallAllowArgs(
        #         protocol="tcp",
        #         ports=["2049", "8888"],
        #     )],
        #     source_ranges=[data.get("subnet_cidr")]
        # )

        #  Private DNS zone for DB
        self.private_zone = ManagedZone(f"kasm-private-zone",
                                        name=f"kasm--private-zone",
                                        dns_name=f"kasm.int.",
                                        description=f"kasm Pivate DNS zone",
                                        visibility="private",
                                        private_visibility_config=ManagedZonePrivateVisibilityConfigArgs(
                                            networks=[
                                                ManagedZonePrivateVisibilityConfigNetworkArgs(
                                                    network_url=self.vpc.id,
                                                )
                                            ],
                                        ))

        # private IP for DB
        self.private_ip_address = GlobalAddress(f"kasm-db-private-ip",
                                                name=f"kasm-db-private-ip",
                                                purpose="VPC_PEERING",
                                                address="10.1.0.0",
                                                address_type="INTERNAL",
                                                prefix_length=16,
                                                network=self.vpc.id)

        # Public IP for GKE Ingress Load Balancer
        self.public_ip_address = GlobalAddress("kasm-loadbalancer-public-ip", name="kasm-loadbalancer-public-ip")
        pulumi.export("primary_ingress_loadbalancer", self.public_ip_address.address)


        self.private_vpc_connection = Connection(f"kasm-connection",
                                                 network=self.vpc.id,
                                                 service="servicenetworking.googleapis.com",
                                                 reserved_peering_ranges=[
                                                     self.private_ip_address.name])

        # Additional Zone Resources
        additional_zones = data.get("additional_kasm_zone")
        self.additional_zone_public_ip_address = []
        self.additional_zone_proxy_vm_public_ip_address=[]
        self.additional_zone_subnet=[]
        self.additional_zone_router=[]
        self.additional_zone_nat=[]
        for zone_index in range(2, len(data.get("additional_kasm_zone"))+2):
            zone_config = additional_zones[zone_index-2]
            # Additional Zone Subnet
            subnet = Subnetwork(f"kasm-{zone_config["region"]}-subnet",
                                     name=f"kasm-{zone_config["region"]}-subnet",
                                     ip_cidr_range=f"10.0.{zone_index}.0/24",
                                     region=f"{zone_config["region"]}",
                                     network=self.vpc.id,
                                     )
            self.additional_zone_subnet.append(subnet)

            # Additional Zone Cloud Router
            router = Router(f"kasm-{zone_config["region"]}-router",
                                 name=f"kasm-{zone_config["region"]}-router",
                                 network=self.vpc.id,
                                 region=zone_config["region"]
                                 )
            self.additional_zone_router.append(router)

            # Additional Zone Cloud NAT
            nat = RouterNat(f"kasm-{zone_config["region"]}-nat",
                                 name=f"kasm-{zone_config["region"]}-nat",
                                 router=router.name,
                                 nat_ip_allocate_option="AUTO_ONLY",
                                 source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",
                                 region=zone_config["region"],
                                 log_config={
                                     "enable": True,
                                     "filter": "ERRORS_ONLY"
                                 })
            self.additional_zone_nat.append(nat)

            # Additional Zone Public IP for GKE Ingress Load Balancer
            public_ip_address = GlobalAddress(f'kasm-{zone_config["name"]}-loadbalancer-public-ip', name=f'kasm-{zone_config["name"]}-loadbalancer-public-ip')
            self.additional_zone_public_ip_address.append(public_ip_address)
            pulumi.export(f"{zone_config["name"]}_ingress_loadbalancer", public_ip_address.address)


            proxy_public_ip_address = Address(f'kasm-{zone_config["name"]}-proxy-public-ip', name=f'kasm-{zone_config["name"]}-proxy-public-ip', region=zone_config["region"])
            self.additional_zone_proxy_vm_public_ip_address.append(proxy_public_ip_address)
            pulumi.export(f"{zone_config["name"]}-proxy-public-ip", proxy_public_ip_address.address)

