#!/usr/bin/env python3
import os
from sys import version

from aws_cdk import (
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_iam as iam,
    aws_rds as rds,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_efs as efs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_logs as logs,
    core as cdk
)
from aws_cdk.aws_elasticloadbalancingv2 import ApplicationProtocol

class MoodleStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs):
        super().__init__(scope=scope, id=id, **kwargs)

        self.vpc = ec2.Vpc(
            self, 'MoodleVpc',
            cidr='10.0.0.0/16',
            max_azs=2,
            nat_gateways=0,
        )

        redisSubnetGroup = elasticache.CfnSubnetGroup(
            self,'RedisSubnetGroup',
            description='subnet group for redis cluster',
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.isolated_subnets],
            cache_subnet_group_name='moodle-redis-subnet-group'
        )

        self.redisCluster = elasticache.CfnCacheCluster(
            self, 'RedisCluster',
            cache_node_type=self.node.try_get_context('redis_node_type'),
            engine='Redis',
            num_cache_nodes=1,
            az_mode='single-az',
            cache_subnet_group_name=redisSubnetGroup.cache_subnet_group_name,
            cluster_name='moodle-redis-session-cache',
            engine_version='6.x',
            vpc_security_group_ids=[self.vpc.vpc_default_security_group],
            preferred_availability_zone='us-east-1a'
        )
        self.redisCluster.add_depends_on(redisSubnetGroup)

        rdsSubnetGroup = rds.CfnDBSubnetGroup(
            self, 'RDSSubnetGroup',
            db_subnet_group_description='subnet group for rds instance',
            db_subnet_group_name='moodle-rds-subnet-group',
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.isolated_subnets],
        )

        # self.rdsDatabase = rds.DatabaseInstance(
        #     self, "RDSInstance",
        #     engine=rds.DatabaseInstanceEngine.mysql(
        #         version=rds.MysqlEngineVersion.VER_8_0_23
        #     ),
        #     instance_type=ec2.InstanceType(self.node.try_get_context('rds_node_type')),
        #     database_name='moodle-sql-db',
        #     vpc=self.vpc,
        #     subnet_group=rdsSubnetGroup,
        #     # vpc_subnets = {'subnet_type': ec2.SubnetType.ISOLATED},
        #     security_groups=[ec2.SecurityGroup.from_security_group_id(self, 'defaultSG',self.vpc.vpc_default_security_group)],
        #     multi_az=False,
        #     availability_zone='us-east-1a',
        # )
        self.rdsDatabase = rds.CfnDBInstance(
            self, 'RDSDBInstance',
            # db_instance_identifier='moodle-sql-db',
            db_name='moodledb',
            db_instance_class=self.node.try_get_context('rds_node_type'),
            allocated_storage='20',
            availability_zone='us-east-1a',
            db_subnet_group_name=rdsSubnetGroup.db_subnet_group_name,
            engine='mysql',
            engine_version='8.0.23',
            master_username='admin',
            master_user_password=self.node.try_get_context('rds_admin_password'),
            multi_az=False,
            vpc_security_groups=[self.vpc.vpc_default_security_group],
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
        self.rdsDatabase.add_depends_on(rdsSubnetGroup)
        
        self.ecsCluster = ecs.Cluster(
            self, "ECSCluster",
            vpc=self.vpc,
            cluster_name='moodle-ecs-cluster',
            container_insights=True,
        )

        self.ecsCluster.add_capacity("MoodleAutoScalingGroupCapacity",
            instance_type=ec2.InstanceType(self.node.try_get_context('ecs_node_type')),
            desired_capacity=1,
            min_capacity=1,
            max_capacity=1,
            auto_scaling_group_name='moodle-asg',
            vpc_subnets={'subnet_type': ec2.SubnetType.PUBLIC},
            
        )

        file_system = efs.FileSystem(self, "MoodleFileSystem",
            vpc=self.vpc,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_14_DAYS, # files are not transitioned to infrequent access (IA) storage by default
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            vpc_subnets={'subnet_type': ec2.SubnetType.ISOLATED},
            throughput_mode=efs.ThroughputMode.BURSTING
        )

        volume = ecs.Volume(
            name='moodle-efs',
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=file_system.file_system_id
            )
        )

        task_definition = ecs.Ec2TaskDefinition(
            self, "MoodleTaskDefinition",
            network_mode=ecs.NetworkMode.AWS_VPC,
            volumes=[volume],
        )

        task_definition.node.add_dependency(file_system)

        container = task_definition.add_container("MoodleContainer",
            # image=ecs.ContainerImage.from_asset('./docker'),
            image=ecs.ContainerImage.from_registry('moodlehq/moodle-php-apache:7.4'),
            # cpu=1000,
            # health_check=ecs.HealthCheck(
            #     command=['php','./report/status/index.php'],
            #     interval=cdk.Duration.seconds(60),
            #     start_period=cdk.Duration.seconds(120),
            #     timeout=cdk.Duration.seconds(10)
            #     ),
            memory_limit_mib=500,
            environment={
                'DB_TYPE': 'mysql',
                'DB_HOST': self.rdsDatabase.attr_endpoint_address,
                'MOODLE_DB_PORT': self.rdsDatabase.attr_endpoint_port,
                'DB_NAME': 'moodledb',
                'DB_USER': 'admin',
                'DB_PASS': self.node.try_get_context('rds_admin_password'),
                'WEB_HOST': 'https://35.170.245.46',
                'REDIS_HOST': self.redisCluster.attr_redis_endpoint_address,
                'REDIS_PORT': self.redisCluster.attr_redis_endpoint_port
            },
            logging=ecs.LogDriver.aws_logs(stream_prefix='moodle-ecs-ec2', log_retention=logs.RetentionDays.FIVE_DAYS)
        )


        container.add_mount_points(ecs.MountPoint(
            read_only=False,
            container_path='/var/moodle',
            source_volume=volume.name,
        ))

        container.add_port_mappings(ecs.PortMapping(container_port=80))


        lbsg = ec2.SecurityGroup(
            self, 'MoodleLoadBalancerSG',
            vpc=self.vpc,
            allow_all_outbound=False,
        )
        lbsg.add_egress_rule(
            ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description='Allow outbound 80'
        )

        self.lb = elbv2.ApplicationLoadBalancer(
            self, 'MoodleLoadBalancer',
            vpc=self.vpc,
            internet_facing=True,
            security_group=lbsg,
            vpc_subnets={'subnet_type': ec2.SubnetType.PUBLIC}
        )
        service = ecs.Ec2Service(
            self, "MoodleService",
            cluster=self.ecsCluster,
            task_definition=task_definition,
            desired_count=1,
            health_check_grace_period=cdk.Duration.seconds(900),
            enable_execute_command=True,
        )

        # service.connections.allow_to(other=self.rdsDatabase, port_range=ec2.Port.tcp(3306))
        # service.connections.allow_to(other=file_system,port_range=ec2.Port.tcp(file_system.DEFAULT_PORT))
        service.connections.allow_from(other=self.lb, port_range=ec2.Port.tcp(80))
        http_listener = self.lb.add_listener(
            'MoodleHttpListener',
            port=80,

        )
        http_listener.add_targets(
            'MoodleHttpServiceTarget',
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[service],
            health_check=elbv2.HealthCheck(
                healthy_http_codes='200-299,301,302',
                healthy_threshold_count=3,
                unhealthy_threshold_count=2,
                interval=cdk.Duration.seconds(10)),
            
        )

        # load_balanced_ecs_service = ecs_patterns.ApplicationLoadBalancedEc2Service(
        #     self, "MoodleLoadBalancedService",
        #     cluster=self.ecsCluster,
        #     memory_limit_mib=501,
        #     task_definition=task_definition,
        #     desired_count=1,
        #     # redirect_http=True,
        #     # target_protocol=elbv2.ApplicationProtocol.HTTPS,
        #     service_name='moodle-ecs-service',
        #     # listener_port=
        # )
        # ecs_service = ecs_patterns.NetworkLoadBalancedEc2Service(
        #     self, "Ec2Service",
        #     cluster=self.ecsCluster,
        #     memory_limit_mib=512,
        #     task_definition=task_definition,
        #     # listener_port=80,
        # )




app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context('cdk_default_account'),
    region=app.node.try_get_context('cdk_default_region'),
)


MoodleStack(app,'MoodleStack',env=env)

app.synth()