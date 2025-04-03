# Kasm GCP Deployment (Python)
This example automates the deployment of a **multi-zone Kasm** across Google Cloud Platform (GCP). The script sets up all necessary resources, including networking, PostgreSQL database, Kubernetes cluster, and Kasm agents and proxies for seamless deployment.

## Prerequisites

Before using the Pulumi script, ensure that the following requirements are met:

- **Pulumi**: Install [Pulumi](https://www.pulumi.com/docs/get-started/) to manage your infrastructure as code.
- **Python**: Ensure Python 3.6+ is installed on your machine.
- **GCP Account**: Ensure you have a Google Cloud Platform account with appropriate permissions to create resources.
- **Google Cloud SDK**: Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) to authenticate and configure your GCP environment.
- **Pulumi GCP Provider**: You will need to install the Pulumi GCP and Pulumi Kubernetes providers.


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
**region**: The GCP region for the primary Kasm zone. Example: `europe-west2`.
**zone**: The GCP zone for the primary Kasm zone. Example: `europe-west2-a`.
**agent_enable_ssh**: Set to `true` to enable SSH access for Kasm agent and proxy VMs, otherwise set to `false`.
**domain**: The domain to be used for the primary Kasm zone (e.g. `kasm.kasm-test.com`). The domain needs to be owned by you.
**agent_size**: The instance size for Kasm agents in the primary zone. Example: `e2-standard-4`.
**agent_number**: The number of Kasm agent instances to deploy in the primary zone. Example: `2`.
**agent_disk_size**: The disk size (in GB) for each Kasm agent instance across **all** zones. Example: `100`.
**cert**: Leave it as it is for Helm to generate. To use your own cert, run the command to set the value: `cat /path/to/cert.pem | pulumi config set --path data.cert --secret`
**cert_key**: Leave it as it is for Helm to generate. To use your own cert, run the command to set the value: `cat /path/to/cert.key | pulumi config set --path data.cert_key --secret`


### kasm-gcp:data.cloud_dns_zone
**create**: Set to `true` if you do not have a Cloud DNS zone already, the Pulumi script will create a new Cloud zone for you and you need to manually link your domain to this DNS zone. Set to `false` if you already have a cloud dns zone (thats already connected to your domain), the cloud dns will not be created, instead we will use the existing one.
**zone_name**: The name of the GCP Cloud DNS zone to be used (e.g., `kasm-test-com`). the config is only used when `create=false`
**zone_dns_name**: The GCP DNS name for the Cloud DNS zone (e.g., `kasm-test.com.`). the config is only used when `create=true`

### kasm-gcp:data.additional_kasm_zone
A list of additional Kasm zones to be deployed. Each zone will have its own set of configurations:
**name**: A unique identifier for each additional Kasm zone (e.g., `zoneb`, `zonec`).
**region**: The GCP region where the additional Kasm zone will be deployed (e.g., `europe-west1`). Each additional zone should reside in its own unique region.
**zone**: The GCP availability zone within the specified region for the additional Kasm zone (e.g., `europe-west1-b`).
**proxy_size**: The instance size for the Kasm proxy server in the additional zone. Example: `e2-standard-2`.
**agent_size**: The instance size for the Kasm agent servers in the additional zone. Example: `e2-standard-4`.
**agent_number**: The number of Kasm agent instances to be deployed in the additional zone. Example: `2`.
**domain**: The domain name for the additional Kasm zone. Example: `zoneb.kasm.kasm-test.com`.
**proxy_domain**: The domain name for the Kasm proxy server in the additional zone. Example: `proxy-zoneb.kasm.kasm-test.com`

## Pulumi Script Notes
1. postgres DB have the flag deletion_protection=False and deletion_protection_enabled=False, change this to true in gcp_db.py base on your preference
2. GKE cluster have the flag deletion_protection= False, change this in gcp_kubernetes.py based on your preference

## Execute Pulumi Script
Once you have finished configurating the Pulumi stack, use command `pulumi up --stack dev` to execute the Pulumi script. This script may take 20-30 minutes to complete.

Note: it can take up to 10 minutes for GCP to create the corresponding loadbanlancer for the ingress after the Pulumi script finished executing.

## Point Cloud Domain to the created DNS Zone
If you set `kasm-gcp:data.cloud_dns_zone.create=true`, you need to point you domain to the created GCP DNS zone. If you set `kasm-gcp:data.cloud_dns_zone.create=false` and your domain already pointed to the defined `kasm-gcp:data.cloud_dns_zone`, you can ignore this step.

## Config Kasm
Once you the Pulumi script is finished, you should be able to access your Kasm admin at https://{domain}
To get the login credentials, execute the command `pulumi stack output --show-secrets`, and use the values of `Kasm Admin User` and `Kasm Admin Password`

### Enable the Agent
In the Kasm admin console, select **Infrastructure > Docker Agents** and using the arrow menu select **Edit** on the agent you just created. Make sure **Enabled** is selected and click **Save**.

### Config Kasm Zone Proxy
In the Kasm admin console, select **Infrastructure > Docker Agents**

### Install a Workspace
In the Kasm admin console, select **Workspaces > Registry** and choose the workspace image you would like to install.

*Note: The agent may take a few minutes to download the selected workspace image before a session can be started.*

### Start A Kasm Session
Navigate to the **WORKSPACES** tab at the top of the page and start your first Kasm session once the workspace image is ready!




