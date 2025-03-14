#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 --domain <domain_name> --service-token <service_token> --zone <zone> --cert-path <cert_path>"
    echo "  --domain        The domain name"
    echo "  --service-token The service token"
    echo "  --zone          The zone (e.g., us-east-1)"
    echo "  --cert-path     The path to the certificate file"
    exit 1
}

# Parse command-line options using getopt
TEMP=$(getopt -o '' --long domain:,service-token:,zone:,cert-path: -- "$@")
eval set -- "$TEMP"

# Default values
domain=""
service_token=""
zone=""
cert_path=""

# Process the options
while true; do
    case "$1" in
        --domain)
            domain="$2"
            shift 2
            ;;
        --service-token)
            service_token="$2"
            shift 2
            ;;
        --zone)
            zone="$2"
            shift 2
            ;;
        --cert-path)
            cert_path="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            usage
            ;;
    esac
done

# Check if all required fields are provided
if [ -z "$domain" ] || [ -z "$service_token" ] || [ -z "$zone" ] || [ -z "$cert_path" ]; then
    echo "Error: --domain, --service-token, --zone, and --cert-path are required!"
    usage
fi

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y



echo "Done."
