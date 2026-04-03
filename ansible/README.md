# Ansible: Copper PostgreSQL module

This repository ships an Ansible-compatible module that applies the same PostgreSQL configuration as `cu sql execute`.

## Requirements

- **Ansible** on the machine that runs the module (usually the controller).
- **`copper` installed in the Python environment Ansible uses** (e.g. `pip install copper` or `uv pip install -e .` from a checkout).

The module imports `copper.sql.apply` and connects with `psycopg2`. Run it on a host where that environment is available—typically **`delegate_to: localhost`** with **`connection: local`**.

## Install the module for Ansible

Point Ansible’s module search path at the directory that contains `cloudutil_postgres.py`:

```ini
# ansible.cfg (next to your playbook)
[defaults]
library = ../copper/sql/ansible
```

Or copy/symlink `copper/sql/ansible/cloudutil_postgres.py` into your playbook’s `library/` directory.

## Example playbook

```yaml
- name: Apply Copper PostgreSQL config
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Provision DB objects from YAML
      cloudutil_postgres:
        config_path: "{{ playbook_dir }}/../copper/sql/example.yaml"
        state: present
      environment:
        POSTGRES_PASSWORD: "{{ lookup(‘env’, ‘POSTGRES_PASSWORD’) }}"
```

Use `state: validated` to only parse/validate the YAML (no database connection).

## Module reference

See `DOCUMENTATION` / `EXAMPLES` in `copper/sql/ansible/cloudutil_postgres.py`, and `copper/sql/USAGE.md` for the YAML schema.
