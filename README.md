# Overview
The combination of the 2 functions deployed by this repository allow centralised logging of serverless components in Elasticsearch.
This package is used to deploy 2 serverless function to centralise the serverless logging.
1. create a log-shipper function to ship CloudWatch logs generated after the invocation of Lambda Functions.
2. create a log-subscriber function to subscribe newly created CloudWatch log groups with PREFIX "/aws/lambda/" to the log-shipper function.

Whenever the `log-shipper` lambda is invoked :
* logs are generated in the CloudWatch log group for the respective lambda function.
* logs are matched by the shipper function
* logs are shipped to the Elasticsearch Cloud used for log centralization.

Whenever there is any serverless component deployed in the AWS accounts, the `log-subscriber` function will detect the `CreateLogGroup` event from CloudWatch logs and create a subscription filter for the CloudWatch log group to allow the `log-shipper` function to ship the logs to the Elasticsearch.


# Instructions
The `functionbeat.yml` file mentions the log group `/aws/lambda/sample` for subscription to the `log-shipper` function. This log group is only added for initialization of the `log-shipper` function.

* functionbeat binary does not automatically handle updates to the function if the configuration changes. To mitigate this, we have a boolean variable in CI / CD pipeline job which takes care of the DEPLOY or UPDATE. 

A value of DEPLOY = "TRUE" will deploy the function as a new cloudformation stack at first deployment.
A value of DEPLOY = "FALSE" will update the existing cloudformation stack if there are any changes to the file `functionbeat.yml`

# Deploy lambda

## Package
The 2 functions described above use 2 different methods to be deployed to the AWS accounts.
* `log-shipper` uses functionbeat.
* `log-subscriber` uses serverless.

Getting Started : https://www.elastic.co/guide/en/beats/functionbeat/current/functionbeat-getting-started.html

## Deploying the functions
The function can be deployed using functionbeat and serverless binary separately.

### Functionbeat
You can find the Elastic Cloud password in AWS Secrets Manager. This secret is required for HTTP Basic Authentication to send logs via HTTPS to Elastic Cloud.

#### Step 1: Download Functionbeat
```
curl -L -O https://artifacts.elastic.co/downloads/beats/functionbeat/functionbeat-7.6.1-linux-x86_64.tar.gz
tar xzvf functionbeat-7.6.1-linux-x86_64.tar.gz
```

#### Step 2: Configure Functionbeat
 Guide : https://www.elastic.co/guide/en/beats/functionbeat/current/functionbeat-configuration.html

#### Step 3: Load Index template in Elasticsearch
 Guide : https://www.elastic.co/guide/en/beats/functionbeat/current/functionbeat-template.html

#### Step 4: Deploy Functionbeat
1. Make sure you have the credentials required to authenticate with AWS. You can set environment variables that contain your credentials:
```
export AWS_ACCESS_KEY_ID=ABCDEFGHIJKLMNOPUSER
export AWS_SECRET_ACCESS_KEY=EXAMPLE567890devgHIJKMLOPNQRSTUVZ1234KEY
export AWS_DEFAULT_REGION=us-east-1
```

2. Make sure the user has the permissions required to deploy and run the function. For more information, See https://www.elastic.co/guide/en/beats/functionbeat/current/iam-permissions.html  for more details.

3. Deploy the cloud function.
For example, the following command deploys a function called cloudwatch:

linux and mac:
```
./functionbeat -v -e -d "*" deploy log-shipper
```

#### Step 5: View your data in Kibana
To learn how to view and explore your data, see the Kibana User Guide - https://www.elastic.co/guide/en/kibana/7.6/index.html

### Serverless

#### Deploying the function
You can find the RDS password in AWS Secrets Manager. When we provision the DB with terraform we also write that secret there so that it can integrate with the automated deployment process securely.

Deploy command (**staging** example):
```bash
aws lambda create-function --function-name test-results-customer --runtime python3.6 \
--zip-file fileb://results-customer-consumer.zip --handler handler.handler \
--role arn:aws:iam::882235782134:role/temp-lambda-results-consumer \
--environment "Variables={API_ENDPOINT=https://api.epilot.cloud,API_USERNAME=staging_results_consumer,API_PASSWORD=<redacted>,WIDGET_API_ENDPOINT=https://api.staging.epilot.io/widget}"
```

#### Map lambda function to sqs
```bash
aws lambda create-event-source-mapping --function-name test-results-customer --batch-size 5 \
--event-source-arn arn:aws:sqs:eu-central-1:882235782134:customer
```

#### Update function code
```bash
aws lambda update-function-code --function-name test-results-customer  --zip-file fileb://results-customer-consumer.zip
```

## Subscriber Function
Once both the serverless functions are deployed, we also have the capability to auto-subcribe newly created CloudWatch log groups to the log-shipper function.
The log subscriber function will look for prefix /aws/lambda/ to auto-subscribe the newly created CloudWatch log groups.

# References

* https://www.elastic.co/guide/en/beats/functionbeat/current/index.html

* https://www.elastic.co/guide/en/beats/functionbeat/current/functionbeat-getting-started.html

* https://serverless.com/framework/docs/getting-started/
