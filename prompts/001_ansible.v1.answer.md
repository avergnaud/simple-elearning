# What was created

```
ansible/
├── site.yml                          ← Main playbook
├── requirements.yml                  ← community.postgresql collection dep
├── SMOKE_TEST.md                     ← 12-step verification checklist
├── inventory/hosts.yml
├── group_vars/all/
│   ├── vars.yml                      ← Fully commented non-secret vars
│   └── vault.yml                     ← Secrets template (encrypt before use)
└── roles/
    ├── base/tasks/main.yml           ← apt upgrade, packages, system user, dirs
    ├── base/handlers/main.yml
    ├── postgres/tasks/main.yml       ← PostgreSQL user/db/pg_hba setup
    ├── postgres/handlers/main.yml
    ├── app/tasks/main.yml            ← Deploy key, git clone, venv, pip, migrate
    ├── app/templates/env.j2
    ├── gunicorn/tasks/main.yml
    ├── gunicorn/handlers/main.yml    ← "Restart Gunicorn" (notified by app role)
    ├── gunicorn/templates/gunicorn.service.j2
    ├── nginx/tasks/main.yml
    ├── nginx/handlers/main.yml       ← "Reload Nginx"
    ├── nginx/templates/elearning.conf.j2
    └── ssl/tasks/main.yml
```

# Key design decisions
First-run TLS bootstrapping — The nginx role checks for the cert with stat and sets an ssl_cert_exists fact. The Jinja2 template produces either an HTTP-only config (first run) or an HTTP-redirect + HTTPS config (cert present). site.yml runs the nginx role twice: once before ssl and once as a post_task after ssl, which is fully idempotent.

Cross-role handler — The "Restart Gunicorn" handler lives in gunicorn/handlers/main.yml but is notified by the git task in app/tasks/main.yml. Ansible merges all handlers from all roles in a play, so this works correctly.

PostgreSQL auth — Changed md5 → scram-sha-256 in pg_hba.conf because PostgreSQL 16 on Ubuntu 25.04 stores passwords as SCRAM hashes by default. MD5 auth would fail silently with a SCRAM-stored password. If you need MD5, you also need password_encryption = md5 in postgresql.conf.

Deploy key — Added vault_deploy_key to vault.yml. Generate with ssh-keygen -t ed25519, add the public key as a GitHub Deploy Key, paste the private key in vault.yml before encrypting.

Before running:

```
ansible-galaxy collection install -r ansible/requirements.yml
ansible-vault encrypt ansible/group_vars/all/vault.yml
ansible-playbook -i ansible/inventory/hosts.yml ansible/site.yml --ask-vault-pass
```