import boto3
import logging

ec2 = boto3.resource('ec2')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("stopping instances...")

    instance_filter = [
        {'Name': 'instance-state-name', 'Values': ['running']},
        {'Name':'tag:AutoOff', 'Values':['True']}
    ]

    instances = [i for i in ec2.instances.filter(Filters=instance_filter)]

    logger.info(f"instances to be stopped: {instances}")

    for instance in instances:
        logger.info(f"stopping instance: {instance.id}")
        instance.stop()

    logger.info("instances stopped")