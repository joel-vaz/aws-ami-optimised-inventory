# EC2 AMI Inventory Tool

Python tool for auditing EC2 instances and their AMIs across AWS regions with production-grade reliability.

## Features

- **Multi-Region** - Automatically scans all commercial AWS regions
- **Cross-Account Support** - Resolves AMIs across linked AWS accounts
- **Scale Ready** - Handles >10k instances with memory-safe operations
- **Clear Observability** - Structured JSON output with error tracking

## Quick Start

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run inventory (default settings)
python ec2_ami_inventory.py
```

## Technical Design

### Core Implementation
- **Pagination** - Uses AWS SDK paginators for large datasets
  ```python
  paginator = ec2_client.get_paginator('describe_instances')
  for page in paginator.paginate(): ...
  ```
- **Batched Requests** - Processes AMIs in chunks of 100/request
- **Memory Safety** - Defaultdict with O(1) lookups prevents memory bloat

### Error Handling
| Error Type | Behavior | Exit Code |
|------------|----------|-----------|
| Configuration | Immediate stop | 1 |
| Partial AMI failures | Continue with errors | 2 |
| Critical API failures | Full stop | 3 |

### Performance
```text
Region Processing Flow:
1. Discover instances → 1 API call/region
2. Group AMI IDs → 100 IDs/API call
3. Validate cross-account access → OwnerID checks
```

## Output Example
```json
{
  "us-west-2": {
    "ami-0abc123": {
      "ImageDescription": "Prod API Server",
      "InstanceCount": 42,
      "CrossAccount": {
        "SourceAccount": "123456789012", 
        "Verified": true
      }
    }
  }
}
```

## Key Requirements
- Python 3.7+
- AWS credentials with EC2 read access
- boto3 >= 1.20.0

## Testing
```bash
# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Test specific functionality
pytest -k "test_cross_account_ami"
```

## Failure Recovery
- **Throttling**: Automated retries with jitter
- **Unavailable AMIs**: Skips invalid entries, logs errors
- **Region Outages**: Fails individual regions, continues others
