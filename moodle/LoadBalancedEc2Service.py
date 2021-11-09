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

class MoodleLoadBalacedServiceStack(cdk.Stack):

    def __init__(
        self, scope: cdk.Construct, id: str, 
        cluster: ecs.Cluster,
        task_definition: ecs.TaskDefinition,
        **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.service = ecs_patterns.ApplicationLoadBalancedEc2Service(
            self, 'MoodleLoadBalancedService',
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            health_check_grace_period=cdk.Duration.seconds(120),
            listener_port=80,
            min_healthy_percent=0,
            max_healthy_percent=200,
        )