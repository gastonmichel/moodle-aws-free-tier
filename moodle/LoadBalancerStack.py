from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    core as cdk
)

class MoodleLoadBalancerStack(cdk.Stack):
 
    def __init__(self, scope: cdk.Construct, construct_id: str, vpc: ec2.Vpc, **kwargs):
        
        super().__init__(scope, construct_id, **kwargs)
        
        self.security_group = ec2.SecurityGroup(
            self, 'MoodleLoadBalancerSG',
            vpc=vpc,
            allow_all_outbound=False,
        )

        self.security_group.add_egress_rule(
            ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description='Allow outbound 80/443',
        )

        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self, 'MoodleLoadBalancer',
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            internet_facing=True,
            security_group=self.security_group,
        )