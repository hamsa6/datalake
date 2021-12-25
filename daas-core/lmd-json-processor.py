import json
import boto3



# --------------------------------------------------
# Initializes global variables
# --------------------------------------------------
def init():
    global s3, s3_client, lambda_client, event_client, glue_client, glue_db_name 
    global lakeformation_role_name, target_lambda_name, daas_config, accountid
    global region
    s3_client = boto3.client('s3')
    s3 = boto3.resource('s3')
    glue_client = boto3.client('glue')
    lambda_client = boto3.client('lambda')
    event_client = boto3.client('events')
    accountid = os.environ["ENV_VAR_ACCOUNT_ID"]
    region = os.environ["ENV_VAR_REGION_NAME"]
    daas_config = os.environ["ENV_VAR_DAAS_CONFIG_FILE"]
    glue_db_name = os.environ["ENV_VAR_DAAS_CORE_GLUE_DB"]
    lakeformation_role_name = os.environ["ENV_VAR_GLUE_SERVICE_ROLE"]
    target_lambda_name = os.environ["ENV_VAR_CLIENT_LAMBDA_NAME"]

# -------------------------------------------------
# Create the cloudwatch event for the crawler
# -------------------------------------------------
def create_cloudwatch_event(crawler_name):
    rule_name = crawler_name + "-event"
    event_json_string = json.dumps({'source': ['aws.glue'], 'detail-type': ['Glue Crawler State Change'],
                                    'detail': {'crawlerName': [crawler_name], 'state': ['Succeeded']}})
 
    # Create the rule first
    rule_response = event_client.put_rule(
        Name=rule_name,
        EventPattern=event_json_string,
        State='ENABLED',
        Description='Cloud Watch event rule for crawler ' + crawler_name
    )
 
    # Place the lambda target for the rule
    response = event_client.put_targets(
        Rule=rule_name,
        Targets=[{'Id': rule_name, 'Arn': target_lambda_arn}, ]
    )
 
    # Grant invoke permission to Lambda
    lambda_client.add_permission(
        FunctionName=target_lambda_name,
        StatementId=rule_name,
        Action='lambda:InvokeFunction',
        Principal='events.amazonaws.com',
        SourceArn=rule_response['RuleArn'],
    )

# ----------------------------------------------------------
# Read the account id from the daas-config file
# ----------------------------------------------------------
def get_client_accountid(data_dict):
    accountid = json.loads(data_dict)['account_id']
    return accountid

# ----------------------------------------------------------
# Read the region from the daas-config file
# ----------------------------------------------------------
def get_client_region(data_dict):
    region = json.loads(data_dict)['region']
    return region

# ----------------------------------------------------------
# Read the entity from the daas-config file
# ----------------------------------------------------------
def get_client_entity_name(data_dict):
    entity_name = json.loads(data_dict)['entity']
    return entity_name
# ----------------------------------------------------------
# Invoke metadata generator lambda on the client account
# ----------------------------------------------------------
def invoke_lambda(target_lambda_arn, target_lambda_role_arn, crawler_name, path, domain_name, table_name, value, partition_values):
    sts_connection = boto3.client('sts')
    daas_client = sts_connection.assume_role(
        RoleArn=target_lambda_role_arn,
        RoleSessionName="daas-core"
    )
    ACCESS_KEY = daas_client['Credentials']['AccessKeyId']
    SECRET_KEY = daas_client['Credentials']['SecretAccessKey']
    SESSION_TOKEN = daas_client['Credentials']['SessionToken']
    lambda_client = boto3.client('lambda', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, aws_session_token=SESSION_TOKEN)
    data={}
    data['glue_db_name'] = glue_db_name
    data['lakeformation_role_name'] = lakeformation_role_name
    data['target_lambda_name'] = target_lambda_name
    data['target_lambda_arn'] = target_lambda_arn
    data['source_file_path'] = path
    data['domain_name'] = domain_name
    data['crawler_name'] = crawler_name
    data['table_name'] = table_name
    data['partitions'] = value
    data['partition_values'] = partition_values
    json_str=json.dumps(data)
    response = lambda_client.invoke(
        FunctionName= target_lambda_arn, 
        InvocationType = "Event", 
        Payload = json_str
    )
    return response['Payload'].read()

# -------------------------------------------------
# Main lambda function
# -------------------------------------------------
def lambda_handler(event, context):
    init()
    print(f'event is {event}')
    partition_values=[]
    source_bucket = event['bucket_name']
    source_key = urllib.parse.unquote_plus(event['file_key'], encoding='utf-8')
    object_name = source_key.split('/')[-1] # get the file name
    domain_name = source_key.split('/')[0:2][1]  # get the second prefix and assign it as the domain name
    short_path = source_key[0:source_key.rfind('/',0)] # get upto the file path
    is_dot_folder_object = short_path.rfind('.',0)
    is_ignore_object = short_path.find('-daas-gen-raw')
    if object_name and is_dot_folder_object == -1 and is_ignore_object == -1:
        source_name = source_key.split('/')[0:1][0]  # get the first prefix and assign it as the source name
        partitions = source_key.split('/')[2:-1]  # Remove source name, domain name in the front and the key at the end
        for key in partitions:
            value = key.split('=')[1]
            print(value)
            if value:
                partition_values.append(value)
            else:
                partition_values.append(key)
        extention = object_name.split('.')[-1] # get the file extension.
        path = 's3://' + source_bucket + '/' + source_name + '/' +  domain_name + '/'
        if extention.lower() == 'json':
            fileObj = s3_client.get_object(Bucket= source_bucket, Key=daas_config)
            data_dict = fileObj['Body'].read()
            account_id = get_client_accountid(data_dict)
            region = get_client_region(data_dict)
            entity = get_client_entity_name(data_dict)
            target_lambda_arn = 'arn:aws:lambda:' + region + ':' + account_id + ':function:' + target_lambda_name
            target_lambda_role_arn = 'arn:aws:iam::' + account_id + ':role/rle-' + target_lambda_name
            crawler_name = entity + '-' + source_name + '-' + domain_name + '-' + 'raw-crawler'
            table_name = domain_name.replace('-','_')
            result = invoke_lambda(target_lambda_arn, target_lambda_role_arn, crawler_name, path, domain_name, table_name, value, partition_values)
            # create_cloudwatch_event(crawler_name)
            print(result)
        else:
            print('File is not json, so ignoring')
    
