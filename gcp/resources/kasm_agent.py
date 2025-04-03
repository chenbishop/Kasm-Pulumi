from pulumi import Config, ResourceOptions, Output, CustomTimeouts
from pulumi_gcp.compute import Instance
import pulumi

config = Config()
data = config.require_object("data")
gcp_config = Config("gcp")


class SetupKasmAgent:
    def __init__(self, gcp_network, kasm_helm, get_agent_startup_script, get_proxy_startup_script):

        # Get the Agent Startup script
        agent_startup_script = get_agent_startup_script(agent_swap_size=4,
                                            kasm_build_url="https://kasm-static-content.s3.amazonaws.com/kasm_release_1.16.1.98d6fa.tar.gz",
                                            manager_url= data.get("domain"),
                                            manager_token=kasm_helm.manager_token)

        # Create Agent VMs For The Primary Zone
        self.agent_vm = []
        for agent_index in range(1, int(data.get("agent_number"))+1):
            agent = Instance(f"kasm-primary-zone-agent-{agent_index}",
                               network_interfaces=[{
                                   "access_configs": [{}],
                                   "network": gcp_network.vpc.id,
                                   "subnetwork": gcp_network.subnet.id
                               }],
                               name=f"kasm-primary-zone-agent-{agent_index}",
                               machine_type=data.get("agent_size"),
                               zone=data.get("zone"),
                               boot_disk={
                                   "initialize_params": {
                                       "image": "ubuntu-2404-noble-amd64-v20250228",
                                       "size": data.get("agent_disk_size"),
                                   },
                               },
                               metadata_startup_script=agent_startup_script,
                               opts=ResourceOptions(
                                   depends_on=[kasm_helm.helm])
                               )
            self.agent_vm.append(agent)


        additional_zones = data.get("additional_kasm_zone")
        self.additional_zone_agents = {}
        self.additional_zone_proxies = []
        for zone_index in range(2, len(data.get("additional_kasm_zone"))+2):
            # Create Agent VMs For Additional Zones
            zone_config = additional_zones[zone_index-2]
            self.additional_zone_agents[zone_config["name"]] = []
            agent_startup_script = get_agent_startup_script(agent_swap_size=4,
                                                kasm_build_url="https://kasm-static-content.s3.amazonaws.com/kasm_release_1.16.1.98d6fa.tar.gz",
                                                manager_url= zone_config["domain"],
                                                manager_token=kasm_helm.manager_token)
            for agent_index in range(1, int(zone_config["agent_number"])+1):
                agent = Instance(f"kasm-{zone_config["name"]}-agent-{agent_index}",
                                 name=f"kasm-{zone_config["name"]}-agent-{agent_index}",
                                 network_interfaces=[{
                                     "access_configs": [{}],
                                     "network": gcp_network.vpc.id,
                                     "subnetwork": gcp_network.additional_zone_subnet[zone_index-2].id
                                 }],
                                 machine_type=zone_config["agent_size"],
                                 zone=zone_config["zone"],
                                 boot_disk={
                                     "initialize_params": {
                                         "image": "ubuntu-2404-noble-amd64-v20250228",
                                         "size": data.get("agent_disk_size"),
                                     },
                                 },
                                 metadata_startup_script=agent_startup_script,
                                 opts=ResourceOptions(
                                     depends_on=[kasm_helm.helm])
                                 )
                self.additional_zone_agents[zone_config["name"]] .append(agent)

            # Create Proxy VM For Additional Zones
            proxy_startup_script = get_proxy_startup_script(data.get("domain"), kasm_helm.service_token, zone_config["name"], kasm_helm.tls_crt, kasm_helm.tls_key)
            proxy = Instance(f"kasm-{zone_config["name"]}-proxy",
                             name=f"kasm-{zone_config["name"]}-proxy",
                             network_interfaces=[{
                                 "access_configs":  [{
                                     "nat_ip": gcp_network.additional_zone_proxy_vm_public_ip_address[zone_index-2].address,
                                 }],
                                 "network": gcp_network.vpc.id,
                                 "subnetwork": gcp_network.additional_zone_subnet[zone_index-2].id,
                             }],
                             machine_type=zone_config["proxy_size"],
                             zone=zone_config["zone"],
                             boot_disk={
                                 "initialize_params": {
                                     "image": "ubuntu-2404-noble-amd64-v20250228",
                                     "size": 50,
                                 },
                             },
                             metadata_startup_script=proxy_startup_script,
                             can_ip_forward=True,
                             opts=ResourceOptions(
                                 depends_on=[kasm_helm.helm, kasm_helm.kasm_secrets])
                             )
            self.additional_zone_proxies.append(proxy)
