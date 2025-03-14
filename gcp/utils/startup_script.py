import pulumi

def get_agent_startup_script(agent_swap_size, kasm_build_url, manager_url, manager_token):

    return pulumi.Output.all(agent_swap_size,
                             kasm_build_url,
                             manager_url,
                             manager_token
                             ).apply(lambda v: f"""#!/bin/bash
set -ex
echo "Starting Kasm Workspaces Agent Install"

## Create Swap partition
fallocate -l "{v[0]}"g /var/kasm.swap
chmod 600 /var/kasm.swap
mkswap /var/kasm.swap
swapon /var/kasm.swap
echo '/var/kasm.swap swap swap defaults 0 0' | tee -a /etc/fstab

cd /tmp

PRIVATE_IP=(`hostname -I | cut -d' ' -f1 | tr -d '\\n'`)

wget  {v[1]} -O kasm_workspaces.tar.gz
tar -xf kasm_workspaces.tar.gz

echo "Waiting for Kasm WebApp availability..."
while ! (curl -k https://{v[2]}/api/__healthcheck 2>/dev/null | grep -q true)
do
  echo "Waiting for API server..."
  sleep 5
done
echo "WebApp is alive"

bash kasm_release/install.sh -S agent -e -H -p $PRIVATE_IP -m {v[2]} -M {v[3]}

echo "Done"
"""
                                     )

def get_proxy_startup_script(domain, service_token, zone, cert, cert_key):

    return pulumi.Output.all(domain, service_token, zone, cert, cert_key).apply(lambda v: f"""#!/bin/bash
# If the directory does not exist, clone the repository
cd /tmp

if [ ! -d "/tmp/Kasm-Pulumi" ]; then
    git clone https://github.com/chenbishop/Kasm-Pulumi.git
fi

bash /tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/install.sh --domain "{v[0]}" --service-token "{v[1]}" --zone "{v[2]}" --cert "/tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs/server.crt" --cert_key "/tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs/server.key" 

sudo mkdir -p /tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs
sudo cat > /tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs/server.crt << EOL
{cert}
EOL

sudo cat > /tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs/server.key << EOL
{cert_key}
EOL

"""
                                     )
