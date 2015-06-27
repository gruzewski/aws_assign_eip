__author__ = 'jacek gruzewski'

# Python's libraries
import requests
import sys
import logging

# AWS Boto library
from boto import ec2

# Config file imports
import aws_config

# Static AWS Rest service for getting instance details
AWS_METADATA = 'http://169.254.169.254/latest/meta-data/instance-id'

logging.basicConfig(filename='/var/log/cloud-init-eip.log', level=logging.INFO)

# Parsing configuration and connecting to AWS
try:
    region = getattr(aws_config, "region")
    aws_access_key = getattr(aws_config, "access_key")
    aws_secret_key = getattr(aws_config, "secret_key")
    eip_id = getattr(aws_config, "eip_id")

    ec2_conn = ec2.connect_to_region(region_name=region,
                                     aws_access_key_id=aws_access_key,
                                     aws_secret_access_key=aws_secret_key)
except AttributeError as at_err:
    logging.error('Couldnt read parameters from aws_config.py file. [%s]', at_err)
    sys.exit(1)

if ec2_conn is None:
    logging.error('Couldnt connect with this parameters: %s, %s, <secret key>', region, aws_access_key)
    sys.exit(1)

logging.info('Connected to AWS [%s]', region)

try:
    instance_id = requests.get(AWS_METADATA, timeout=0.5).text
except requests.exceptions.Timeout as t_err:
    logging.error('Timeout occured: %s', t_err)
    sys.exit(1)
except requests.exceptions.ConnectionError as con_err:
    logging.error('Connection error occured: %s', con_err)
    sys.exit(1)

logging.info('Got details from AWS [instance id: %s]', instance_id)

eip = ec2_conn.get_all_addresses(allocation_ids=eip_id)

if eip[0].instance_id is None:
    status = ec2_conn.associate_address(instance_id=instance_id,
                                        public_ip=None,
                                        allocation_id=eip_id)
    if status is True:
        logging.info('Elastic IP was allocated.')
    else:
        logging.error('Elastic IP [%s] couldnt be allocated.', eip_id)
else:
    logging('Elastic IP [%s] is allocated to %s', eip_id, instance_id)
    sys.exit(1)
