import json
import boto3
from botocore.client import Config
import zipfile
import StringIO
import mimetypes

def lambda_handler(event, context):
    s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:096175320781:deployPortfolioTopic')

    location = {
        "bucketName" : 'build.reysuela.com',
        "objectKey" : 'buildportfolio.zip'
    }
   
    try:
        job = event.get("CodePipeline.job")

        if job:
            codepipeline = boto3.client('codepipeline')
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "BuildArtifact":
                    location = artifact["location"]["s3Location"] 
            
        build_bucket = s3.Bucket(location["bucketName"])
        portfolio_bucket = s3.Bucket('reysuela.com')
        portfolio_zip = StringIO.StringIO()
        #'/tmp/buildportfolio.zip'
        
        # On Windows, this will need to be a different location than /tmp
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)
        
        print "Location: " + str(location)
        
        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm, ExtraArgs={'ContentType': str(mimetypes.guess_type(nm)[0])})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
              
        topic.publish(Subject='Portfolio Deployment Success', Message='Your deployment was successful')
        if job:
            codepipeline.put_job_success_result(jobId=job['id'])

    except:
        print "something failed"
        topic.publish(Subject='Portfolio Deployment Not Successful', Message='Your deployment was not successful')
        if job:
            failureDetails={'type': 'JobFailed', 'message': 'something went wrong','externalExecutionId': job['id']}
            codepipeline.put_job_failure_result(jobId=job['id'],failureDetails=failureDetails)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

