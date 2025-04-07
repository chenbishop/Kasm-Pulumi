# Kasm GCP Deployment (Python)
This example automates the deployment of a **multi-zone Kasm** across Google Cloud Platform (GCP). The script sets up all necessary resources, including networking, PostgreSQL database, Kubernetes cluster, and Kasm agents and proxies for seamless deployment.

## Prerequisites

Before using the Pulumi script, ensure that the following requirements are met:

- **Pulumi**: Install [Pulumi](https://www.pulumi.com/docs/get-started/) to manage your infrastructure as code.
- **Python**: Ensure Python 3.6+ is installed on your machine.
- **GCP Account**: Ensure you have a Google Cloud Platform account with appropriate permissions to create resources.
- **Google Cloud SDK**: Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) to authenticate and configure your GCP environment.
- **Pulumi GCP Provider**: You will need to install the Pulumi GCP and Pulumi Kubernetes providers.

Further, You will need to have the following info ready before proceed further
- **Kasm Hosting Domain**: The domain where Kasm will be hosted, e.g., `kasm.kasm-test.com`.
- **GCP Project**: The GCP project where you want to deploy the Pulumi resources.
- **GCP Region**: The GCP region where Kasm will be hosted.
- **Additional Zones**: Decide if you'd like additional zones and specify their corresponding GCP region(s).
- **Agent**: Define the agent VM size and the number of agents for each Kasm zone.
- **Additional Zone DNS Name**: DNS name for the additional Kasm zone, e.g., `zoneb.kasm.kasm-test.com`.
- **Additional Zone Proxy DNS Name**: DNS name for the Kasm proxy in the additional zone, e.g., `proxy-zoneb.kasm.kasm-test.com`.
- **SSL Certificate**: Ensure you have an SSL certificate covering the following domains:
    - Kasm domain (e.g., `kasm.kasm-test.com`)
    - Additional zone DNS name (e.g., `zoneb.kasm.kasm-test.com` and `zonec.kasm.kasm-test.com`)
    - Additional zone proxy DNS name (e.g., `proxy-zoneb.kasm.kasm-test.com` and `proxy-zonec.kasm.kasm-test.com`)
- **Cloud DNS Creation**:
    - **If Yes**: If you want the Pulumi script to create Cloud DNS, you will need to point your domain to the created Cloud DNS after the script completes and provide your domain’s DNS name in the Pulumi configuration.
    - **If No**: If you do not want the Pulumi script to create Cloud DNS, you must provide the name of your existing GCP Cloud DNS.

## Authenticate with GCP
```bash
gcloud auth login
gcloud auth application-default login
```

Note: make sure both auth commands are passed.

## Clone Git repo
TODO: to be changed
```bash
git clone https://github.com/chenbishop/Kasm-Pulumi
cd Kasm-Pulumi
```

