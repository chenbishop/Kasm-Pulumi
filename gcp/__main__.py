from resources.gcp_networking import SetupGcpNetwork
from resources.gcp_db import SetupGcpDb
from resources.gcp_kubernetes import SetupGcpKubernetes
from resources.kasm_deployment import KasmDeployment
from resources.kasm_agent import SetupKasmAgent
from utils.password_generator import password_generator
from utils.startup_script import get_agent_startup_script, get_proxy_startup_script
from pulumi import Config

config = Config()
data = config.require_object("data")

# Setup GCP Network
gcp_network = SetupGcpNetwork()

# Create GCP postgres DB
db_password = password_generator(13)
gcp_db = SetupGcpDb(gcp_network, db_password)

# Crete GKE Cluster
# gcp_cluster = SetupGcpKubernetes(gcp_network)

# Deploy Kasm Helm
# kasm_helm = KasmDeployment(gcp_network, gcp_cluster.cluster_provider, gcp_db)

# Deploy Kasm Agents
# kasm_agent = SetupKasmAgent(gcp_network, kasm_helm, get_agent_startup_script, get_proxy_startup_script)