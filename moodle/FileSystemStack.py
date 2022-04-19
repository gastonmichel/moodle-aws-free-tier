from aws_cdk import (
    aws_ec2 as ec2,
    aws_efs as efs,
    core as cdk
)
from . import VPCStack
class MoodleFileSystemStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, vpc: VPCStack.MoodleVPCStack, **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.efs = efs.FileSystem(
            self, "MoodleFileSystem",
            vpc=vpc.vpc,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_14_DAYS,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED),
            throughput_mode=efs.ThroughputMode.BURSTING,
        )