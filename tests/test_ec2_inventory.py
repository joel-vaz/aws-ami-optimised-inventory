import sys
from pathlib import Path

# Add parent directory to Python path to import ec2_ami_inventory
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from unittest.mock import patch, MagicMock
from ec2_ami_inventory import (
    create_default_ami_entry,
    get_ec2_ami_inventory,
    get_all_regions
)

class TestEC2AMIInventory(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_instance_response = {
            'Reservations': [{
                'Instances': [
                    {'ImageId': 'ami-123', 'InstanceId': 'i-abc'},
                    {'ImageId': 'ami-123', 'InstanceId': 'i-def'},
                    {'ImageId': 'ami-456', 'InstanceId': 'i-xyz'}
                ]
            }]
        }
        
        self.mock_images_response = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Description': 'Test AMI 1',
                    'Name': 'test-ami-1',
                    'ImageLocation': 'aws-marketplace/test1',
                    'OwnerId': '123456789012'
                },
                {
                    'ImageId': 'ami-456',
                    'Description': 'Test AMI 2',
                    'Name': 'test-ami-2',
                    'ImageLocation': 'aws-marketplace/test2',
                    'OwnerId': '123456789012'
                }
            ]
        }

    def test_create_default_ami_entry(self):
        """Test default AMI entry creation"""
        entry = create_default_ami_entry()
        self.assertIsNone(entry['ImageDescription'])
        self.assertIsNone(entry['ImageName'])
        self.assertIsNone(entry['ImageLocation'])
        self.assertIsNone(entry['OwnerId'])
        self.assertEqual(entry['InstanceIds'], [])

    @patch('boto3.client')
    def test_get_all_regions(self, mock_boto):
        """Test region listing functionality"""
        mock_ec2 = MagicMock()
        mock_ec2.describe_regions.return_value = {
            'Regions': [
                {'RegionName': 'us-east-1'},
                {'RegionName': 'us-west-2'}
            ]
        }
        mock_boto.return_value = mock_ec2

        regions = get_all_regions(mock_ec2)
        self.assertEqual(regions, ['us-east-1', 'us-west-2'])

    @patch('boto3.client')
    def test_get_ec2_ami_inventory(self, mock_boto):
        """Test main inventory collection functionality"""
        # Setup mock EC2 client
        mock_ec2 = MagicMock()
        
        # Mock paginator
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [self.mock_instance_response]
        mock_ec2.get_paginator.return_value = mock_paginator
        
        # Mock describe_images
        mock_ec2.describe_images.return_value = self.mock_images_response

        # Execute test
        result = get_ec2_ami_inventory(mock_ec2)

        # Verify results
        self.assertIn('ami-123', result)
        self.assertIn('ami-456', result)
        self.assertEqual(len(result['ami-123']['InstanceIds']), 2)
        self.assertEqual(len(result['ami-456']['InstanceIds']), 1)
        self.assertEqual(result['ami-123']['ImageName'], 'test-ami-1')

    @patch('boto3.client')
    def test_error_handling(self, mock_boto):
        """Test error handling for API failures"""
        mock_ec2 = MagicMock()
        
        # Mock paginator for successful instance retrieval
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [self.mock_instance_response]
        mock_ec2.get_paginator.return_value = mock_paginator
        
        # Mock describe_images to fail
        mock_ec2.describe_images.side_effect = Exception("API Error")

        # Execute test
        result = get_ec2_ami_inventory(mock_ec2)

        # Verify error handling
        self.assertIn('ami-123', result)
        self.assertIsNone(result['ami-123']['ImageName'])
        self.assertIn('i-abc', result['ami-123']['InstanceIds'])

if __name__ == '__main__':
    unittest.main() 