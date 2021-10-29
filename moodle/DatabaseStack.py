from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    core as cdk
)

class MoodleDatabaseStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, vpc: ec2.Vpc, **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.db_subnet_group = rds.CfnDBSubnetGroup(
            self, 'MoodleDBSubnetGroup',
            db_subnet_group_description='subnet group for rds instance',
            db_subnet_group_name='moodle-rds-subnet-group',
            subnet_ids=[subnet.subnet_id for subnet in vpc.isolated_subnets],
        )

        self.db_instance = rds.CfnDBInstance(
            self, 'MoodleDBInstance',
            # db_instance_identifier='moodle-sql-db',
            db_name='moodledb',
            db_instance_class=self.node.try_get_context('rds_node_type'),
            allocated_storage='20',
            availability_zone='us-east-1a',
            db_subnet_group_name=self.db_subnet_group.db_subnet_group_name,
            engine='mysql',
            engine_version='8.0.23',
            master_username='admin',
            master_user_password=self.node.try_get_context('rds_admin_password'),
            multi_az=False,
            vpc_security_groups=[vpc.vpc_default_security_group],
            storage_type='gp2',
            publicly_accessible=False,
            # allow_major_version_upgrade=allow_major_version_upgrade,
            # associated_roles=associated_roles,
            # auto_minor_version_upgrade=auto_minor_version_upgrade,
            # backup_retention_period=backup_retention_period,
            # ca_certificate_identifier=ca_certificate_identifier,
            # character_set_name=character_set_name,
            # copy_tags_to_snapshot=copy_tags_to_snapshot,
            # db_cluster_identifier=db_cluster_identifier,
            # db_parameter_group_name=db_parameter_group_name,
            # db_security_groups=db_security_groups,
            # db_snapshot_identifier=db_snapshot_identifier,
            # delete_automated_backups=delete_automated_backups,
            # deletion_protection=deletion_protection,
            # domain=domain,
            # domain_iam_role_name=domain_iam_role_name,
            # enable_cloudwatch_logs_exports=enable_cloudwatch_logs_exports,
            # enable_iam_database_authentication=enable_iam_database_authentication,
            # enable_performance_insights=enable_performance_insights,
            # iops=iops,
            # kms_key_id=kms_key_id,
            # license_model=license_model,
            # max_allocated_storage=max_allocated_storage,
            # monitoring_interval=monitoring_interval,
            # monitoring_role_arn=monitoring_role_arn,
            # option_group_name=option_group_name,
            # performance_insights_kms_key_id=performance_insights_kms_key_id,
            # performance_insights_retention_period=performance_insights_retention_period,
            # port=port,
            # preferred_backup_window=preferred_backup_window,
            # preferred_maintenance_window=preferred_maintenance_window,
            # processor_features=processor_features,
            # promotion_tier=promotion_tier,
            # source_db_instance_identifier=source_db_instance_identifier,
            # source_region=source_region,
            # storage_encrypted=storage_encrypted,
            # tags=tags,
            # timezone=timezone,
            # use_default_processor_features=use_default_processor_features,
        )
        self.db_instance.add_depends_on(self.db_subnet_group)
        