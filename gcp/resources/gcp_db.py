from pulumi_gcp.sql import DatabaseInstance, DatabaseInstanceSettingsArgs, DatabaseInstanceSettingsIpConfigurationArgs, \
    DatabaseInstanceSettingsDatabaseFlagArgs
from pulumi import Config, ResourceOptions
from pulumi_gcp.dns import RecordSet
from pulumi_gcp import sql
import pulumi


config = Config()
data = config.require_object("data")


class SetupGcpDb:
    def __init__(self, gcp_network, db_password):
        # Create DB instance
        self.db_instance = DatabaseInstance(f"kasm-db-instance",
                                            name=f"kasm-db",
                                            database_version="POSTGRES_14",
                                            deletion_protection=False,
                                            region=data.get("region"),
                                            settings=DatabaseInstanceSettingsArgs(
                                                tier="db-g1-small",
                                                ip_configuration=DatabaseInstanceSettingsIpConfigurationArgs(
                                                    # TODO: to be disabled, remove line exporting this too
                                                    ipv4_enabled=True,
                                                    private_network=gcp_network.vpc.id,
                                                    enable_private_path_for_google_cloud_services=True,
                                                ),
                                                database_flags=[DatabaseInstanceSettingsDatabaseFlagArgs(
                                                    name="max_connections",
                                                    value="1000"
                                                )],
                                                deletion_protection_enabled=False
                                            ),
                                            opts=ResourceOptions(
                                                depends_on=[gcp_network.private_vpc_connection],
                                                ignore_changes=["settings"]))

        # Create record set for DB instance
        self.db_record_set = RecordSet(f"kasm-db-recordset",
                                       # name=f"db.{data.get('dns_name')}.",
                                       name=f"db.kasm.int.",
                                       type="A",
                                       ttl=300,
                                       managed_zone=gcp_network.private_zone.name,
                                       rrdatas=[self.db_instance.private_ip_address])

        self.kasm_user = sql.User("kasm-db-user",
                                      instance=self.db_instance.name,
                                      name="kasmapp",
                                      password=db_password,
                                      opts=ResourceOptions(
                                          depends_on=[self.db_instance],
                                          ignore_changes=["password"]))

        self.kasm_db = sql.Database("kasm-db",
                                              name="kasm",
                                              instance=self.db_instance.name,
                                              opts=ResourceOptions(
                                                  depends_on=[self.db_instance, self.kasm_user]))

        # TODO: to be removed
        pulumi.export("kasm_db_public_ip", self.db_instance.ip_addresses[0].ip_address)

        pulumi.export("kasm_db_name", "kasm")
        pulumi.export("kasm_db_user", "kasmapp")
        pulumi.export("kasm_db_user_password", self.kasm_user.password)