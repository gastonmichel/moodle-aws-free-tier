
import os
from aws_cdk import (
    aws_ec2 as _ec2,
    aws_ecs as _ecs,
    aws_rds as _rds,
    aws_efs as _efs,
    aws_ecr_assets as _ecr_assets,
    aws_elasticloadbalancingv2 as _elbv2,
    aws_logs as _logs,
    core as cdk
)
 
class MoodleLoadBalancerStackProperties:
 
    def __init__(
            self,
            vpc: _ec2.Vpc,
    ) -> None:
 
        self.vpc = vpc
 
class MoodleLoadBalancerStack(cdk.Stack):
 
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 properties: MoodleLoadBalancerStackProperties, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
 
        # define loadbalancer security group with custom outbound rule
        lbsg = _ec2.SecurityGroup(self, id="MoodleLoadBalancer-SG"
                               , vpc=properties.vpc, allow_all_outbound=False
        )
 
        # set egress rule to port 80/443
        lbsg.add_egress_rule(_ec2.Peer.any_ipv4(),
            connection=_ec2.Port.tcp(80),
            description="Allow outbound 80/443"
        )
 
        # load balancer       
        self.loadbalancer = _elbv2.ApplicationLoadBalancer(
            self, "MoodleLoadBalancer",
            vpc=properties.vpc,
            internet_facing=True,
            security_group=lbsg,
            vpc_subnets=_ec2.SubnetSelection(subnet_type=_ec2.SubnetType.PUBLIC)           
        )