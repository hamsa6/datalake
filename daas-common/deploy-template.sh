#!/bin/bash
# set variables
entity="$1"
accountId="$2"
environment="$3"
region="$4"
serviceType="$5"
templateName=cft-$serviceType-common
commonS3Bucket=$entity-s3-$accountId-$region-common-artifacts-$environment

# Check if parameters are defined
if [ ! -z "$entity" ] && [ ! -z "$accountId" ] && [ ! -z "$environment" ] && [ ! -z "$region" ] && [ ! -z "$serviceType" ]
then
    # Check if common bucket exits
    if aws s3 ls "$commonS3Bucket" 2>&1 | grep -q 'bucket does not exist'; then
        #Create the common bucket first
        echo $region
        aws s3api  create-bucket --acl private --bucket $commonS3Bucket --region $region
        sleep 20
        # Make common bucket private
        aws s3api put-public-access-block --bucket $commonS3Bucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
        #Add tags to the common bucket
        aws s3api  put-bucket-tagging --bucket $commonS3Bucket --tagging 'TagSet=[{Key=Name,Value="'$commonS3Bucket'"},{Key=Entity,Value="'$entity'"},{Key=Environment,Value="'$environment'"},{Key=region,Value="'$region'"}]'
    fi

    # Find the current directory to switch to daas-common
    parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
    if ! echo $parent_path | grep -p "daas-common"; then
        current_path="$parent_path/daas-common"
    else
        current_path=$parent_path
    fi

    # Copy the s3 bucket to the common deploy folder
    aws s3 cp $current_path/$templateName-template.yml \
       s3://$commonS3Bucket/$serviceType/scripts/template/$templateName-template.yml

    if [ "$serviceType" == "lmd" ]
    then
        # Copy the environment variable to the common deploy folder
        aws s3 cp $current_path/$templateName-env-var.yml \
          s3://$commonS3Bucket/$serviceType/scripts/template/$templateName-env-var.yml    
    fi

    # Switch back to parent directory
    if ! echo $parent_path | grep -p "daas-common"; then
        cd $parent_path
    fi
else
  echo "Missing required parameter. Usage: deploy-template.sh <entity> <account id> <environment> <region> <service type>"
fi