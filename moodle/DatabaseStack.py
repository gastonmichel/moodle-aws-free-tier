from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    core as cdk
)
from . import VPCStack

class MoodleDatabaseStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, vpc: VPCStack.MoodleVPCStack, **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.subnets = rds.SubnetGroup(
            self,
            "MoodleDBSubnetGroup",
            description="subnet group for moodle db",
            vpc=vpc.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.ISOLATED,
            ),
        )

        self.mysql = rds.DatabaseInstance(
            self, 'MoodleDBInstance',
            database_name='moodle',
            instance_identifier='moodle',
            instance_type=ec2.InstanceType(self.node.try_get_context('rds_node_type')),
            credentials=rds.Credentials.from_password(
                username='admin',
                password=cdk.SecretValue.plain_text(self.node.try_get_context('rds_admin_password')),
            ),
            multi_az=False,
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0,
            ),
            vpc=vpc.vpc,
            subnet_group=self.subnets,
            publicly_accessible=False,
            allocated_storage=20,
            storage_type=rds.StorageType.GP2,
        )
        self.mysql.node.add_dependency(self.subnets)
        