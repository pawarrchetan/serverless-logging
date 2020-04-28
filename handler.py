# Lambda function to subscribe all new cloudwatch log groups to a
# log shipper function
import os
import sys
import logging
import uuid
import boto3


# set logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)
logging.getLogger('botocore').setLevel(logging.WARNING)

lb = boto3.client("lambda")
logs = boto3.client("logs")


# Target function for subscriptions
LOG_SHIPPER_FUNCTION = os.environ['TARGET_FUNCTION']
PREFIX = os.getenv('PREFIX', '/aws/lambda/')
# Common name for subscription filters
FILTER_NAME = "all"


def get_shipper_arn():
    try:
        response = lb.get_function(FunctionName=LOG_SHIPPER_FUNCTION)
    except Exception as e:
        log.error(f"Could not get the funcion ARN : {e}")
        log.error(f"code: {e.response['Error']['Code']}")
        sys.exit()
    return response["Configuration"]["FunctionArn"]


def subscribe_log_group(lg_name, region, account_id):
    log.info("Setting permissions")
    try:
        response = lb.add_permission(
            FunctionName=LOG_SHIPPER_FUNCTION,
            StatementId=str(uuid.uuid4()),
            Action='lambda:InvokeFunction',
            Principal=f"logs.{region}.amazonaws.com",
            SourceArn=f"arn:aws:logs:{region}:{account_id}:log-group:{lg_name}:*",
            SourceAccount=account_id)
        log.debug("Response: {response}")
    except Exception as e:
        log.error(f"Unexpected error in Add Permission : {e}")
        log.error(f"code: {e.response['Error']['Code']}")
        sys.exit()
    # log.info("Subscribing log group", lg_name)
    try:
        logs.put_subscription_filter(
            logGroupName=lg_name,
            filterName=FILTER_NAME,
            filterPattern='',
            destinationArn=get_shipper_arn())
    except Exception as e:
        log.error(f"Unexpected error in put Subscription Filter : {e}")
        log.error(f"code: {e.response['Error']['Code']}")
        sys.exit()


def lambda_handler(event, context):
    log.info("Running log subscriber")
    region = context.invoked_function_arn.split(':')[3]
    account_id = context.invoked_function_arn.split(':')[4]

    # Commence subscription functionality
    event_name = event['detail']['eventName']
    if event_name == "CreateLogGroup":
        log_group_name = event['detail']['requestParameters']['logGroupName']
        print(log_group_name)
        print(PREFIX)
        if log_group_name.startswith(PREFIX):
            log.info(f"Log Group {log_group_name} discovered")
            subscribe_log_group(log_group_name, region, account_id)
        else:
            log.info("No log group with prefix /aws/lambda/ found.")
