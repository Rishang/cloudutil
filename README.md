# ☁️ CloudUtil

A powerful CLI wrapper for daily AWS cloud operations with interactive selection and beautiful output.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-Cloud-orange.svg)](https://aws.amazon.com/)

## 📚 Table of Contents

- [☁️ CloudUtil](#️-cloudutil)
  - [📚 Table of Contents](#-table-of-contents)
  - [✨ Features](#-features)
  - [📦 Installation](#-installation)
    - [Requirements](#requirements)
  - [🚀 Usage](#-usage)
    - [AWS Console Login](#aws-console-login)
    - [SSM Parameter Management](#ssm-parameter-management)
    - [SSM Instance Connections](#ssm-instance-connections)
    - [Secrets Manager](#secrets-manager)
    - [Azure Key Vault Secrets](#azure-key-vault-secrets)
    - [Decode Authorization Message](#decode-authorization-message)
  - [🎯 Interactive Selection](#-interactive-selection)
  - [🛠️ Advanced Usage](#️-advanced-usage)
    - [Custom Policy for Console Login](#custom-policy-for-console-login)
    - [Environment Variables](#environment-variables)
  - [📋 Command Reference](#-command-reference)
  - [🔧 Development](#-development)
    - [Local Development](#local-development)

## ✨ Features

- 🚀 **Interactive AWS Console Login** - Generate federated console URLs with custom policies
- 🔐 **SSM Parameter Management** - Search and retrieve parameters with fuzzy finding
- 📡 **SSM Instance Connections** - Direct SSH and port forwarding through Systems Manager
- 🔑 **Secrets Manager Integration** - Interactive secret browsing with JSON formatting
- 🎯 **Fuzzy Selection** - Powered by `fzf` for lightning-fast interactive selection
- 🎨 **Beautiful Output** - Rich terminal interface with colors and formatting
- ⚡ **Profile & Region Support** - Seamless switching between AWS profiles and regions

## 📦 Installation

```bash
pip install -U git+https://github.com/Rishang/cloudutil.git
```

### Requirements

- Python 3.8+
- AWS CLI configured with credentials
- Azure CLI (`az login` must be run primarily)
- `fzf` for interactive selection
- [AWS Session Manager Plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

```bash
# Install fzf (if not already installed)
# macOS
brew install fzf

# Ubuntu/Debian
sudo apt install fzf

# Or follow: https://github.com/junegunn/fzf#installation
```

## 🚀 Usage

### AWS Console Login

Generate a temporary AWS console login URL with optional policy restrictions:

```bash
# Basic console login
cu aws login

# With custom profile and region
cu aws login --profile my-profile --region us-west-2

# With custom duration and policy file
cu aws login --duration 3600 --policy-file ./read-only-policy.json

# Just print URL (don't open browser)
cu aws login --no-open
```

**Example output:**
```
[*] Opening URL in your default web browser...
[+] Done. Check your browser.
```

### SSM Parameter Management

Interactively search and retrieve SSM parameters:

```bash
# Search all parameters
cu aws ssm-parameters

# Search with prefix
cu aws ssm-parameters --prefix /app/production/

# With specific profile and region
cu aws ssm-parameters --prefix /app/ --profile prod --region eu-west-1
```

**Example workflow:**
```
[*] Listing SSM parameters with prefix: /app/production/
[*] Found 24 parameters. Opening fzf for selection...
[*] Retrieving 3 selected parameters...
[+] Parameters retrieved successfully.

{
  "name": "/app/production/database/host",
  "value": "prod-db.example.com"
}
{
  "name": "/app/production/api/key",
  "value": "secret-api-key-value"
}
```

### SSM Instance Connections

Connect to EC2 instances through Systems Manager:

```bash
# Interactive instance selection and direct connection
cu aws ec2-ssm

# Port forwarding tunnel
cu aws ec2-ssm --tunnel --remote-host localhost --remote-port 5432 --local-port 5432
```

**Example workflow:**
```
[*] Found 8 instances. Opening fzf for selection...
# Select: i-0123456789abcdef0 | web-server-prod
# Connects directly to the instance via SSM
```

### Secrets Manager

Browse and retrieve secrets with automatic JSON parsing:

```bash
# Search all secrets
cu aws secrets

# Filter by name prefix
cu aws secrets --filter "prod/"

# With specific profile and region
cu aws secrets --filter "app/" --profile production --region us-east-1
```

**Example output:**
```
[*] Found 12 secrets. Opening fzf for selection...
[*] Retrieving 2 selected secrets...
[+] Secrets retrieved successfully.


Name: 'prod/database/credentials'
Description: 'Production database credentials'
ARN: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/database/credentials-AbCdEf'
Value (JSON):
{
  "username": "admin",
  "password": "super-secure-password",
  "host": "prod-db.example.com",
  "port": 5432
}
```

### Azure Key Vault Secrets

Browse and retrieve Azure Key Vault secrets with automatic JSON parsing (similar to AWS Secrets Manager):

```bash
# Search all secrets in a vault
cu azure secrets --vault my-key-vault

# Filter by name prefix
cu azure secrets --vault my-key-vault --filter "prod-"
```

**Example output:**
```
[*] Listing secrets from vault my-key-vault with filter: prod-
[*] Found 5 secrets. Opening fzf for selection...
[*] Retrieving 1 selected secrets...
[+] Secrets retrieved successfully.

Name: 'prod-db-password'
Content Type: 'password'
ID: 'https://my-key-vault.vault.azure.net/secrets/prod-db-password/...'
Value:
super-secret-value
```

### Decode Authorization Message

Decode an AWS authorization failure message using IAM's `decode_authorization_message` API:

```bash
# Decode a message interactively (opens vim)
cu aws decode-message

# Decode a specific message
cu aws decode-message --message "AQAA...<encoded message>..."
```

**Example output:**
```
{
  "allowed_actions": [],
  "denied_actions": [
    {
      "actions": ["s3:GetObject"],
      "api_call": "GetObject",
      "main_type": "s3",
      "condition": {},
      "resource": "arn:aws:s3:::my-bucket/*",
      "type": "s3",
      "condition_text": "",
      "effective_action": "s3:GetObject",
      "reason": "Access Denied",
      "encoded_error_message": "Access Denied"
    }
  ],
  "encoded_message": "AQAA...",
  "decoded_error": "Access Denied",
  "decoded_message": "The provided authorization message is invalid or has expired."
}
```

## 🎯 Interactive Selection

All commands use `fzf` for interactive selection, providing:

- **Fuzzy matching** - Type partial names to filter
- **Multi-select** - Use `Tab` to select multiple items
- **Real-time filtering** - Instant results as you type
- **Keyboard shortcuts** - Standard fzf navigation

## 🛠️ Advanced Usage

### Custom Policy for Console Login

Create a JSON policy file to restrict console permissions:

```json
{
  "Version": "2012-10-17",
| `decode-message` | Decode authorization failure message | `--message` |
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": "*"
    }
  ]
}
```

```bash
cloudutil aws-login --policy-file ./s3-read-only.json
```

### Environment Variables

CloudUtil respects standard AWS environment variables:

```bash
export AWS_PROFILE=my-profile
export AWS_DEFAULT_REGION=us-west-2
cu aws ssm-parameters  # Uses the environment settings
```


## 🔧 Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/Rishang/cloudutil.git
cd cloudutil

# Install in development mode
uv sync

# Activate the virtual environment
poetry shell

# Run the CLI
cd src/cloudutil && python3 cli.py
```

---

<div align="center">
  <p>Made with ❤️ for the AWS community</p>
  <p>
    <a href="https://github.com/Rishang/cloudutil/issues">Report Bug</a>
    ·
    <a href="https://github.com/Rishang/cloudutil/issues">Request Feature</a>
  </p>
</div>
