from aws_cdk import (
    core as cdk
)
from aws_cdk.aws_s3 import RedirectProtocol
from moodle import (
    VPCStack,
    DatabaseStack,
    FileSystemStack,
    ApplicationStack,
    LoadBalancerStack,
)

app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context('cdk_default_account'),
    region=app.node.try_get_context('cdk_default_region'),
)

vpc = VPCStack.MoodleVPCStack(
    app, 'MoodleVPC', env=env,
)


loadbalancer = LoadBalancerStack.MoodleLoadBalancerStack(
    app, 'MoodleLoadBalancer', env=env,
    vpc=vpc,    
)

database = DatabaseStack.MoodleDatabaseStack(
    app,'MoodleDatabase', env=env, 
    vpc=vpc,
)

filesystem = FileSystemStack.MoodleFileSystemStack(
    app,'MoodleFileSystem', env=env,
    vpc=vpc,
)

application = ApplicationStack.MoodleApplicationStack(
    app,'MoodleApplication', env=env,
    vpc=vpc,
    loadbalancer=loadbalancer,
    database=database,
    filesystem=filesystem,
)
application.add_dependency(filesystem)

app.synth()