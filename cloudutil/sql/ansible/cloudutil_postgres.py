#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) CloudUtil contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Ansible module: apply CloudUtil PostgreSQL YAML configuration."""

from __future__ import annotations

import traceback

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: cloudutil_postgres
short_description: Provision PostgreSQL databases, extensions, users, and privileges from CloudUtil YAML
description:
  - Applies the same schema as C(cu sql execute) / C(cu sql validate).
  - Requires the C(cloudutil) Python package (and dependencies such as C(psycopg2-binary)) on the host where the module runs (usually the Ansible controller with C(connection: local), or the target if you delegate).
version_added: "0.2.0"
options:
  config_path:
    description:
      - Path to a YAML file using the CloudUtil SQL schema (see I(cloudutil/sql/example.yaml) in the repository).
    type: path
    required: false
  config:
    description:
      - Inline configuration as a dictionary (same structure as the YAML file).
    type: dict
    required: false
  provider:
    description:
      - Reserved for future providers. Only C(postgres) is implemented.
    type: str
    default: postgres
    choices:
      - postgres
  state:
    description:
      - C(present) connects and applies configuration.
      - C(validated) only parses and validates configuration (no database connection).
    type: str
    default: present
    choices:
      - present
      - validated
requirements:
  - cloudutil
  - psycopg2-binary
seealso:
  - name: CloudUtil SQL usage
    description: Configuration schema and examples.
    link: https://github.com/Rishang/cloudutil/blob/main/cloudutil/sql/USAGE.md
author:
  - CloudUtil contributors
"""

EXAMPLES = r"""
- name: Apply SQL config from a file on the controller
  cloudutil_postgres:
    config_path: /opt/app/sql/example.yaml
  environment:
    POSTGRES_PASSWORD: "{{ vault_postgres_password }}"
    APP_SERVICE_PASSWORD: "{{ vault_app_password }}"
  delegate_to: localhost
  connection: local

- name: Inline config (passwords via environment or Ansible vars resolved in the dict)
  cloudutil_postgres:
    config:
      provider:
        name: postgres
        version: 17
        host: "{{ db_host }}"
        port: 5432
        username: postgres
        password: "{{ postgres_password }}"
      database:
        - name: myapp
          create: true
          extensions: []
      users: []
  delegate_to: localhost
  connection: local

- name: Validate YAML only (no DB connection)
  cloudutil_postgres:
    config_path: /opt/app/sql/example.yaml
    state: validated
  delegate_to: localhost
  connection: local
"""

RETURN = r"""
changed:
  description: Whether any create or update operation was performed.
  type: bool
  returned: always
changes:
  description: List of change reports from the PostgreSQL provider.
  type: list
  elements: dict
  returned: when state is present
"""


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "config_path": {"type": "path", "required": False},
            "config": {"type": "dict", "required": False},
            "provider": {
                "type": "str",
                "default": "postgres",
                "choices": ["postgres"],
            },
            "state": {
                "type": "str",
                "default": "present",
                "choices": ["present", "validated"],
            },
        },
        mutually_exclusive=[["config", "config_path"]],
        required_one_of=[["config", "config_path"]],
        supports_check_mode=False,
    )

    try:
        from cloudutil.sql.apply import apply_postgres_config, validate_postgres_config
    except ImportError as exc:
        module.fail_json(
            msg="The cloudutil package must be installed to use this module "
            "(e.g. pip install cloudutil).",
            exception=str(exc),
        )

    if module.params["provider"] != "postgres":
        module.fail_json(msg="Only provider 'postgres' is supported.")

    state = module.params["state"]
    config = module.params["config"]
    config_path = module.params["config_path"]

    try:
        if state == "validated":
            validate_postgres_config(config=config, config_path=config_path)
            module.exit_json(changed=False, validated=True)
        else:
            changed, changes = apply_postgres_config(
                config=config, config_path=config_path
            )
            module.exit_json(changed=changed, changes=changes)
    except FileNotFoundError as exc:
        module.fail_json(msg=str(exc))
    except ValueError as exc:
        module.fail_json(msg=str(exc))
    except Exception as exc:
        module.fail_json(
            msg=str(exc),
            exception=traceback.format_exc(),
        )


if __name__ == "__main__":
    main()
