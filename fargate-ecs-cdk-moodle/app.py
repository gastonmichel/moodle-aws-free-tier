#!/usr/bin/env python3
import os
from aws_cdk import core as cdk
from ecs_cdk_moodle.VPCStack import MoodleVPCStack
from ecs_cdk_moodle.FileSystemStack import (
    MoodleFileSystemStackProperties,
    MoodleFileSystemStack
)
from ecs_cdk_moodle.LoadBalancerStack import (
    MoodleLoadBalancerStackProperties,
    MoodleLoadBalancerStack
)
from ecs_cdk_moodle.DatabaseStack import (
    MoodleDatabaseStackProperties,
    MoodleDatabaseStack
)
from ecs_cdk_moodle.ApplicationStack import (
    MoodleApplicationStackProperties,
    MoodleApplicationStack
)
 
# specify environment details
environment_name = "DEV"

env = cdk.Environment(
    account='841690643466',
    region='us-east-2',
)
app = cdk.App()
 
# specify tag details
tags = [
    ['Application', 'Moodle'],
    ['Environment', environment_name]
]
 
# create vpc stack
moodle_vpc_stack = MoodleVPCStack(
    app, f"MoodleVPC{environment_name}", env=env,
    )
 
# define load balancer properties, passing vpc as parameter
moodle_loadbalancer_properties = MoodleLoadBalancerStackProperties(
    vpc=moodle_vpc_stack.vpc,
)
 
#create load balancer stack
moodle_loadbalancer_stack = MoodleLoadBalancerStack(
    app, f"MoodleLoadBalancer{environment_name}", env=env,
    properties=moodle_loadbalancer_properties
)
 
#create database properties, passing vpc as parameter
moodle_database_properties = MoodleDatabaseStackProperties(
    vpc=moodle_vpc_stack.vpc
)
 
# create database stack
moodle_database_stack = MoodleDatabaseStack(
    app, f"MoodleDatabase{environment_name}", env=env,
    properties=moodle_database_properties
)
 
# create file system properties, passing vpc as parameter
moodle_filesystem_properties = MoodleFileSystemStackProperties(
    vpc=moodle_vpc_stack.vpc
)
 
# create file system stack
moodle_filesystem_stack = MoodleFileSystemStack(
    app, f"MoodleFileSystem{environment_name}", env=env,
    properties=moodle_filesystem_properties
)
 
# create application properties, passing previous resources as parameters
moodle_application_properties = MoodleApplicationStackProperties(
    vpc=moodle_vpc_stack.vpc,
    loadbalancer=moodle_loadbalancer_stack.loadbalancer,
    database=moodle_database_stack.database,
    filesystem=moodle_filesystem_stack.file_system,
)
 
# create application stack
moodle_application_stack = MoodleApplicationStack(
   app, f"MoodleApplication{environment_name}", env=env,
    properties=moodle_application_properties
)
 
# assign tags to resources created within stacks
for stack in [moodle_vpc_stack, moodle_loadbalancer_stack, moodle_filesystem_stack, moodle_database_stack, moodle_application_stack]:
    for tag in tags:
        cdk.Tags.of(stack).add(tag[0], tag[1])
 
app.synth()