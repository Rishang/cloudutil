# ☁️ CloudUtil

CLI `cu` is a wrapper for most common AWS and Azure cloud operations with interactive selection and beautiful output.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-Cloud-orange.svg)](https://aws.amazon.com/)
[![Azure](https://img.shields.io/badge/Azure-Cloud-blue.svg)](https://azure.microsoft.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Cloud-blue.svg)](https://kubernetes.io/)

```bash
pip install -U git+https://github.com/Rishang/cloudutil.git
```

## 📚 Table of Contents

- [☁️ CloudUtil](#️-cloudutil)
  - [📚 Table of Contents](#-table-of-contents)
  - [✨ Features](#-features)
  - [📦 Installation](#-installation)
    - [Requirements](#requirements)
  - [🚀 Usage](#-usage)
    - [AWS Operations](#aws-operations)
      - [Console Login](#console-login)
      - [SSM Parameter Management](#ssm-parameter-management)
      - [SSM Instance Connections](#ssm-instance-connections)
      - [Secrets Manager](#secrets-manager)
      - [Decode Authorization Message](#decode-authorization-message)
      - [Advanced AWS Usage](#advanced-aws-usage)
        - [Custom Policy for Console Login](#custom-policy-for-console-login)
        - [Environment Variables](#environment-variables)
    - [Azure Operations](#azure-operations)
      - [Key Vault Secrets](#key-vault-secrets)
    - [OS Utils](#os-utils)
      - [YAML Diff Checker](#yaml-diff-checker)
      - [Shell History](#shell-history)
    - [Taskfile Operations](#taskfile-operations)
    - [Password Pusher Operations](#password-pusher-operations)
    - [SQL Operations](#sql-operations)
    - [Kubernetes Operations](#kubernetes-operations)
      - [Kubernetes Secrets](#kubernetes-secrets)
      - [Kubernetes ConfigMaps](#kubernetes-configmaps)
  - [🎯 Interactive Selection](#-interactive-selection)
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
- 🐍 **SQL Database Management** - Simple, type-safe database configuration management for PostgreSQL
- 🎛️ **Kubernetes Operations** - Interactive Kubernetes secrets and ConfigMaps browsing via `kubectl`
- 🧰 **OS Utils** - YAML diff checker for cross-file config comparisons using JMESPath
- 🗂️ **Taskfile Passthrough** - Run local Taskfile tasks via `cu task ...` with interactive terminal support
- 🔐 **Password Pusher Integration** - Configure Password Pusher, share secrets, and generate strong passwords

## 📦 Installation

```bash
pip install -U git+https://github.com/Rishang/cloudutil.git
```

OR

```bash
git clone https://github.com/Rishang/cloudutil.git && cd cloudutil && uv build && pip install ./dist/cloudutil-*.tar.gz
```

### Requirements

- Python 3.12+
- `fzf` for interactive selection
- [Only for AWS operations] AWS CLI configured with credentials
- [Only for Azure operations] Azure CLI (`az login` must be run primarily)
- [Only for Kubernetes operations] `kubectl` configured with access to your target cluster
- [Only for Taskfile operations] [Taskfile](https://taskfile.dev/) installed and configured

```bash
# Install fzf (if not already installed)
# macOS
brew install fzf

# Ubuntu/Debian
sudo apt install fzf

# Or follow: https://github.com/junegunn/fzf#installation
```

## 🚀 Usage

### AWS Operations

#### Console Login

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

#### SSM Parameter Management

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

#### SSM Instance Connections

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

#### Secrets Manager

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

#### Decode Authorization Message

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

#### Advanced AWS Usage

##### Custom Policy for Console Login

Create a JSON policy file to restrict console permissions:

```json
{
  "Version": "2012-10-17",
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

##### Environment Variables

CloudUtil respects standard AWS environment variables:

```bash
export AWS_PROFILE=my-profile
export AWS_DEFAULT_REGION=us-west-2
cu aws ssm-parameters  # Uses the environment settings
```

### Azure Operations

#### Key Vault Secrets

Browse and retrieve Azure Key Vault secrets with automatic JSON parsing:

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

### OS Utils

Utilities for local/dev workflows and config validation tasks.

#### YAML Diff Checker

Compare YAML nodes across files at a given JMESPath location and report:
- missing keys on either side
- value differences
- matching keys
- ignored keys based on patterns

```bash
# Use default config path: ./ydiff_config.yaml
cu os ydiff

# Use a custom config file
cu os ydiff --config ./cloudutil/os_utils/example.yaml
```

**Config format (`ydiff_config.yaml`):**

```yaml
ydiff:
  - jsmec: "configMap"
    files:
      - app-v1: "./values/main.yaml"
      # $branch is resolved to the current git branch name for that file path.
      - $branch: "./values/feature.yaml"
    ignore_patterns:
      - test
      - dev
```

Notes:
- `jsmec` is the JMESPath expression used to extract the node to compare.
- Every item under `files` is a single-key mapping: `{alias: path}`.
- At least 2 files are required per check.
- You can use `$branch` as an alias to auto-resolve the current git branch name for that file path.

#### Shell History

Search shell history with fzf.

```bash
cu os history
```

### Taskfile Operations

Run [Taskfile](https://taskfile.dev/) tasks directly through CloudUtil.

`cu task` forwards arguments to `task` and preserves interactive TTY behavior, so prompts/selectors work as expected.

```bash
# Run default task
cu task default

# Run any task with additional flags/args
cu task deploy -- --env prod

# Use a custom Taskfile
cu task --yaml-file ./Taskfile.yml default

# Open task's own help
cu task --help
```

### Password Pusher Operations

Manage temporary secret sharing with [Password Pusher](https://pwpush.com/).

```bash
# Save Password Pusher config
cu pwpush config --source https://pwpush.com --token <api-token>

# Optional legacy/self-hosted auth mode
cu pwpush config --source https://pwpush.example.com --token <api-token> --email you@example.com

# Send a secret (opens $EDITOR if --file is omitted)
cu pwpush send --note "prod db password" --days 7 --views 5

# Send secret from file
cu pwpush send --file ./secret.txt --note "vpn creds"

# List active pushes
cu pwpush list-active

# Generate a random password
cu pwpush pwgen --length 24
```

Notes:
- Config is stored at `~/.config/cu/psst.json`.
- `send` uses bearer auth by default; if `--email` is configured, it uses legacy auth headers.

### SQL Operations

In progress...

### Kubernetes Operations

Browse Kubernetes resources interactively using `fzf`. Selected resources are printed as JSON in the terminal.

For **Secrets** and **ConfigMaps**, `fzf` lists **one line per data key**: `namespace/name/key`. Choosing a line prints **only that key’s value** (secrets are base64-decoded).

#### Kubernetes Secrets

View and inspect Secret keys. Each key appears as `namespace/secret-name/key`; values are base64-decoded when shown.

```bash
# Scan secrets across all namespaces
cu k8s secrets

# Scan a specific namespace
cu k8s secrets --namespace default

# Explicitly scan all namespaces
cu k8s secrets -A

# Choose namespace interactively first, then pick secrets
cu k8s secrets --select-namespace
```

**Example output** (one selected key):
```
{
  "default/app-secret": {
    "DATABASE_URL": "postgres://app:***@db:5432/app"
  }
}
```

#### Kubernetes ConfigMaps

View and inspect ConfigMap keys. Each key appears as `namespace/configmap-name/key`, with the same namespace flags as secrets.

```bash
# Scan ConfigMaps across all namespaces
cu k8s configmaps

# Scan a specific namespace
cu k8s configmaps --namespace kube-system

# Explicitly scan all namespaces
cu k8s configmaps --all-namespaces

# Choose namespace interactively first, then pick ConfigMaps
cu k8s configmaps --select-namespace
```

**Example output** (one selected key):
```
{
  "kube-system/coredns": {
    "Corefile": ".:53 {\n    errors\n    health\n    kubernetes cluster.local in-addr.arpa ip6.arpa\n    ...\n}"
  }
}
```

## 🎯 Interactive Selection

All commands use `fzf` for interactive selection, providing:

- **Fuzzy matching** - Type partial names to filter
- **Multi-select** - Use `Tab` to select multiple items
- **Real-time filtering** - Instant results as you type
- **Keyboard shortcuts** - Standard fzf navigation

## 📋 Command Reference

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
  <p>Made with ❤️ for the Cloud community</p>
  <p>
    <a href="https://github.com/Rishang/cloudutil/issues">Report Bug</a>
    ·
    <a href="https://github.com/Rishang/cloudutil/issues">Request Feature</a>
  </p>
</div>