## Setup Python Environment
```bash
cd gcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Setup Pulumi Stack
```bash
pulumi stack init dev
cp Pulumi.dev.yaml.example Pulumi.dev.yaml
pulumi config set gcp:project <your-project-id>
```

## Config Pulumi Stack
Modify `Pulumi.dev.yaml` as follows:

### kasm-gcp:data
- **region**: The GCP region for the primary Kasm zone. Example: `europe-west2`.
- **zone**: The GCP zone for the primary Kasm zone. Example: `europe-west2-a`.
- **agent_enable_ssh**: Set to `true` to enable SSH access for Kasm agent and proxy VMs, otherwise set to `false`.
- **domain**: The domain to be used for the primary Kasm zone (e.g. `kasm.kasm-test.com`). The domain needs to be owned by you.
- **agent_size**: The instance size for Kasm agents in the primary zone. Example: `e2-standard-4`.
- **agent_number**: The number of Kasm agent instances to deploy in the primary zone. Example: `2`.
- **agent_disk_size**: The disk size (in GB) for each Kasm agent instance across **all** zones. Example: `100`.
- **db_tier**: The tier for the GCP PostgreSQL database is specified as `db-custom-{core_count}-{RAM_in_MB}`. We recommend using at least 2 cores and 3840 MB of RAM for optimal performance. For example, `db-custom-2-3840` represents a database tier with 2 CPU cores and 3840 MB of RAM.
- **cert**: Leave it as it is for Helm to generate. To use your own cert, run the command to set the value: `cat /path/to/cert.pem | pulumi config set --path data.cert --secret`
- **cert_key**: Leave it as it is for Helm to generate. To use your own cert, run the command to set the value: `cat /path/to/cert.key | pulumi config set --path data.cert_key --secret`

**Note**: We highly recommend using the following DNS structure for a multi-zone Kasm setup:
- Assume Kasm domain is `kasm.kasm-test.com`.
- Additional zone DNS names should be subdomains of the Kasm domain (e.g., `zoneb.kasm.kasm-test.com`).
- Additional zone proxy DNS names should also be subdomains of the Kasm domain (e.g., `proxy-zoneb.kasm.kasm-test.com`), at the same level as the additional zone DNS names.

The multi-zone setup must have a valid SSL certificate, and the provided certificate must cover all of the following:
- Kasm domain (e.g., `kasm.kasm-test.com`)
- Additional zone DNS names (e.g., `zoneb.kasm.kasm-test.com`, `zonec.kasm.kasm-test.com`)
- Additional zone proxy DNS names (e.g., `proxy-zoneb.kasm.kasm-test.com`, `proxy-zonec.kasm.kasm-test.com`)

### kasm-gcp:data.cloud_dns_zone
- **create**: Set to `true` if you do not have a Cloud DNS zone already, the Pulumi script will create a new Cloud zone for you and you need to manually link your domain to this DNS zone. Set to `false` if you already have a cloud dns zone (thats already connected to your domain), the cloud dns will not be created, instead we will use the existing one.
- **zone_name**: The name of the GCP Cloud DNS zone to be used (e.g., `kasm-test-com`). the config is only used when `create=false`
- **zone_dns_name**: The GCP DNS name for the Cloud DNS zone (e.g., `kasm-test.com.`). the config is only used when `create=true`

### kasm-gcp:data.additional_kasm_zone
A list of additional Kasm zones to be deployed. Each zone will have its own set of configurations:
- **name**: A unique identifier for each additional Kasm zone (e.g., `zoneb`, `zonec`).
- **region**: The GCP region where the additional Kasm zone will be deployed (e.g., `europe-west1`). Each additional zone should reside in its own unique region.
- **zone**: The GCP availability zone within the specified region for the additional Kasm zone (e.g., `europe-west1-b`).
- **proxy_size**: The instance size for the Kasm proxy server in the additional zone. Example: `e2-standard-2`.
- **agent_size**: The instance size for the Kasm agent servers in the additional zone. Example: `e2-standard-4`.
- **agent_number**: The number of Kasm agent instances to be deployed in the additional zone. Example: `2`.
- **domain**: The domain name for the additional Kasm zone. Example: `zoneb.kasm.kasm-test.com`.
- **proxy_domain**: The domain name for the Kasm proxy server in the additional zone. Example: `proxy-zoneb.kasm.kasm-test.com`

## Pulumi Script Notes
1. By default, the GCP Cloud PostgreSQL database has a disk size of 10GB, with `automatic storage increase` enabled. This allows GCP to manage the database size automatically. If you'd like to modify this behavior, you can manually adjust the settings in the `gcp_db.py` script.
2. The GCP Cloud PostgreSQL database has the flags `deletion_protection=False` and `deletion_protection_enabled=False`. You can change these to `True` in the `gcp_db.py` script based on your preference.
2. The GKE cluster has the flag `deletion_protection=False`. You can update this value in the `gcp_kubernetes.py` script according to your preference.

## Execute Pulumi Script
Once you have finished configuring the Pulumi stack, use command `pulumi up --stack dev` to execute the Pulumi script. This script may take 20-30 minutes to complete.

**Note**: It may take up to 10 minutes for GCP to provision the load balancer for the ingress after the Pulumi script completes execution. Kasm will not be accessible until the ingress load balancer is fully created.

## Point Cloud Domain to the created DNS Zone
If you set `kasm-gcp:data.cloud_dns_zone.create=true`, you need to point you domain to the created GCP DNS zone. If you set `kasm-gcp:data.cloud_dns_zone.create=false` and your domain already pointed to the defined `kasm-gcp:data.cloud_dns_zone`, you can ignore this step.

## Login Kasm
Once you the Pulumi script is finished, you should be able to access your Kasm admin at https://{domain}
To get the login credentials, execute the command `pulumi stack output --show-secrets`, and use the values of `Kasm Admin User` and `Kasm Admin Password`

## Install a Kasm Workspace
In the Kasm admin console, select **Workspaces > Registry** and choose the workspace image you would like to install.

*Note: The agent may take a few minutes to download the selected workspace image before a session can be started.*

## Start A Kasm Session
Navigate to the **WORKSPACES** tab at the top of the page and start your first Kasm session once the workspace image is ready!

## Accessing Your GKE Cluster with kubectl
Once the Pulumi script is completed, follow these steps to access your GKE cluster using kubectl.

### Configure kubectl to Use the Cluster Credentials
Run the following command to retrieve the credentials for your GKE cluster:
```bash
gcloud container clusters get-credentials kasm-cluster --region={GCP Region}
```
Replace {GCP Region} with the region where your Kasm primary zone is configured. This command sets up kubectl to use the necessary credentials for interacting with your cluster.

### Verify Cluster Access
After configuring kubectl, you can start querying your GKE cluster. For instance, to list the pods in the kasm namespace, use:
```bash
kubectl -n kasm get pods
```


## Created Pulumi Resources
### GCP Networking
The table below provides an overview of the GCP network-related resources that are created:

| **Resource Type**    | **Summary**                                                                                                                                                         |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **VPC**              | Virtual Private Cloud (VPC) that hosts all compute instances and networking resources.                                                                              |
| **Subnet**           | Subnets for the primary zone and one for each additional zone.                                                                                                      |
| **Router**           | Cloud Router deployed for the primary zone and each additional zone.                                                                                                |
| **RouterNat**        | Cloud NAT for outbound traffic in the primary zone and each additional zone to enable instances to access the internet.                                             |
| **Firewall**         | Firewall rules for SSH access (if `vm_enable_ssh=true`) and HTTPS traffic.                                                                                          |
| **ManagedZone**      | Private DNS zone for the database and public DNS zone (if `cloud_dns_zone=true`) for Kasm ingress load balancers and proxies for additional zones.                  |
| **GlobalAddress**    | Public IP addresses for ingress load balancers (one per zone), Kasm proxies (one per additional zone), and an internal IP for the database.                         |
| **RecordSet**        | DNS recordset for ingress load balancer addresses and Kasm proxy VM addresses in the public zone, and DB record set in the private zone for internal communication. |
| **Connection**       | Cloud PostgreSQL connection to the VPC for database access within the VPC.                                                                                          |

### Other GCP Resources
The table below provides an overview of the GCP resources that are created, which are not part of the previous table:

| **Resource Type**    | **Summary**                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| **DatabaseInstance** | GCP PostgreSQL instance.                                                    |
| **SQL User**         | A user created within the PostgreSQL instance for database access.          |
| **Database**         | PostgreSQL database within the created PostgreSQL instance.                 |
| **Cluster**          | GKE Autopilot cluster, used to host the Kasm Helm chart.                    |
| **Instance**         | GCP VM instances hosting Kasm agents and Kasm proxies for additional zones. |



### No GCP Resources
The table below provides an overview of the non-GCP resources that are created:

| **Resource Type**     | **Summary**                                                                           |
|-----------------------|---------------------------------------------------------------------------------------|
| **Provider**          | Kubernetes provider used by Pulumi to communicate with the created GKE cluster.       |
| **Release**           | Kasm Helm chart deployed into the created GKE cluster for hosting Kasm services.      |
| **Job**               | Kubernetes job for configuring Kasm, including enabling agents and other setup tasks. |


## Delete Pulumi Stack
To delete the created Pulumi stack along with all the associated resources, run the following command:

```bash
pulumi down --stack dev
```

**Note**: Due to a limitation with GCP's Network Endpoint Group (NEG), you may encounter the following error during pulumi down:
```bas
sdk-v2/provider2.go:515: sdk.helper_schema: Error waiting for Deleting Network: The network resource 'projects/xxx/global/networks/kasm' is already being used by 'projects/xxx/zones/xxx/networkEndpointGroups/xxx'
```
If this occurs, manually delete the NEG(s) associated with the kasm VPC network in your GCP project and then re-run `pulumi down`.

