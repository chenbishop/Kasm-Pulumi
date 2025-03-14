from pulumi import Config, ResourceOptions, Output, CustomTimeouts
from pulumi_gcp.compute import Instance
import pulumi

config = Config()
data = config.require_object("data")
gcp_config = Config("gcp")


class SetupKasmAgent:
    def __init__(self, gcp_network, kasm_helm, get_agent_startup_script, get_proxy_startup_script):
        agent_vm = []
        # GCP VM
        agent_startup_script = get_agent_startup_script(agent_swap_size=4,
                                            kasm_build_url="https://kasm-static-content.s3.amazonaws.com/kasm_release_1.16.1.98d6fa.tar.gz",
                                            manager_url= data.get("domain"),
                                            manager_token=kasm_helm.manager_token)
        for agent_index in range(1, int(data.get("agent_number"))+1):
            agent = Instance(f"kasm-agent-{agent_index}-vm-{data.get('region')}",
                               network_interfaces=[{
                                   "access_configs": [{}],
                                   "network": gcp_network.vpc.id,
                                   "subnetwork": gcp_network.subnet.id
                               }],
                               name=f"kasm-agent-{agent_index}-vm-{data.get('region')}",
                               machine_type=data.get("agent_size"),
                               zone=data.get("zone"),
                               boot_disk={
                                   "initialize_params": {
                                       "image": "ubuntu-2404-noble-amd64-v20250228",
                                       "size": 50,
                                   },
                               },
                               metadata_startup_script=agent_startup_script,
                               opts=ResourceOptions(
                                   depends_on=[kasm_helm.helm])
                               )
            agent_vm.append(agent)


        additional_zones = data.get("additional_kasm_zone")
        self.additional_zone_agents = {}
        self.additional_zone_proxies = []
        for zone_index in range(2, len(data.get("additional_kasm_zone"))+2):
            zone_config = additional_zones[zone_index-2]
            self.additional_zone_agents[zone_config["name"]] = []
            agent_startup_script = get_agent_startup_script(agent_swap_size=4,
                                                kasm_build_url="https://kasm-static-content.s3.amazonaws.com/kasm_release_1.16.1.98d6fa.tar.gz",
                                                manager_url= zone_config["domain"],
                                                manager_token=kasm_helm.manager_token)
            for agent_index in range(1, int(zone_config["agent_number"])+1):
                agent = Instance(f"kasm-agent-{zone_config["name"]}-{agent_index}-vm-{zone_config['region']}",
                                 network_interfaces=[{
                                     "access_configs": [{}],
                                     "network": gcp_network.vpc.id,
                                     "subnetwork": gcp_network.additional_zone_subnet[zone_index-2].id
                                 }],
                                 name=f"kasm-agent-{agent_index}-vm-{zone_config['region']}",
                                 machine_type=zone_config["agent_size"],
                                 zone=zone_config["zone"],
                                 boot_disk={
                                     "initialize_params": {
                                         "image": "ubuntu-2404-noble-amd64-v20250228",
                                         "size": 50,
                                     },
                                 },
                                 metadata_startup_script=agent_startup_script,
                                 opts=ResourceOptions(
                                     depends_on=[kasm_helm.helm])
                                 )
                self.additional_zone_agents[zone_config["name"]] .append(agent)

            proxy_startup_script = get_proxy_startup_script(zone_config["domain"], kasm_helm.service_token, zone_config["name"], kasm_helm.tls_crt, kasm_helm.tls_key)
            proxy = Instance(f"kasm-proxy-{zone_config["name"]}-vm-{zone_config['region']}",
                             network_interfaces=[{
                                 "access_configs": [{}],
                                 "network": gcp_network.vpc.id,
                                 "subnetwork": gcp_network.additional_zone_subnet[zone_index-2].id
                             }],
                             name=f"kasm-proxy-{zone_config["name"]}-vm-{zone_config['region']}",
                             machine_type=zone_config["proxy_size"],
                             zone=zone_config["zone"],
                             boot_disk={
                                 "initialize_params": {
                                     "image": "ubuntu-2404-noble-amd64-v20250228",
                                     "size": 50,
                                 },
                             },
                             metadata_startup_script=proxy_startup_script,
                             opts=ResourceOptions(
                                 depends_on=[kasm_helm.helm])
                             )
            self.additional_zone_proxies.append(proxy)




