from ast import Load
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
    aws_ses as ses,
    core as cdk
)
from . import (
    VPCStack,
    DatabaseStack,
    FileSystemStack,
    LoadBalancerStack,
)

class MoodleApplicationStack(cdk.Stack):

    def __init__(
        self, scope: cdk.Construct, id: str, 
        vpc: VPCStack.MoodleVPCStack,
        database: DatabaseStack.MoodleDatabaseStack,
        filesystem: FileSystemStack.MoodleFileSystemStack,
        loadbalancer: LoadBalancerStack.MoodleLoadBalancerStack,
        **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.asg = autoscaling.AutoScalingGroup(
            self, 'MoodleASG',
            vpc=vpc.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            # security_group=ec2.SecurityGroup.from_security_group_id(
            #     self, 'DefaultSG',
            #     security_group_id=vpc.vpc_default_security_group,
            # ),
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
            vpc=vpc.vpc,
        )

        self.ecs.add_asg_capacity_provider(
            provider=self.capacity_provider,
        )

        self.task_role = iam.Role(self, "MoodleTaskExecutionRole", assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        self.task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"))
 
        self.task = ecs.Ec2TaskDefinition(
            self, 'MoodleTaskDefinition',
            network_mode=ecs.NetworkMode.BRIDGE,
            task_role=self.task_role,
            # volumes=[self.volume]
        )
        self.smtp_user = iam.User(
            self, 'MoodleSMTPUser',
        )
        
        self.smtp_user.attach_inline_policy(
            iam.Policy(
                self, 'MoodleSesSendingAccess',
                statements=[
                    iam.PolicyStatement(
                        actions=['ses:SendRawEmail'],
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                    )
                ]
            )
        )

        self.smtp_keys = iam.AccessKey(
            self, 'MoodleSMTPUserKeys',
            user=self.smtp_user,
        )

        self.container = self.task.add_container(
            'MoodleContainer',
            image=ecs.ContainerImage.from_registry('public.ecr.aws/bitnami/moodle:latest'),
            environment={
                'MOODLE_USERNAME': 'admin', # Moodle application username. Default: user
                'MOODLE_PASSWORD': self.node.try_get_context('rds_admin_password'), # Moodle application password. Default: bitnami
                'MOODLE_EMAIL': 'michel.z.gaston@gmail.com', # Moodle application email. Default: user@example.com
                'MOODLE_SITE_NAME': 'TFAT', # Moodle site name. Default: New Site
                # 'MOODLE_SKIP_BOOTSTRAP': '', # Do not initialize the Moodle database for a new deployment. This is necessary in case you use a database that already has Moodle data. Default: no
                'MOODLE_DATABASE_TYPE': 'mysqli', # Database type. Valid values: mariadb, mysqli. Default: mariadb
                'MOODLE_DATABASE_HOST': database.mysql.db_instance_endpoint_address, # Hostname for database server. Default: mariadb
                'MOODLE_DATABASE_PORT_NUMBER': database.mysql.db_instance_endpoint_port, # Port used by database server. Default: 3306
                'MOODLE_DATABASE_NAME': 'moodle', # Database name that Moodle will use to connect with the database. Default: bitnami_moodle
                'MOODLE_DATABASE_USER': 'moodle', # Database user that Moodle will use to connect with the database. Default: bn_moodle
                'MOODLE_DATABASE_PASSWORD': self.node.try_get_context('rds_user_password'), # Database password that Moodle will use to connect with the database. No defaults.
                # 'ALLOW_EMPTY_PASSWORD': '', # It can be used to allow blank passwords. Default: no
                # 'MYSQL_CLIENT_FLAVOR': 'mysql', # SQL database flavor. Valid values: mariadb or mysql. Default: mariadb.
                # 'MYSQL_CLIENT_DATABASE_HOST': '', # Hostname for MariaDB server. Default: mariadb
                # 'MYSQL_CLIENT_DATABASE_PORT_NUMBER': '', # Port used by MariaDB server. Default: 3306
                # 'MYSQL_CLIENT_DATABASE_ROOT_USER': '', # Database admin user. Default: root
                # 'MYSQL_CLIENT_DATABASE_ROOT_PASSWORD': '', # Database password for the database admin user. No defaults.
                # 'MYSQL_CLIENT_CREATE_DATABASE_NAME': '', # New database to be created by the mysql client module. No defaults.
                # 'MYSQL_CLIENT_CREATE_DATABASE_USER': '', # New database user to be created by the mysql client module. No defaults.
                # 'MYSQL_CLIENT_CREATE_DATABASE_PASSWORD': '', # Database password for the MYSQL_CLIENT_CREATE_DATABASE_USER user. No defaults.
                # 'MYSQL_CLIENT_CREATE_DATABASE_CHARACTER_SET': '', # Character set to use for the new database. No defaults.
                # 'MYSQL_CLIENT_CREATE_DATABASE_COLLATE': '', # Database collation to use for the new database. No defaults.
                # 'MYSQL_CLIENT_CREATE_DATABASE_PRIVILEGES': '', # Database privileges to grant for the user specified in MYSQL_CLIENT_CREATE_DATABASE_USER to the database specified in MYSQL_CLIENT_CREATE_DATABASE_NAME. No defaults.
                # 'MYSQL_CLIENT_ENABLE_SSL_WRAPPER': '', # Whether to force SSL connections to the database via the mysql CLI tool. Useful for applications that rely on the CLI instead of APIs. Default: no
                # 'MYSQL_CLIENT_ENABLE_SSL': '', # Whether to force SSL connections for the database. Default: no
                # 'MYSQL_CLIENT_SSL_CA_FILE': '', # Path to the SSL CA file for the new database. No defaults
                # 'MYSQL_CLIENT_SSL_CERT_FILE': '', # Path to the SSL CA file for the new database. No defaults
                # 'MYSQL_CLIENT_SSL_KEY_FILE': '', # Path to the SSL CA file for the new database. No defaults
                # 'ALLOW_EMPTY_PASSWORD': '', # It can be used to allow blank passwords. Default: no
                # 'MOODLE_SMTP_HOST': f'email-smtp.{self.region}.amazonaws.com', # SMTP host.
                # 'MOODLE_SMTP_PORT': '465', # SMTP port.
                # 'MOODLE_SMTP_USER': self.smtp_keys.access_key_id, # SMTP account user.
                # 'MOODLE_SMTP_PASSWORD': self.smtp_keys.secret_access_key, # SMTP account password.
                # 'MOODLE_SMTP_PROTOCOL': 'TLS', # SMTP protocol.
                'PHP_ENABLE_OPCACHE': 'yes', # Enable OPcache for PHP scripts. No default.
                # 'PHP_EXPOSE_PHP': '', # Enables HTTP header with PHP version. No default.
                # 'PHP_MAX_EXECUTION_TIME': '', # Maximum execution time for PHP scripts. No default.
                # 'PHP_MAX_INPUT_TIME': '', # Maximum input time for PHP scripts. No default.
                # 'PHP_MAX_INPUT_VARS': '', # Maximum amount of input variables for PHP scripts. No default.
                # 'PHP_MEMORY_LIMIT': '', # Memory limit for PHP scripts. Default: 256M
                # 'PHP_POST_MAX_SIZE': '', # Maximum size for PHP POST requests. No default.
                # 'PHP_UPLOAD_MAX_FILESIZE': '', # Maximum file size for PHP uploads. No default.
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="moodle-ecs-ec2", 
                log_retention=logs.RetentionDays.FIVE_DAYS
            ),
            memory_reservation_mib=300,
        )


        self.task.add_volume(
            name='MoodleVolume',
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=filesystem.efs.file_system_id,
                root_directory='/data'
            )
        )

        self.container.add_mount_points(
            ecs.MountPoint(
                read_only=False,
                container_path='/bitnami',
                source_volume='MoodleVolume',
            )
        )

        self.container.add_port_mappings(
            ecs.PortMapping(container_port=8080)
        )

        self.service = ecs.Ec2Service(
            self, 'MoodleService',
            cluster=self.ecs,
            task_definition=self.task,
            desired_count=1,
            # vpc_subnets={'subnet_type': ec2.SubnetType.PUBLIC},
            # security_groups=[ec2.SecurityGroup.from_security_group_id(self,'DefaultSG',vpc.vpc_default_security_group)],
            health_check_grace_period=cdk.Duration.seconds(60),
            min_healthy_percent=0,
            max_healthy_percent=300,
            enable_execute_command=False,
        )

        # self.service.connections.allow_to(
        #     other=database.mysql,
        #     port_range=database.mysql.db_instance_endpoint_port,
        #     description='allow service to access mysql db'
        # )
        database.mysql.connections.allow_default_port_from(
            other=self.service,
            description='allow service to access mysql'
        )
        filesystem.efs.connections.allow_default_port_from(
            other=self.service,
            description='allow service to access efs filesystem',
        )

        self.service.connections.allow_from(
            other=loadbalancer.load_balancer,
            port_range=ec2.Port.tcp(80)
        )


        loadbalancer.http_listener.add_targets(
            'MoodleHttpServiceTarget',
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[self.service],
            health_check=elbv2.HealthCheck(
                healthy_http_codes="200-299,301,302",
                healthy_threshold_count=3,
                unhealthy_threshold_count=2,    
                interval=cdk.Duration.seconds(10),
            )
        )
