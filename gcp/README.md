# Kasm GCP Deployment (Python)
This example automates the deployment of a **multi-zone Kasm** across Google Cloud Platform (GCP). The script sets up all necessary resources, including networking, PostgreSQL database, Kubernetes cluster, and Kasm agents and proxies for seamless deployment.

## Prerequisites

Before using the Pulumi script, ensure that the following requirements are met:

- **Pulumi**: Install [Pulumi](https://www.pulumi.com/docs/get-started/) to manage your infrastructure as code.
- **Python**: Ensure Python 3.6+ is installed on your machine.
- **GCP Account**: Ensure you have a Google Cloud Platform account with appropriate permissions to create resources.
- **Google Cloud SDK**: Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) to authenticate and configure your GCP environment.
- **Pulumi GCP Provider**: You will need to install the Pulumi GCP and Pulumi Kubernetes providers.




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