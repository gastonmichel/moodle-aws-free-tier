import os
from aws_cdk import (
    aws_ec2 as _ec2,
    aws_elasticloadbalancingv2 as _elbv2,
    core as cdk
)
 
class MoodleVPCStack(cdk.Stack):
 
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
 
        # VPC in 2 AZs with separate Private and Public subnets and 2 NAT Gateways
        self.vpc = _ec2.Vpc(
            self, "MoodleVPC",
            max_azs=2,
            subnet_configuration=[
                _ec2.SubnetConfiguration(
                    subnet_type=_ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                _ec2.SubnetConfiguration(
                    subnet_type=_ec2.SubnetType.PRIVATE,
                    name="Private",
                    cidr_mask=24,
                )
            ],
            nat_gateway_provider=_ec2.NatProvider.instance(instance_type=_ec2.InstanceType('t2.micro')),
            nat_gateways=1,
        )
       
        cdk.CfnOutput(self, "MoodleVPCID",
                       value=self.vpc.vpc_id)