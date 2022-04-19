from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    core as cdk
)
from . import VPCStack

class MoodleLoadBalancerStack(cdk.Stack):
 
    def __init__(self, scope: cdk.Construct, construct_id: str, vpc: VPCStack.MoodleVPCStack, **kwargs):
        
        super().__init__(scope, construct_id, **kwargs)

        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self, 'MoodleLoadBalancer',
            vpc=vpc.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            internet_facing=True,
        )

        self.load_balancer.connections.allow_from_any_ipv4(
            port_range=ec2.Port.tcp(80),
            description='allow internet in port 80',
        )

        # self.load_balancer.connections.allow_from_any_ipv4(
        #     port_range=ec2.Port.tcp(443),
        #     description='allow internet in port 443',
        # )


        self.http_listener = self.load_balancer.add_listener(
            'MoodleHttpListener',
            port=80,
        )