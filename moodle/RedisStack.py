from aws_cdk import (
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    core as cdk
)

class MoodleRedisStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, vpc: ec2.Vpc, **kwargs):
        
        super().__init__(scope=scope, id=id, **kwargs)

        self.redis_subnet_group = elasticache.CfnSubnetGroup(
            self, 'MoodleRedisSubnetGroup',
            description='moodle redis subnet group',
            subnet_ids=[subnet.subnet_id for subnet in vpc.isolated_subnets],
            cache_subnet_group_name='moodle-redis-subnet-group',
        )

        self.redis_cluster = elasticache.CfnCacheCluster(
            self, 'RedisCluster',
            cache_node_type=self.node.try_get_context('redis_node_type'),
            engine='Redis',
            num_cache_nodes=1,
            az_mode='single-az',
            cache_subnet_group_name=self.redis_subnet_group.cache_subnet_group_name,
            cluster_name='moodle-redis-session-cache',
            engine_version='6.x',
            vpc_security_group_ids=[vpc.vpc_default_security_group],
            preferred_availability_zone='us-east-1a'
        )

        self.redis_cluster.add_depends_on(self.redis_subnet_group)