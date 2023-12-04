import boto3
import logging

ec2 = boto3.resource('ec2')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# get a list of all instances
all_instances = [i for i in ec2.instances.all()]

def lambda_handler(event, context):

    #instances = ec2.instances.filter(Filters=filters)
    # get instances with filter of running + with tag `Name`
    instances = [i for i in ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}, {'Name':'tag:AutoOff', 'Values':['False']}])]

    # make a list of filtered instances IDs `[i.id for i in instances]`
    # Filter from all instances the instance that are not in the filtered list
    instances_to_delete = [to_del for to_del in all_instances if to_del.id not in [i.id for i in instances]]

    # run over your `instances_to_delete` list and terminate each one of them
    print("Instances to delete:")
    for instance in instances_to_delete:
        print(instance.id)