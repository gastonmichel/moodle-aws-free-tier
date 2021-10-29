from aws_cdk import (
    aws_ec2 as ec2,
    aws_efs as efs,
    core as cdk
)

class MoodleFileSystemStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, vpc: ec2.Vpc, **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.file_system = efs.FileSystem(
            self, "MoodleFileSystem",
            vpc=vpc,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_14_DAYS,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            vpc_subnets={'subnet_type': ec2.SubnetType.ISOLATED},
            throughput_mode=efs.ThroughputMode.BURSTING
        )