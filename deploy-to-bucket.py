import json
import boto3
from botocore.client import Config
import zipfile

def lambda_handler(event, context):
    s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:096175320781:deployPortfolioTopic')
    
    try:
        
        build_bucket = s3.Bucket('build.reysuela.com')
        portfolio_bucket = s3.Bucket('reysuela.com')
        
        # On Windows, this will need to be a different location than /tmp
        build_bucket.download_file('buildportfolio.zip', '/tmp/buildportfolio.zip')
        
        with zipfile.ZipFile('/tmp/buildportfolio.zip') as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm)
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
        
        topic.publish(Subject='Portfolio Deployment Success', Message='Your deployment was successful')
        
    except:
        topic.publish(Subject='Portfolio Deployment Not Successful', Message='Your deployment was not successful')
        
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!')
        }

