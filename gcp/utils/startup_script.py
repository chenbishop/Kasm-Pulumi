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

for server_info in \$(echo "\$response" | jq -r '.servers[] | @base64'); do
  server_id=\$(echo \$server_info | base64 --decode | jq -r '.server_id')
  hostname=\$(echo \$server_info | base64 --decode | jq -r '.hostname')
  if [[ "\$AGENT_LIST" =~ "\$hostname" ]]; then
    echo "Enabling agent server with ID: \$server_id and hostname: \$hostname";
      curl "https://\$URL/api/admin/update_server" \
      -k \
      -s \
      -H 'accept: application/json' \
      -H 'content-type: application/json' \
      -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
      --data-raw '{"target_server":{"server_type":"host","server_id":"'"\$server_id"'","enabled":true},"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}' \
      > /dev/null 2>&1;
  else
    echo "Skipping server with with ID: \$server_id and hostname: \$hostname, not part of the pulumi deployment.";
  fi;
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

echo "Creating Kasm Server Pool"
response=\$(curl "https://\$URL/api/admin/create_server_pool" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
  --data-raw '{"target_server_pool":{"server_pool_name":"gcp_autoscaler_pool","server_pool_type":"Docker Agent"},"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}'); \
      > /dev/null 2>&1;
SERVER_POOL_ID=\$(echo "\$response" | jq -r '.server_pool.server_pool_id');
echo "Created Server Pool with ID: \$SERVER_POOL_ID"

echo "Creating Kasm Auto Scaling Config"
response=\$(curl "https://\$URL/api/admin/get_zones" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b "username=admin@kasm.local; session_token=\$KASM_TOKEN" \
  --data-raw '{"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}');
ZONE_INFO=\$(echo "\$response" | jq '{
  zones: [.zones[] | {
    zone_name: .zone_name,
    zone_id: .zone_id,
    total_memory_gb: (([.servers[].memory] | add) / 1073741824 | ceil),
    total_cores: ([.servers[].cores] | add),
    avg_memory_gb: (([.servers[].memory] | add) / (.servers | length) / 1073741824 | ceil),
    avg_memory_mb: (([.servers[].memory] | add) / (.servers | length) / 1048576 | ceil),
    avg_cores: (([.servers[].cores] | add) / (.servers | length) | ceil),
  }]
}');
echo \$ZONE_INFO

