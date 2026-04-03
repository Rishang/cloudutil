<div align="center">

```
  ██████╗ ██████╗ ██████╗ ██████╗ ███████╗██████╗ 
 ██╔════╝██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
 ██║     ██║   ██║██████╔╝██████╔╝█████╗  ██████╔╝
 ██║     ██║   ██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗
 ╚██████╗╚██████╔╝██║     ██║     ███████╗██║  ██║
  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝
```

# 🔶 Copper

### *The Conductive Element for Multi-Cloud Operations*

**Cu — Interactive CLI for AWS, Azure, Kubernetes with fuzzy search superpowers**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Azure](https://img.shields.io/badge/Azure-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-command-reference)

</div>

---

## 🚀 Quick Start

```bash
# Install Copper
pip install -U git+https://github.com/Rishang/copper.git

# Search AWS SSM parameters interactively
cu aws ssm-parameters --prefix /app/

# Browse Kubernetes secrets with fuzzy finding
cu k secrets --all-namespaces

# Generate AWS console login URL with custom policy
cu aws login -f ./my-policy.json

# Share secrets securely via Password Pusher
cu pwpush send --note "API credentials" --days 7
```

> **💡 Pro Tip:** Every command supports interactive `fzf` selection — just type, filter, and select!  
> **🔶 Fun Fact:** `cu` is the atomic symbol for Copper — a highly conductive element, just like this tool connects you to all your clouds!

## 🎯 Why Copper?

<table>
<tr>
<td width="50%">

### 😫 Before Copper
```bash
# Multiple AWS CLI commands
aws ssm get-parameters-by-path \
  --path /app/ --recursive | jq ...

# Manual filtering and parsing
aws secretsmanager list-secrets | \
  grep "prod" | ...

# Complex kubectl queries
kubectl get secrets -A -o json | \
  jq '.items[] | ...' 
```

</td>
<td width="50%">

### 🎉 With Copper
```bash
# Interactive fuzzy search
cu aws ssm-parameters --prefix /app/
# → Opens fzf, select multiple, done!

# Beautiful formatted output
cu aws secrets --filter prod/
# → Multi-select, auto JSON parse

# Simple, interactive
cu k secrets -A
# → One command, all namespaces
```

</td>
</tr>
</table>

**Key Benefits:**
- ⚡ **10x Faster** — Interactive selection beats typing complex commands
- 🎯 **Fuzzy Search** — Find what you need without exact names
- 🎨 **Beautiful Output** — Formatted JSON, colored output, clear feedback
- 🔄 **Multi-Cloud** — AWS, Azure, Kubernetes in one unified CLI
- 🛠️ **DevOps Friendly** — Built for daily cloud operations

---

## 📚 Table of Contents

- [🎯 Why Copper?](#-why-copper)
- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
  - [Requirements](#requirements)
- [🚀 Usage](#-usage)
    - [Top-level commands](#top-level-commands)
    - [AWS Operations](#aws-operations)
      - [Console Login](#console-login)
      - [SSM Parameter Management](#ssm-parameter-management)
      - [SSM Instance Connections](#ssm-instance-connections)
      - [Secrets Manager](#secrets-manager)
      - [Decode Authorization Message](#decode-authorization-message)
      - [Advanced AWS Usage](#advanced-aws-usage)
        - [Custom Policy for Console Login](#custom-policy-for-console-login)
        - [Environment Variables](#environment-variables)
    - [Azure Operations (`az`)](#azure-operations-az)
      - [Key Vault Secrets](#key-vault-secrets)
    - [SQL Operations](#sql-operations)
    - [Kubernetes Operations](#kubernetes-operations)
      - [Kubernetes Secrets](#kubernetes-secrets)
      - [Kubernetes ConfigMaps](#kubernetes-configmaps)
      - [Kubernetes Cluster Context Switching](#kubernetes-cluster-context-switching)
    - [OS Utils](#os-utils)
      - [YAML Diff Checker](#yaml-diff-checker)
      - [Shell History](#shell-history)
    - [Taskfile Operations](#taskfile-operations)
    - [Password Pusher Operations](#password-pusher-operations)
  - [🎯 Interactive Selection](#-interactive-selection)
  - [📋 Command Reference](#-command-reference)
  - [🔧 Development](#-development)
    - [Local Development](#local-development)

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### ☁️ Cloud Platforms

#### 🟠 AWS Operations
- **🔐 Console Login** — Generate federated URLs with custom IAM policies
- **📦 SSM Parameters** — Interactive parameter store browsing
- **💻 EC2 SSM Sessions** — Direct SSH & port forwarding
- **🔑 Secrets Manager** — Browse & retrieve secrets with auto JSON parsing
- **🔓 Decode Auth Messages** — Decode IAM authorization failures

#### 🔵 Azure Operations
- **🗝️ Key Vault Secrets** — Interactive secret management
- **🎯 Filter & Search** — Quick name-based filtering

#### ⎈ Kubernetes
- **🔒 Secrets Browser** — Per-key selection with auto base64 decode
- **📋 ConfigMaps** — Interactive ConfigMap exploration
- **🔄 Context Switching** — Quick cluster context changes

</td>
<td width="50%" valign="top">

### 🛠️ DevOps Tools

#### 🗄️ SQL Management
- **📝 YAML Config** — Declarative PostgreSQL management
- **✅ Validation** — Pre-flight config checks
- **🚀 Execution** — Apply database configurations

#### 🔐 Security Tools
- **🔗 Password Pusher** — Secure temporary secret sharing
- **🎲 Password Generator** — Strong random password generation
- **⏰ Expiration Control** — Time & view-based limits

#### 🧰 Utilities
- **📊 YAML Diff** — Cross-file config comparison via JMESPath
- **📜 Shell History** — Fuzzy search through command history
- **📋 Taskfile Integration** — Direct Taskfile task execution

</td>
</tr>
</table>

### 🎯 Core Superpowers

| Feature | Description |
|---------|-------------|
| ⚡ **Fuzzy Selection** | `fzf`-powered interactive selection — type to filter, Tab to multi-select |
| 🎨 **Beautiful Output** | Rich formatting, syntax highlighting, structured JSON display |
| 🔄 **Multi-Profile** | Seamless AWS profile & region switching |
| 🚀 **Zero Config** | Works with existing AWS/Azure/kubectl configurations |
| 📦 **Batch Operations** | Multi-select support for bulk operations |

## 📦 Installation

### Option 1: Direct Install (Recommended)
```bash
pip install -U git+https://github.com/Rishang/copper.git
```

### Option 2: Build from Source
```bash
git clone https://github.com/Rishang/copper.git
cd copper
uv build
pip install ./dist/copper-*.tar.gz
```

### Requirements

<details>
<summary><b>📋 Core Requirements (click to expand)</b></summary>

| Requirement | Purpose | Install |
|-------------|---------|---------|
| **Python 3.12+** | Runtime | [python.org](https://www.python.org/downloads/) |
| **fzf** | Interactive selection | `brew install fzf` / `apt install fzf` |

</details>

<details>
<summary><b>☁️ Cloud Platform Requirements (optional)</b></summary>

| Platform | Requirement | Setup |
|----------|-------------|-------|
| **AWS** | AWS CLI + credentials | [Configure AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) |
| **Azure** | Azure CLI + login | Run `az login` |
| **Kubernetes** | kubectl + context | [Install kubectl](https://kubernetes.io/docs/tasks/tools/) |

</details>

<details>
<summary><b>🛠️ Optional Tools</b></summary>

| Tool | Purpose | Link |
|------|---------|------|
| **Taskfile** | Task automation | [taskfile.dev](https://taskfile.dev/) |
| **Password Pusher** | Secret sharing | [pwpush.com](https://pwpush.com/) |

</details>

### Quick Setup

```bash
# Install Copper
pip install -U git+https://github.com/Rishang/copper.git

# Install fzf (if not already installed)
# macOS
brew install fzf

# Linux (Ubuntu/Debian)
sudo apt install fzf

# Verify installation
cu --help
```

## 🚀 Usage

---

## 🎮 Command Overview

### Top-level commands

The main entrypoint is `cu` (see `[project.scripts]` in `pyproject.toml`). Subcommands are wired in `cloudutil/cli.py`:

| Command | Module | Purpose |
|--------|--------|---------|
| `cu aws` | `cloudutil.aws.cli` | AWS (login, SSM, Secrets Manager, decode message) |
| `cu az` | `cloudutil.azure.cli` | Azure Key Vault secrets |
| `cu sql` | `cloudutil.sql.cli` | PostgreSQL config validate / execute / init |
| `cu os` | `cloudutil.os_utils.cli` | YAML diff, shell history |
| `cu k` | `cloudutil.k8s.cli` | Kubernetes secrets, ConfigMaps, context switch |
| `cu pwpush` | `cloudutil.pwpush.cli` | Password Pusher |
| `cu task` | `cloudutil.task.cli` | Passthrough to the `task` binary |

### AWS Operations

#### Console Login

Generates a temporary AWS console login URL using STS `GetFederationToken`. A **policy JSON file is required** (`-f` / `--policy-file`).

```bash
# Policy file is required — example: read-only S3 policy in ./read-only-policy.json
cu aws login -f ./read-only-policy.json

# With profile and session duration (hours, default 2, range 1–24)
cu aws login -f ./read-only-policy.json --profile my-profile --duration 4

# Just print URL (don't open browser)
cu aws login -f ./read-only-policy.json --no-open
```

**Example output:**
```
[*] Opening URL in your default web browser...
[+] Done. Check your browser.
```

#### SSM Parameter Management

Interactively search and retrieve SSM parameters:

```bash
# Search parameters (default prefix /)
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
# Decode a message interactively (opens $EDITOR, default vim)
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
cu aws login -f ./s3-read-only.json
```

##### Environment Variables

Copper respects standard AWS environment variables:

```bash
export AWS_PROFILE=my-profile
export AWS_DEFAULT_REGION=us-west-2
cu aws ssm-parameters  # Uses the environment settings
```

### Azure Operations (`az`)

Azure commands are under **`cu az`** (not `cu azure`).

#### Key Vault Secrets

Browse and retrieve Azure Key Vault secrets with automatic JSON parsing:

```bash
# Search all secrets in a vault
cu az secrets --vault my-key-vault

# Filter by name prefix
cu az secrets --vault my-key-vault --filter "prod-"

# JSON output (quieter logging)
cu az secrets --vault my-key-vault -o json
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

### SQL Operations

PostgreSQL-oriented workflows (see `cloudutil/sql/cli.py`):

```bash
# Generate a sample YAML template (default: config.yaml)
cu sql init
cu sql init -o my-config.yaml

# Validate configuration without connecting
cu sql validate my-config.yaml

# Apply configuration
cu sql execute --config-file my-config.yaml
# short form:
cu sql execute -c my-config.yaml
```

### Kubernetes Operations

Browse Kubernetes resources interactively using `fzf`. Selected resources are printed as JSON in the terminal.

For **Secrets** and **ConfigMaps**, `fzf` lists **one line per data key**: `namespace/name/key`. Choosing a line prints **only that key’s value** (secrets are base64-decoded).

#### Kubernetes Secrets

View and inspect Secret keys. Each key appears as `namespace/secret-name/key`; values are base64-decoded when shown.

```bash
# Scan secrets across all namespaces
cu k secrets

# Scan a specific namespace
cu k secrets --namespace default

# Explicitly scan all namespaces
cu k secrets --all-namespaces
# or
cu k secrets -A

# Choose namespace interactively first, then pick secrets
cu k secrets --select-namespace
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
cu k configmaps

# Scan a specific namespace
cu k configmaps --namespace kube-system

# Explicitly scan all namespaces
cu k configmaps --all-namespaces
# or
cu k configmaps -A

# Choose namespace interactively first, then pick ConfigMaps
cu k configmaps --select-namespace
```

**Example output** (one selected key):
```
{
  "kube-system/coredns": {
    "Corefile": ".:53 {\n    errors\n    health\n    kubernetes cluster.local in-addr.arpa ip6.arpa\n    ...\n}"
  }
}
```

#### Kubernetes Cluster Context Switching

Switch kube contexts interactively using `fzf`.

```bash
# Pick a context from kubeconfig and switch to it
cu k ctx
```

Notes:
- Context names are read from your current kubeconfig (`kubectl config view -o json`).
- The selected context is applied with `kubectl config use-context` (process is replaced via `exec`).

### OS Utils

Utilities for local/dev workflows and config validation tasks.

#### YAML Diff Checker

Compare YAML nodes across files at a given JMESPath location and report:
- missing keys on either side
- value differences
- matching keys
- ignored keys based on patterns

Default config file: `ydiff_config.yaml` in the current directory.

```bash
cu os ydiff

# Custom config
cu os ydiff --config ./cloudutil/os_utils/example.yaml
cu os ydiff -c ./my-ydiff.yaml
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

Search shell history with fzf (supports zsh and bash).

```bash
cu os history
```

### Taskfile Operations

Run [Taskfile](https://taskfile.dev/) tasks through Copper. `cu task` replaces the current process with `task`, forwarding extra arguments for full interactive TTY behavior.

Default Taskfile: `~/.config/cu/Taskfile.yml`. Default directory: current working directory.

```bash
# Run default task
cu task default

# Run any task with additional flags/args (after --)
cu task deploy -- --env prod

# Custom Taskfile and working directory
cu task -t ./Taskfile.yml -d /path/to/project default
cu task --taskfile ./Taskfile.yml --directory . deploy

# Task passthrough help
cu task --help
```

### Password Pusher Operations

Manage temporary secret sharing with [Password Pusher](https://pwpush.com/) (`cloudutil/pwpush/cli.py`).

```bash
# Save Password Pusher config (requires --token, --source, and --email)
cu pwpush config --source https://pwpush.com --token <api-token> --email you@example.com

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
- `send` uses bearer auth when no email is stored in config; legacy header auth when `email` is present in the saved config.

## 🎯 Interactive Selection

All commands use `fzf` for interactive selection, providing:

- **Fuzzy matching** - Type partial names to filter
- **Multi-select** - Use `Tab` to select multiple items
- **Real-time filtering** - Instant results as you type
- **Keyboard shortcuts** - Standard fzf navigation

## 📋 Command Reference

| Group | Commands |
|-------|----------|
| `cu aws` | `login`, `ssm-parameters`, `ec2-ssm`, `secrets`, `decode-message` |
| `cu az` | `secrets` |
| `cu sql` | `execute`, `validate`, `init` |
| `cu os` | `ydiff`, `history` |
| `cu k` | `secrets`, `configmaps`, `ctx` |
| `cu pwpush` | `config`, `send`, `list-active`, `pwgen` |
| `cu task` | forwards to `task -t <taskfile> -d <dir> ...` |

Run `cu --help` and `cu <group> --help` for live usage.

## 🔧 Development

### Local Development

```bash
git clone https://github.com/Rishang/copper.git
cd copper

# Install dependencies (creates .venv when using uv)
uv sync

# Run the CLI (console script from pyproject)
uv run cu --help

# Or activate the venv and run cu directly
source .venv/bin/activate
cu --help
```

---

<div align="center">

### 🔶 Copper — Highly Conductive Cloud Operations

<p>Made with ❤️ for the Cloud & DevOps community</p>

<p>
  <a href="https://github.com/Rishang/copper/issues">🐛 Report Bug</a>
  ·
  <a href="https://github.com/Rishang/copper/issues">✨ Request Feature</a>
  ·
  <a href="https://github.com/Rishang/copper/discussions">💬 Discussions</a>
</p>

<p>
  <sub>Cu — Atomic number 29 — Connecting your clouds since 2024</sub>
</p>

</div>
