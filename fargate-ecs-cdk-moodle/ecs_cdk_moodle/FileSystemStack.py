
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
 
class MoodleFileSystemStackProperties:
    def __init__(
            self,
            vpc: _ec2.Vpc,
    ) -> None:
 
        self.vpc = vpc
 
class MoodleFileSystemStack(cdk.Stack):
 
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 properties: MoodleFileSystemStackProperties, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
 
        # define shared file system
        self.file_system = _efs.FileSystem(
            self, "MoodleFileSystem",
            vpc=properties.vpc,
            performance_mode=_efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=_efs.ThroughputMode.BURSTING
        )