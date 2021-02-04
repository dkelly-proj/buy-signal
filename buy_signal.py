import boto3
import config

client = boto3.client(
    "sns",
    aws_access_key_id = config.python_texter_ak,
    aws_secret_access_key = config.python_texter_sk,
    region_name = config.python_texter_region
)

client.publish(PhoneNumber = "+16148227577", Message = "Please don't reply it's Dustin texting from Amazon Web Services via Python")