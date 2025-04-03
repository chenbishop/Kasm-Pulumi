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

sudo mkdir -p /tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs
sudo cat > /tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs/server.crt << EOL
{v[3]}
EOL

sudo cat > /tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs/server.key << EOL
{v[4]}
EOL

# setting up the proxy
bash /tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/install.sh --domain "{v[0]}" --service-token "{v[1]}" --zone "{v[2]}" --cert "/tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs/server.crt" --cert-key "/tmp/Kasm-Pulumi/additional_zone/dedicated_proxy/kasm-docker-compose/certs/server.key" 

"""
                                     )

def get_kasm_config_script():
    return """apt-get update -y;
apt-get install curl jq -y;
cat > kasm_config.sh << EOL
while true; do
  http_status=\$(curl -k -s -o /dev/null -w "%{http_code}" "https://\$URL");

  if (( http_status == 200 )); then
    echo "Site is up. Proceeding with the script...";
    break;
  else
    echo "Site not reachable. HTTP Status: \$http_status. Retrying in 5 seconds...";
    sleep 5;
  fi;
done;

KASM_TOKEN=\$(curl -s "https://\$URL/api/authenticate" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  --data-raw '{"username":"admin@kasm.local","password":"'"\$ADMIN_PASS"'","token":null}' | jq -r '.token');
  
if [ "\$KASM_TOKEN" == "null" ] || [ -z "\$KASM_TOKEN" ]; then
    echo "Error: Failed to retrieve the token."
    echo "Response: \$KASM_TOKEN"
    exit 2
fi
  
response=\$(curl "https://\$URL/api/admin/get_servers" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b "session_token=\$KASM_TOKEN" \
  --data-raw '{"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}');

while true; do
  server_count=\$(echo "\$response" | jq -r '.servers | length');

  # If the server count matches AGENT_NUMBER, break the loop
  if (( server_count == AGENT_NUMBER )); then
    break;
  fi;

  echo "Waiting for the servers array size to be \$AGENT_NUMBER (currently \$server_count)...";
  sleep 5;

  # Re-fetch the response in case it changes
  response=\$(curl "https://\$URL/api/admin/get_servers" \
    -k \
    -s \
    -H 'accept: application/json' \
    -H 'content-type: application/json' \
    -b "session_token=\$KASM_TOKEN" \
    --data-raw '{"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}');
done;

for server_id in \$(echo "\$response" | jq -r '.servers[].server_id'); do
  echo "Enabling agent server with ID: \$server_id";
  curl "https://\$URL/api/admin/update_server" \
    -k \
    -s \
    -H 'accept: application/json' \
    -H 'content-type: application/json' \
    -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
    --data-raw '{"target_server":{"server_type":"host","server_id":"'"\$server_id"'","enabled":true},"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}' \
    > /dev/null 2>&1;
done;

response=\$(curl "https://\$URL/api/admin/get_zones" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
  --data-raw '{"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}');

while true; do
  zone_count=\$(echo "\$response" | jq -r '.zones | length');

  if (( zone_count - 1 == ADDITIONAL_ZONES )); then
    break;
  fi;

  echo "Waiting for the zone array size to be  \$((ADDITIONAL_ZONES + 1)) (currently \$zone_count)...";
  sleep 5  # Wait for 5 seconds before checking again;

  # Re-fetch the response in case it changes
  response=\$(curl "https://\$URL/api/admin/get_zones" \
    -k \
    -s \
    -H 'accept: application/json' \
    -H 'content-type: application/json' \
    -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
    --data-raw '{"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}');
done;

echo "\$response" | jq -c '.zones[] | select(.zone_name != "default")' | while IFS= read -r zone; do
  zone_id=\$(echo "\$zone" | jq -r '.zone_id');
  zone_name=\$(echo "\$zone" | jq -r '.zone_name');
  eval UPSTREAM_AUTH_ADDRESS=\\\$\${zone_name}_UPSTREAM_AUTH_ADDRESS;
  eval PROXY_HOSTNAME=\\\$\${zone_name}_PROXY_HOSTNAME;
  
  echo "Updating zone with zone_id: \$zone_id, zone_name: \$zone_name";
  curl  "https://\$URL/api/admin/update_zone" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
  --data-raw '{"target_zone":{"upstream_auth_address":"'"\$UPSTREAM_AUTH_ADDRESS"'","proxy_hostname":"'"\$PROXY_HOSTNAME"'","proxy_rdp_hostname":"'"\$PROXY_HOSTNAME"'","zone_id":"'"\$zone_id"'"},"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}' \
      > /dev/null 2>&1;
done;

response=\$(curl "https://\$URL/api/admin/get_groups" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
  --data-raw '{"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}');
ALL_USER_GROUP_ID=\$(echo "\$response" | jq -r '.groups[] | select(.name == "All Users") | .group_id');

response=\$(curl "https://\$URL/api/admin/get_settings_group" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
  --data-raw '{"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}');
GROUP_SETTING_ID=\$(echo "\$response" | jq -r '.settings[] | select(.name == "allow_zone_selection")| .group_setting_id');

echo "Adding group setting id \$GROUP_SETTING_ID to group id \$ALL_USER_GROUP_ID";
curl  "https://\$URL/api/admin/add_settings_group" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
  --data-raw '{"target_group":{"group_id":"'"\$ALL_USER_GROUP_ID"'"},"target_setting":{"group_setting_id":"'"\$GROUP_SETTING_ID"'","value":"True"},"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}' \
      > /dev/null 2>&1;
EOL
chmod +x kasm_config.sh;
./kasm_config.sh;
"""
