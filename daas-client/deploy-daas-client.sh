#!/bin/bash
# set variables
entity=$1
accountId=$2
region=$3
environment=$4

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] 
then
    # Deploy the VPC
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region vpc
    # sh ../deploy-stack.sh $entity $accountId daas-client $environment $region vpc
    # sleep 90
    # Deploy the Nat Gateway
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region ngw
    # sh ../deploy-stack.sh $entity $accountId daas-client $environment $region ngw
    #sleep 60
    # Deploy the buckets
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region s3
    # sh ../deploy-stack.sh $entity $accountId daas-client-athena-log $environment $region s3
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region s3
    # sh ../deploy-stack.sh $entity $accountId daas-client-test-raw-bucket $environment $region s3
    sh ../deploy-stack.sh $entity $accountId daas-client-test-cur-bucket $environment $region s3

    # Deploy the metadata generator lambda
    sh ../daas-common/deploy-template.sh $entity $accountId $environment $region lmd
    # sh ../deploy-stack.sh $entity $accountId metadata-generator $environment $region lmd 2
    # Deploy the secrets manager for postgres srvlss
    # sh ../daas-common/deploy-template.sh $entity $accountId $environment $region smgr
    # sh ../deploy-stack.sh $entity $accountId daas-client-pgsrvls $environment $region smgr
    # Deploy the Glue connection
    #sh ../daas-common/deploy-template.sh $entity $accountId $environment $region glucon
    #sh ../deploy-stack.sh $entity $accountId daas-client-pgsrvls $environment $region glucon
    # Deploy the glue job generator lambda
    # sh ../deploy-stack.sh $entity $accountId glujb-sync-generator $environment $region lmd 1   
else
    echo "Missing required parameter. Usage: deploy-stack.sh <entity> <account id> <region> <environment>"
fi