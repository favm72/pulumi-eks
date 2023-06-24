import json

import pulumi
import pulumi_aws as aws

# get variables from pulumi.dev.yaml
app_config = pulumi.Config("app")
app_name = app_config.require("name")

aws_config = pulumi.Config("aws")
aws_region = aws_config.require("region")
aws_subnets: list[str] = aws_config.require_object("subnets")


# Create an IAM role for the cluster.
cluster_role = aws.iam.Role(
    f"{app_name}-cluster-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "eks.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    })
)

# Attach the AmazonEKSClusterPolicy managed policy to our cluster role.
cluster_role_policy_attachment = aws.iam.RolePolicyAttachment(
    "cluster-role-policy-attachment",
    role=cluster_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy")

# Create an EKS cluster just in us-east-1a for now.
cluster = aws.eks.Cluster(
    f"{app_name}-cluster",
    role_arn=cluster_role.arn,
    version="1.27",
    name=f"{app_name}-cluster",
    vpc_config=aws.eks.ClusterVpcConfigArgs(
        subnet_ids=aws_subnets,
    ))

# Create an IAM role for the worker nodes.
node_role = aws.iam.Role(
    f"{app_name}-node-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    })
)

# Attach the AmazonEKSWorkerNodePolicy managed policy to our node role.
node_role_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{app_name}-node-role-policy-attachment-1",
    role=node_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy")

# Attach the AmazonEC2ContainerRegistryReadOnly managed policy to our node role.
node_role_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{app_name}-node-role-policy-attachment-2",
    role=node_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly")

# Attach the AmazonEKS_CNI_Policy managed policy to our node role.
node_role_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{app_name}-node-role-policy-attachment-3",
    role=node_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy")


# Add worker nodes to the cluster.
node_group = aws.eks.NodeGroup(
    f"{app_name}-node-group",
    cluster_name=cluster.name,
    node_group_name=f"{app_name}-node-group",
    node_role_arn=node_role.arn,
    subnet_ids=aws_subnets,
    scaling_config=aws.eks.NodeGroupScalingConfigArgs(
        desired_size=1,
        max_size=1,
        min_size=1,
    ),
)

# Export the cluster's info.
pulumi.export("arn", cluster.arn)
pulumi.export("output", cluster.kubernetes_network_config)
