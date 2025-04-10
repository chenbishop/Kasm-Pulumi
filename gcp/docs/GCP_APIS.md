# Required GCP APIs
The following GCP APIs must be enabled for the Pulumi script to function properly:

- `compute.googleapis.com` (Compute Engine)
- `container.googleapis.com` (Google Kubernetes Engine)
- `dns.googleapis.com` (Cloud DNS)
- `servicenetworking.googleapis.com` (Service Networking)
- `sqladmin.googleapis.com` (Cloud SQL Admin)

If `auto_enable_gcp_api=true` is set in the Pulumi stack configuration, the Pulumi script will automatically enable all of the APIs listed above in the specified GCP project. This requires one of the following permissions in the GCP project: `roles/owner`, `roles/editor` or `roles/serviceusage.serviceUsageAdmin`.
If `auto_enable_gcp_api` is set to `false`, the required GCP APIs must be enabled manually. You can enable the APIs either through the GCP Console or using the gcloud CLI, depending on your preference.

## Enabling GCP APIs via the GCP Console
1. Go to **APIs & services** for your project
2. On the Library page, click **Private APIs**. If you don't see the API listed, that means you haven't been granted access to enable the API.
3. Click the API you want to enable. If you need help finding the API, use the search field.
4. In the page that displays information about the API, click **Enable**.

## Enabling GCP APIs via the gcloud CLI
To enable these APIs using the gcloud command-line tool, run the following commands to enable them:

```bash
gcloud services enable sqladmin.googleapis.com --project {project_id}
gcloud services enable container.googleapis.com --project {project_id}
gcloud services enable dns.googleapis.com --project {project_id}
gcloud services enable servicenetworking.googleapis.com --project {project_id}
gcloud services enable sqladmin.googleapis.com --project {project_id}
```
Replace {project_id} with your GCP project ID.