CERT_ESCAPED=\${CERT//\$'\\\\n'/\\\\\\\\n}
CERT_KEY_ESCAPED=\${CERT_KEY//\$'\\\\n'/\\\\\\\\n}

gcp_info=\$(echo "\$GCP_INFO")
agent_disk_size=\$(echo "\$gcp_info" | jq -r '.agent_disk_size')
network=\$(echo "\$gcp_info" | jq -r '.network')
project=\$(echo "\$gcp_info" | jq -r '.project')
image=\$(echo "\$gcp_info" | jq -r '.image')

echo "\$ZONE_INFO" | jq -c '.zones[]' | while read -r zone; do
  zone_name=\$(echo "\$zone" | jq -r '.zone_name')
  zone_id=\$(echo "\$zone" | jq -r '.zone_id')
  total_mem=\$(echo "\$zone" | jq -r '.total_memory_gb')
  total_cores=\$(echo "\$zone" | jq -r '.total_cores')
  avg_memory_gb=\$(echo "\$zone" | jq -r '.avg_memory_gb')
  avg_cores=\$(echo "\$zone" | jq -r '.avg_cores')
  avg_memory_mb=\$(echo "\$zone" | jq -r '.avg_memory_mb')
  
  response=\$(curl "https://\$URL/api/admin/create_autoscale_config" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b 'username="admin@kasm.local"; session_token="'"\$KASM_TOKEN"'"' \
  --data-raw '{"target_autoscale_config":{"enabled":false,"server_pool_id":"'"\$SERVER_POOL_ID"'","autoscale_type":"Docker Agent","autoscale_config_name":"'"\$zone_name"'-autoscale_config","zone_id":"'"\$zone_id"'","standby_cores":"'"\$avg_cores"'","standby_gpus":"0","standby_memory_mb":"'"\$avg_memory_mb"'","agent_cores_override":"'"\$avg_cores"'","agent_gpus_override":"0","agent_memory_override_gb":"'"\$avg_memory_gb"'","nginx_cert":"'"\$CERT_ESCAPED"'","nginx_key":"'"\$CERT_KEY_ESCAPED"'","downscale_backoff":"900"},"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}'); \
      > /dev/null 2>&1;
  autoscale_config_id=\$(echo "\$response" | jq -r '.autoscale_config.autoscale_config_id');
  echo "Autoscale config with id \$autoscale_config_id created for zone: \$zone_name with ID: \$zone_id"
  
  if [ "\$zone_name" != "default" ]; then
    zone_info=\$(echo "\$GCP_INFO" | jq -r --arg name "\$zone_name" '.["additional_zone"][0][] | select(.name == \$name)')
    subnet=\$(echo "\$zone_info" | jq -r '.subnet')
    agent_size=\$(echo "\$zone_info" | jq -r '.agent_size')
    region=\$(echo "\$zone_info" | jq -r '.region')
    zone=\$(echo "\$zone_info" | jq -r '.zone')
  else
    subnet=\$(echo "\$gcp_info" | jq -r '.subnet')
    max_instance=\$(echo "\$gcp_info" | jq -r '.["max_instance"]')
    agent_size=\$(echo "\$gcp_info" | jq -r '.agent_size')
    region=\$(echo "\$gcp_info" | jq -r '.region')
    zone=\$(echo "\$gcp_info" | jq -r '.zone')
  fi
  
  
  
  response=\$(curl "https://\$URL/api/admin/create_vm_provider_config" \
  -k \
  -s \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -b 'username="admin@kasm.local"; session_token="'"\$KASM_TOKEN"'"' \
  --data-raw '{"target_vm_provider_config":{"vm_provider_config_name":"'"\$zone_name"'_gcp_provider_config","vm_provider_name":"gcp","max_instances":"'"\$max_instance"'","vm_installed_os_type":"linux","startup_script_type":"startup-script","startup_script":"#\\u0021/usr/bin/env bash\\nset -ex\\nexport DEBIAN_FRONTEND=noninteractive\\n\\napt_wait () {{\\n  while sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1 ; do\\n    sleep 1\\n  done\\n  while sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 ; do\\n    sleep 1\\n  done\\n  if [ -f /var/log/unattended-upgrades/unattended-upgrades.log ]; then\\n    while sudo fuser /var/log/unattended-upgrades/unattended-upgrades.log >/dev/null 2>&1 ; do\\n      sleep 1\\n    done\\n  fi\\n}}\\n\\ninstall_xfce (){{\\n  apt-get install -y supervisor xfce4 xfce4-terminal xterm xclip\\n}}\\n\\ninstall_kasmvnc (){{\\n  cd /tmp\\n  KASM_VNC_PATH=/usr/share/kasmvnc\\n  BUILD_URL=\\"https://github.com/kasmtech/KasmVNC/releases/download/v1.3.3/kasmvncserver_focal_1.3.3_amd64.deb\\"\\n  KASM_VNC_PASSWD={connection_password}\\n  KASM_VNC_USER={connection_username}\\n  wget \\"\$BUILD_URL\\" -O kasmvncserver.deb\\n  apt-get install -y gettext ssl-cert libxfont2\\n  apt-get install -y /tmp/kasmvncserver.deb\\n  rm -f /tmp/kasmvncserver.deb\\n  ln -s \$KASM_VNC_PATH/www/index.html \$KASM_VNC_PATH/www/vnc.html\\n  cd /tmp\\n  mkdir -p \$KASM_VNC_PATH/www/Downloads\\n  chown -R 0:0 \$KASM_VNC_PATH\\n  chmod -R og-w \$KASM_VNC_PATH\\n  chown -R 1000:0 \$KASM_VNC_PATH/www/Downloads\\n  echo -e \\"\$KASM_VNC_PASSWD\\\\\\\\n\$KASM_VNC_PASSWD\\\\\\\\n\\" | kasmvncpasswd -u \$KASM_VNC_USER -w \\"/home/\$KASM_VNC_USER/.kasmpasswd\\"\\n  chown -R 1000:0 \\"/home/\$KASM_VNC_USER/.kasmpasswd\\"\\n  addgroup \$KASM_VNC_USER ssl-cert\\n  su -l -c \\"vncserver -select-de XFCE\\" \$KASM_VNC_USER\\n}}\\n\\ninstall_tigervnc (){{\\n  apt-get install -y tigervnc-standalone-server\\n  mkdir /home/ubuntu/.vnc\\n  echo \\"password123abc\\" | vncpasswd -f > /home/ubuntu/.vnc/passwd\\n  echo -e \\"#\\u0021/bin/sh\\\\\\\\nunset SESSION_MANAGER\\\\\\\\nunset DBUS_SESSION_BUS_ADDRESS\\\\\\\\nexec startxfce4\\" >> /home/ubuntu/.vnc/xstartup\\n  chown -R ubuntu:ubuntu /home/ubuntu/.vnc\\n  chmod 0600 /home/ubuntu/.vnc/passwd\\n  su -l -c \\"vncserver -localhost no\\" ubuntu\\n}}\\n\\napt_wait\\nsleep 10\\napt_wait\\napt-get update\\ninstall_xfce\\ninstall_kasmvnc\\n#install_tigervnc","gcp_project":"'"\$project"'","gcp_region":"'"\$region"'","gcp_zone":"'"\$zone"'","gcp_machine_type":"'"\$agent_size"'","gcp_image":"'"\$image"'","gcp_boot_volume_gb":"'"\$agent_disk_size"'","gcp_disk_type":"pd-ssd","gcp_network":"'"\$network"'","gcp_subnetwork":"'"\$subnet"'","gcp_network_tags":"","gcp_custom_labels":"","gcp_credentials":"","gcp_metadata":"","gcp_service_account":"","gcp_guest_accelerators":"","gcp_config_override":""},"token":"'"\$KASM_TOKEN"'","username":"admin@kasm.local"}'); \
      > /dev/null 2>&1;
  
done


EOL
chmod +x kasm_config.sh;
./kasm_config.sh;

sleep infinity;
"""
