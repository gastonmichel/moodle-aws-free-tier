from aws_cdk import (
    core as cdk
)
from aws_cdk.aws_s3 import RedirectProtocol
from moodle.VPCStack import MoodleVPCStack
from moodle.DatabaseStack import MoodleDatabaseStack
from moodle.FileSystemStack import MoodleFileSystemStack
from moodle.LoadBalancerStack import MoodleLoadBalancerStack
from moodle.RedisStack import MoodleRedisStack
from moodle.ApplicationStack import MoodleApplicationStack
from moodle.LoadBalancedEc2Service import MoodleLoadBalacedServiceStack
app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context('cdk_default_account'),
    region=app.node.try_get_context('cdk_default_region'),
)

vpc = MoodleVPCStack(
    app, 'MoodleVPC', env=env,
)

redis = MoodleRedisStack(
    app, 'MoodleRedis', env=env, 
    vpc=vpc.vpc,
)

loadbalancer = MoodleLoadBalancerStack(
    app, 'MoodleLoadBalancer', env=env,
    vpc=vpc.vpc,    
)

database = MoodleDatabaseStack(
    app,'MoodleDatabase', env=env, 
    vpc=vpc.vpc,
)

filesystem = MoodleFileSystemStack(
    app,'MoodleFileSystem', env=env,
    vpc=vpc.vpc
)

moodle = MoodleApplicationStack(
    app,'MoodleApplication', env=env,
    vpc=vpc.vpc,
    loadbalancer=loadbalancer.load_balancer,
    database=database.db_instance,
    filesystem=filesystem.file_system,
    sessioncache=redis.redis_cluster,
)
moodle.add_dependency(filesystem)

# service = MoodleLoadBalacedServiceStack(
#     app, 'MoodleService', env=env,
#     cluster=moodle.ecs,
#     task_definition=moodle.task,
# )

app.synth()