from aws_cdk import (
    aws_ec2 as ec2,
    core as cdk
)

class MoodleVPCStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.vpc = ec2.Vpc(
            self, 'MoodleVpc',
            cidr='10.0.0.0/16',
            max_azs=2,
            nat_gateways=0,
        )