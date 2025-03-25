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
gcloud auth application-default login
```

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

### kasm-gcp:data.cloud_dns_zone
**create**: Set to `true` if you do not have a Cloud DNS zone already, the Pulumi script will create a new Cloud zone for you and you need to manually link your domain to this DNS zone. Set to `false` if you already have a cloud dns zone (thats already connected to your domain), the cloud dns will not be created, instead we will use the existing one.
**zone_name**: The name of the Cloud DNS zone to be used (e.g., `kasm-test-com`). the config is only used when `create=false`
**zone_dns_name**: The DNS name for the Cloud DNS zone (e.g., `kasm-test.com.`). the config is only used when `create=true`

### kasm-gcp:data.additional_kasm_zone
A list of additional Kasm zones to be deployed. Each zone will have its own set of configurations:
**name**: A unique name for each additional Kasm zone (e.g., `zoneb`, `zonec`).

**cloud_provider**: The cloud provider to use for the additional zone. Set to gcp for Google Cloud Platform.

**region**: The GCP region for the additional kasm zone (e.g., `europe-west1`).

**zone**: The GCP availability zone for the additional zone (e.g., `europe-west1-b`).

**proxy_size**: The instance size for Kasm proxies in the additional zone. Example: e2-standard-2.

**agent_size**: The instance size for Kasm agents in the additional zone. Example: `e2-standard-4`.
**agent_number**: The number of Kasm agent instances to deploy in the additional zone. Example: `2`.

domain: The domain name for the additional Kasm zone (e.g., zoneb.kasm.kasm-test.com).













Cert:
1. on default generate self sign cert but if you would like to use your own cert
2. cert: "Leave it as it is for Helm to generate. To use your own cert, run the command to set the value: `cat /path/to/cert.pem | pulumi config set --path data.cert --secret`"
3. key: "Leave it as it is for Helm to generate. To use your own cert, run the command to set the value: `cat /path/to/cert.key | pulumi config set --path data.cert_key --secret`"



pre-steps:
1. dns zone, if already have one, cloud_dns_zone.create set to false (default is true) and modify the cloud_dns_zone.zone_name and cloud_dns_zone.zone_dns_name
2. if dont have one, make sure cloud_dns_zone.create is true and modify cloud_dns_zone.zone_name and cloud_dns_zone.zone_dns_name and point your cloud domain to the created dns once the pulumi script finishes

additional:
1. postgres DB have the flag deletion_protection=False and deletion_protection_enabled=False, change this to true in gcp_db.py base on your preference
2. GKE cluster have the flag deletion_protection= False, change this in gcp_kubernetes.py based on your preference

Input:
1. agent_disk_size: in GB and recommend 100 GB


Service account permissions?