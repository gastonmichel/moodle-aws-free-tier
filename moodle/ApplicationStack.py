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
    core as cdk
)

class MoodleApplicationStack(cdk.Stack):

    def __init__(
        self, scope: cdk.Construct, id: str, 
        vpc: ec2.Vpc,
        loadbalancer: elbv2.ApplicationLoadBalancer,
        database: rds.CfnDBInstance,
        filesystem: efs.FileSystem,
        sessioncache: elasticache.CfnCacheCluster,
        **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.image = ecr_assets.DockerImageAsset(
            self, 'MoodleDockerImage',
            directory='./docker',
        )

        self.ecs = ecs.Cluster(
            self, 'MoodleECSCluster',
            vpc=vpc,
            cluster_name='moodle-ecs-cluster',
            container_insights=True,
        )

        self.ecs.add_capacity("MoodleECSAutoScalingGroupCapacity",
            instance_type=ec2.InstanceType(self.node.try_get_context('ecs_node_type')),
            desired_capacity=1,
            min_capacity=1,
            max_capacity=1,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        self.volume = ecs.Volume(
            name='MoodleVolume',
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=filesystem.file_system_id,
            )
        )

        self.task = ecs.Ec2TaskDefinition(
            self, 'MoodleTaskDefinition',
            volumes=[self.volume],
            network_mode=ecs.NetworkMode.BRIDGE,
        )

        self.container = self.task.add_container(
            'MoodleContainer',
            image=ecs.ContainerImage.from_docker_image_asset(self.image),
            environment={
                'DB_TYPE': 'mysqli',
                'DB_HOST': database.attr_endpoint_address,
                'DB_PORT': database.attr_endpoint_port,
                'DB_NAME': 'moodle',
                'DB_USER': 'admin',
                'DB_PASS': self.node.try_get_context('rds_admin_password'),
                'REDIS_HOST': sessioncache.attr_redis_endpoint_address,
                'REDIS_PORT': sessioncache.attr_redis_endpoint_port,
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="moodle-ecs-fargate", 
                log_retention=logs.RetentionDays.FIVE_DAYS
            ),
            memory_reservation_mib=300,
        )

        self.container.add_mount_points(
            ecs.MountPoint(
                read_only=False,
                container_path='/var/www/moodle',
                source_volume=self.volume.name,
            )
        )

        self.container.add_port_mappings(
            ecs.PortMapping(container_port=80)
        )

        self.service = ecs.Ec2Service(
            self, 'MoodleService',
            cluster=self.ecs,
            task_definition=self.task,
            desired_count=1,
            # vpc_subnets={'subnet_type': ec2.SubnetType.PUBLIC},
            # security_groups=[ec2.SecurityGroup.from_security_group_id(self,'DefaultSG',vpc.vpc_default_security_group)],
            health_check_grace_period=cdk.Duration.seconds(1200),
            min_healthy_percent=0,
            max_healthy_percent=200,
            enable_execute_command=True,
        )


        self.service.connections.allow_from(
            other=loadbalancer,
            port_range=ec2.Port.tcp(80)
        )

        self.http_listener = loadbalancer.add_listener(
            'MoodleHttpListener',
            port=80,
        )

        self.http_listener.add_targets(
            'MoodleHttpServiceTarget',
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[self.service],
            # health_check=_elbv2.HealthCheck(healthy_http_codes="200-299,301,302",
            #     healthy_threshold_count=3,
            #     unhealthy_threshold_count=2,    
            #     interval=cdk.Duration.seconds(10),
            # )
        )

        cdk.CfnOutput(
            self, "MoodleLoadBalancerDNSName",
            value=loadbalancer.load_balancer_dns_name
        )