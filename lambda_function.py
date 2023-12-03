import json
import boto3
import logging
import os
import textwrap
import time

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_bucknet_name = os.environ.get("S3_BUCKET_NAME")

logger.info(f's3 bucket name: {s3_bucknet_name}')

s3 = boto3.client('s3')

def lambda_handler(event, context):
    logger.info('calculates pi to n decimal places...')

    subsegment = xray_recorder.begin_subsegment('pi-calc')

    num = 1000
    try:
        num = int(event["queryStringParameters"]['num'])
        logger.info(f'num: {num}')
    except:
        logger.warning('error parsing num from query string')
        pass

    subsegment.put_annotation('num', num)

    pi = 0

    try:
        digits = [str(n) for n in list(pi_digits(int(num)))]
        pi = "%s.%s\n" % (digits.pop(0), "".join(digits))
        logger.info(f'pi: {pi}')
        time.sleep(10) #simulate long running task
    except:
        logger.error('error calculating pi')
        return {
            "statusCode": 503,
            "isBase64Encoded": False,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": 0
        }

    subsegment.put_metadata("pi", pi)
    xray_recorder.end_subsegment()

    pi_wrapped = "\n".join(textwrap.wrap(pi,32))

    if s3_bucknet_name:
        subsegment = xray_recorder.begin_subsegment('s3-save')
        subsegment.put_annotation('num', num)
        subsegment.put_metadata("pi_wrapped", pi_wrapped)

        file_name = "pi.txt"
        s3_path = "data/" + file_name

        logger.info('saving pi to s3 bucket...')
        s3 = boto3.resource("s3")
        s3.Bucket(s3_bucknet_name).put_object(Key=s3_path, Body=pi_wrapped.encode("utf-8"))

        xray_recorder.end_subsegment()

    logger.info('returning response...')
    return {
        "statusCode": 200,
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": pi_wrapped
    }

def pi_digits(x):
    k,a,b,a1,b1 = 2,4,1,12,4
    while x > 0:
        p,q,k = k * k, 2 * k + 1, k + 1
        a,b,a1,b1 = a1, b1, p*a + q*a1, p*b + q*b1
        d,d1 = a/b, a1/b1
        while d == d1 and x > 0:
            yield int(d)
            x -= 1
            a,a1 = 10*(a % b), 10*(a1 % b1)
            d,d1 = a/b, a1/b1
