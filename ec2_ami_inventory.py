import boto3
import json
import sys
from collections import defaultdict
from typing import Dict, Any

def create_default_ami_entry() -> Dict[str, Any]:
    """
    Creates a default dictionary structure for a new AMI entry
    Returns a dictionary with default values for AMI information
    """
    return {
        "ImageDescription": None,
        "ImageName": None,
        "ImageLocation": None,
        "OwnerId": None,
        "InstanceIds": []
    }

def get_ec2_ami_inventory(ec2_client) -> Dict[str, Any]:
    """
    Gather information about EC2 instances grouped by AMI.
    Returns a dictionary with AMI IDs as keys and their details as values.
    """
    result = defaultdict(create_default_ami_entry)
    
    paginator = ec2_client.get_paginator('describe_instances')
    
    for page in paginator.paginate():
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                ami_id = instance['ImageId']
                instance_id = instance['InstanceId']
                result[ami_id]['InstanceIds'].append(instance_id)
    
    unique_ami_ids = list(result.keys())
    batch_size = 100
    
    for i in range(0, len(unique_ami_ids), batch_size):
        ami_batch = unique_ami_ids[i:i + batch_size]
        try:
            ami_response = ec2_client.describe_images(ImageIds=ami_batch)
            for image in ami_response['Images']:
                ami_id = image['ImageId']
                result[ami_id].update({
                    "ImageDescription": image.get('Description'),
                    "ImageName": image.get('Name'),
                    "ImageLocation": image.get('ImageLocation'),
                    "OwnerId": image.get('OwnerId')
                })
        except Exception as e:
            print(f"Warning: Could not fetch details for some AMIs in batch {i}: {str(e)}", 
                  file=sys.stderr)
    
    return dict(result)

def get_all_regions(ec2_client):
    """Get list of all available AWS regions"""
    return [region['RegionName'] 
            for region in ec2_client.describe_regions()['Regions']]

def get_ec2_ami_inventory_multi_region() -> Dict[str, Dict[str, Any]]:
    """
    Gather EC2 instance and AMI information across all regions
    Returns a dictionary with regions as top level keys
    """
    result = {}
    regions = get_all_regions(boto3.client('ec2'))
    
    for region in regions:
        try:
            ec2_client = boto3.client('ec2', region_name=region)
            result[region] = get_ec2_ami_inventory(ec2_client)
        except Exception as e:
            print(f"Error processing region {region}: {str(e)}", file=sys.stderr)
            
    return result

if __name__ == "__main__":
    try:
        inventory = get_ec2_ami_inventory_multi_region()
        print(json.dumps(inventory, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1) 