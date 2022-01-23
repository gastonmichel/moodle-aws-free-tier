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
    aws_ecr_assets as ecr_assets,
    aws_autoscaling as autoscaling,
    core as cdk
)

class MoodleApplicationStack(cdk.Stack):

    def __init__(
        self, scope: cdk.Construct, id: str, 
        vpc: ec2.Vpc,
        database: rds.CfnDBInstance,
        filesystem: efs.FileSystem,
        sessioncache: elasticache.CfnCacheCluster,
        **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.asg = autoscaling.AutoScalingGroup(
            self, 'MoodleASG',
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=ec2.SecurityGroup.from_security_group_id(
                self, 'DefaultSG',
                security_group_id=vpc.vpc_default_security_group,
            ),
            desired_capacity=1,
            min_capacity=1,
            max_capacity=1,
            instance_type=ec2.InstanceType(self.node.try_get_context('ecs_node_type')),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
        )

        self.capacity_provider = ecs.AsgCapacityProvider(
            self, 'MoodleAsgCapacityProvider',
            auto_scaling_group=self.asg,
        )

        self.ecs = ecs.Cluster(
            self, 'MoodleECSCluster',
            vpc=vpc,
            cluster_name='moodle-ecs-cluster',
            container_insights=True,
        )

        self.ecs.add_asg_capacity_provider(
            provider=self.capacity_provider,
        )

        # self.ecs.add_capacity("MoodleECSAutoScalingGroupCapacity",
        #     instance_type=ec2.InstanceType(self.node.try_get_context('ecs_node_type')),
        #     desired_capacity=1,
        #     min_capacity=1,
        #     max_capacity=1,
        #     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        # )
        # .add_security_group(
        #     security_group=ec2.SecurityGroup.from_security_group_id(
        #         self,'DefaultSG',
        #         vpc.vpc_default_security_group,
        #     )
        # )

        # define task execution role and attach ECSTaskExecutionRole managed policy
        self.task_role = iam.Role(self, "MoodleTaskExecutionRole", assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        self.task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"))
 
        self.volume = ecs.Volume(
            name='MoodleVolume',
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=filesystem.file_system_id,
                root_directory='/data'
            )
        )
        self.task = ecs.Ec2TaskDefinition(
            self, 'MoodleTaskDefinition',
            network_mode=ecs.NetworkMode.BRIDGE,
            task_role=self.task_role,
            volumes=[self.volume]
        )

        self.image = ecr_assets.DockerImageAsset(
            self, 'MoodleDockerImage',
            directory='./docker',
        )

        self.container = self.task.add_container(
            'MoodleContainer',
            image=ecs.ContainerImage.from_docker_image_asset(self.image),
            environment={
                'MOODLE_USERNAME': '', # Moodle application username. Default: user
                'MOODLE_PASSWORD': '', # Moodle application password. Default: bitnami
                'MOODLE_EMAIL': '', # Moodle application email. Default: user@example.com
                'MOODLE_SITE_NAME': '', # Moodle site name. Default: New Site
                'MOODLE_SKIP_BOOTSTRAP': '', # Do not initialize the Moodle database for a new deployment. This is necessary in case you use a database that already has Moodle data. Default: no
                'MOODLE_DATABASE_TYPE': '', # Database type. Valid values: mariadb, mysqli. Default: mariadb
                'MOODLE_DATABASE_HOST': '', # Hostname for database server. Default: mariadb
                'MOODLE_DATABASE_PORT_NUMBER': '', # Port used by database server. Default: 3306
                'MOODLE_DATABASE_NAME': '', # Database name that Moodle will use to connect with the database. Default: bitnami_moodle
                'MOODLE_DATABASE_USER': '', # Database user that Moodle will use to connect with the database. Default: bn_moodle
                'MOODLE_DATABASE_PASSWORD': '', # Database password that Moodle will use to connect with the database. No defaults.
                'ALLOW_EMPTY_PASSWORD': '', # It can be used to allow blank passwords. Default: no
                'MYSQL_CLIENT_FLAVOR': '', # SQL database flavor. Valid values: mariadb or mysql. Default: mariadb.
                'MYSQL_CLIENT_DATABASE_HOST': '', # Hostname for MariaDB server. Default: mariadb
                'MYSQL_CLIENT_DATABASE_PORT_NUMBER': '', # Port used by MariaDB server. Default: 3306
                'MYSQL_CLIENT_DATABASE_ROOT_USER': '', # Database admin user. Default: root
                'MYSQL_CLIENT_DATABASE_ROOT_PASSWORD': '', # Database password for the database admin user. No defaults.
                'MYSQL_CLIENT_CREATE_DATABASE_NAME': '', # New database to be created by the mysql client module. No defaults.
                'MYSQL_CLIENT_CREATE_DATABASE_USER': '', # New database user to be created by the mysql client module. No defaults.
                'MYSQL_CLIENT_CREATE_DATABASE_PASSWORD': '', # Database password for the MYSQL_CLIENT_CREATE_DATABASE_USER user. No defaults.
                'MYSQL_CLIENT_CREATE_DATABASE_CHARACTER_SET': '', # Character set to use for the new database. No defaults.
                'MYSQL_CLIENT_CREATE_DATABASE_COLLATE': '', # Database collation to use for the new database. No defaults.
                'MYSQL_CLIENT_CREATE_DATABASE_PRIVILEGES': '', # Database privileges to grant for the user specified in MYSQL_CLIENT_CREATE_DATABASE_USER to the database specified in MYSQL_CLIENT_CREATE_DATABASE_NAME. No defaults.
                'MYSQL_CLIENT_ENABLE_SSL_WRAPPER': '', # Whether to force SSL connections to the database via the mysql CLI tool. Useful for applications that rely on the CLI instead of APIs. Default: no
                'MYSQL_CLIENT_ENABLE_SSL': '', # Whether to force SSL connections for the database. Default: no
                'MYSQL_CLIENT_SSL_CA_FILE': '', # Path to the SSL CA file for the new database. No defaults
                'MYSQL_CLIENT_SSL_CERT_FILE': '', # Path to the SSL CA file for the new database. No defaults
                'MYSQL_CLIENT_SSL_KEY_FILE': '', # Path to the SSL CA file for the new database. No defaults
                'ALLOW_EMPTY_PASSWORD': '', # It can be used to allow blank passwords. Default: no
                'MOODLE_SMTP_HOST': '', # SMTP host.
                'MOODLE_SMTP_PORT': '', # SMTP port.
                'MOODLE_SMTP_USER': '', # SMTP account user.
                'MOODLE_SMTP_PASSWORD': '', # SMTP account password.
                'MOODLE_SMTP_PROTOCOL': '', # SMTP protocol.
                'PHP_ENABLE_OPCACHE': '', # Enable OPcache for PHP scripts. No default.
                'PHP_EXPOSE_PHP': '', # Enables HTTP header with PHP version. No default.
                'PHP_MAX_EXECUTION_TIME': '', # Maximum execution time for PHP scripts. No default.
                'PHP_MAX_INPUT_TIME': '', # Maximum input time for PHP scripts. No default.
                'PHP_MAX_INPUT_VARS': '', # Maximum amount of input variables for PHP scripts. No default.
                'PHP_MEMORY_LIMIT': '', # Memory limit for PHP scripts. Default: 256M
                'PHP_POST_MAX_SIZE': '', # Maximum size for PHP POST requests. No default.
                'PHP_UPLO`AD_MAX_FILESIZE': '', # Maximum file size for PHP uploads. No default.
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="moodle-ecs-fargate", 
                log_retention=logs.RetentionDays.FIVE_DAYS
            ),
            memory_reservation_mib=300,
        )

        # self.task.add_volume(
        #     name='MoodleVolume',
        #     efs_volume_configuration=ecs.EfsVolumeConfiguration(
        #         file_system_id=filesystem.file_system_id,
        #         root_directory='/data'
        #     )
        # )

        # self.container.add_mount_points(
        #     ecs.MountPoint(
        #         read_only=False,
        #         container_path='/var/www/moodle/data',
        #         source_volume=self.volume.name,
        #     )
        # )

        self.container.add_port_mappings(
            ecs.PortMapping(container_port=80)
        )

        # self.service = ecs.Ec2Service(
        #     self, 'MoodleService',
        #     cluster=self.ecs,
        #     task_definition=self.task,
        #     desired_count=1,
        #     # vpc_subnets={'subnet_type': ec2.SubnetType.PUBLIC},
        #     # security_groups=[ec2.SecurityGroup.from_security_group_id(self,'DefaultSG',vpc.vpc_default_security_group)],
        #     # health_check_grace_period=cdk.Duration.seconds(1200),
        #     min_healthy_percent=0,
        #     max_healthy_percent=200,
        #     enable_execute_command=True,
        # )


        # self.service.connections.allow_from(
        #     other=loadbalancer,
        #     port_range=ec2.Port.tcp(80)
        # )

        # self.http_listener = loadbalancer.add_listener(
        #     'MoodleHttpListener',
        #     port=80,
        # )

        # self.http_listener.add_targets(
        #     'MoodleHttpServiceTarget',
        #     protocol=elbv2.ApplicationProtocol.HTTP,
        #     targets=[self.service],
        #     # health_check=_elbv2.HealthCheck(healthy_http_codes="200-299,301,302",
        #     #     healthy_threshold_count=3,
        #     #     unhealthy_threshold_count=2,    
        #     #     interval=cdk.Duration.seconds(10),
        #     # )
        # )

        # cdk.CfnOutput(
        #     self, "MoodleLoadBalancerDNSName",
        #     value=loadbalancer.load_balancer_dns_name
        # )