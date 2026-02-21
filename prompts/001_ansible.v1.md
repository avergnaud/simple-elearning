# Ansible Playbook Generation Prompt

## instructions

The following prompt was designed to be self-contained — it carries all the context Claude needs. If you paste it into an existing session, prior conversation context could interfere with Claude's output. A fresh session gives you a clean, reproducible result that matches your audit log exactly.

### Step 1 — Open a new Claude Code session
Start fresh so you have no conversation context interfering. You can do this with:

claude in a terminal (starts a new session)
Or /clear if you're already in a session

### Step 2 — Paste only the inner prompt
See below "The Prompt (ready to copy-paste)"

### Step 3 — Let Claude generate
Claude will produce all the Ansible files inline. 

### Step 4 — Fill in your CHANGEME values
After the files are written, edit:
```
ansible/inventory/hosts.yml → replace CHANGEME with your OVH server IP
ansible/group_vars/all/vars.yml → set git_repo_url, certbot_email, platform_name
ansible/group_vars/all/vault.yml → fill in secrets, then run ansible-vault encrypt group_vars/all/vault.yml
```


## The Prompt (ready to copy-paste)

```
## Context

I need a complete, production-ready Ansible playbook to provision and deploy a Django
5.x e-learning platform (quiz-only MVP) on a fresh Ubuntu 25.04 VPS.

Everything must be idempotent: running the playbook twice produces no errors and no
duplicate state. Produce every file in full — do not truncate or use "..." to omit
content.

---

## Target Environment

- OS: Ubuntu 25.04 on OVH IaaS VPS
- Domain: appsec.cc (DNS A record already points to the server)
- SSH user: ubuntu
- Python: 3.12
- Database: PostgreSQL 16
- App server: Gunicorn (3 workers, bound to 127.0.0.1:8000, managed by systemd)
- Web server: Nginx (HTTP→HTTPS redirect on port 80, HTTPS reverse proxy on port 443,
  static and media file serving)
- TLS: Let's Encrypt via Certbot, auto-renewal via systemd timer
- Secrets: python-decouple reads /opt/elearning/.env — managed by Ansible via
  ansible-vault
- No Docker, no cloud storage, no Celery, no Redis — direct host deployment only

---

## Application Layout (repository already exists)

The Django project lives at /opt/elearning/ on the server after cloning. Its structure:

  /opt/elearning/
  ├── manage.py
  ├── requirements.txt
  ├── elearning/
  │   ├── settings/
  │   │   ├── base.py
  │   │   ├── development.py
  │   │   └── production.py
  │   ├── urls.py
  │   └── wsgi.py
  └── apps/
      ├── accounts/
      ├── quizzes/
      ├── enrolments/
      └── reporting/

Static files are collected to /var/www/elearning/static/.
Media files are stored at /var/www/elearning/media/.

The git repository is hosted on GitHub and cloned via SSH using a deploy key. See git_repo_url.

---

## Required Ansible Project Structure

Produce all files for this layout:

  ansible/
  ├── inventory/
  │   └── hosts.yml
  ├── group_vars/
  │   └── all/
  │       ├── vars.yml          (non-secret variables, fully commented)
  │       └── vault.yml         (ansible-vault template listing all secrets)
  ├── roles/
  │   ├── base/
  │   │   ├── tasks/main.yml
  │   │   └── handlers/main.yml
  │   ├── postgres/
  │   │   └── tasks/main.yml
  │   ├── app/
  │   │   ├── tasks/main.yml
  │   │   └── templates/env.j2
  │   ├── gunicorn/
  │   │   ├── tasks/main.yml
  │   │   ├── handlers/main.yml
  │   │   └── templates/gunicorn.service.j2
  │   ├── nginx/
  │   │   ├── tasks/main.yml
  │   │   ├── handlers/main.yml
  │   │   └── templates/elearning.conf.j2
  │   └── ssl/
  │       └── tasks/main.yml
  └── site.yml

---

## Role Responsibilities

### base
- apt update + full-upgrade (non-interactive)
- Install packages: python3.12 python3.12-venv python3-pip git curl nginx
  postgresql-16 libpq-dev
- Install WeasyPrint system dependencies:
  libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
- Install Certbot via snap (NOT apt): `snap install --classic certbot`
  then create the symlink: `ln -sf /snap/bin/certbot /usr/bin/certbot`
  Use ansible.builtin.command for both steps (idempotent: check snap list first,
  and use creates: /usr/bin/certbot for the symlink)
- Create a dedicated system user `elearning` (system account, no login shell)
- Create directories owned by the elearning user:
  /opt/elearning, /var/www/elearning/static, /var/www/elearning/media

### postgres
- Ensure the postgresql service is started and enabled
- Create PostgreSQL user elearning_user with password from vault
- Create database elearning_db owned by elearning_user
- Ensure pg_hba.conf allows MD5 auth for elearning_user from localhost
- All tasks must be idempotent (do not drop/recreate if already exists)

### app
- Clone the git repository into /opt/elearning via SSH (git_repo_url variable)
  - Use the ansible.builtin.git module with update: yes, force: no
  - Register the result; notify Gunicorn restart handler if changed
- Create virtualenv at /opt/elearning/venv using python3.12
- Install requirements.txt into the virtualenv (pip install -r)
- Deploy /opt/elearning/.env from templates/env.j2 (owner: elearning, mode: 0600)
- Run migrate: /opt/elearning/venv/bin/python manage.py migrate --no-input
  with DJANGO_SETTINGS_MODULE=elearning.settings.production
- Run collectstatic: /opt/elearning/venv/bin/python manage.py collectstatic --no-input
  with the same settings module

### gunicorn
- Deploy systemd unit from templates/gunicorn.service.j2 to
  /etc/systemd/system/elearning-gunicorn.service
- Reload systemd daemon after deploying the unit file
- Enable and start the elearning-gunicorn service
- Handler: restart elearning-gunicorn (triggered by app role when code changes)

### nginx
- Deploy templates/elearning.conf.j2 to /etc/nginx/sites-available/elearning
- Create symlink: /etc/nginx/sites-enabled/elearning
- Remove /etc/nginx/sites-enabled/default if present
- Handler: reload nginx (triggered when config changes)

The Nginx config must have two server blocks:

  Block 1 — HTTP redirect (port 80):
    listen 80;
    server_name appsec.cc www.appsec.cc;
    return 301 https://appsec.cc$request_uri;

  Block 2 — HTTPS (port 443):
    listen 443 ssl;
    server_name appsec.cc www.appsec.cc;
    ssl_certificate     /etc/letsencrypt/live/appsec.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/appsec.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;   ← guard with a stat check so
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;      ← Nginx role doesn't fail
                                                           on first run (before SSL role)
    location /static/ { alias /var/www/elearning/static/; }
    location /media/  { alias /var/www/elearning/media/;  }
    location / {
      proxy_pass http://127.0.0.1:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
    }

Note: on the very first provisioning, the Let's Encrypt certificate does not yet
exist when the nginx role runs. Handle this gracefully — use a conditional include
for the SSL-related lines, or produce a self-signed placeholder approach, or use
a variable (ssl_configured: false/true) so Nginx can start with HTTP only on first
run and the ssl role enables HTTPS on the same playbook run.

### ssl
- Check if /etc/letsencrypt/live/appsec.cc/fullchain.pem already exists
- If not, run certbot --nginx -d appsec.cc -d www.appsec.cc
  --non-interactive --agree-tos --email {{ certbot_email }}
  (add --staging flag when certbot_staging: true)
- Ensure the certbot renewal systemd timer is enabled and started.
  The snap installation uses the timer name `snap.certbot.renew.timer`
  (NOT `certbot.timer`, which belongs to the deprecated apt-based install)

---

## Variables

### vars.yml — produce with these variables and comments:

  app_user: elearning
  app_dir: /opt/elearning
  venv_dir: /opt/elearning/venv
  static_root: /var/www/elearning/static
  media_root: /var/www/elearning/media
  git_repo_url: git@github.com:avergnaud/simple-elearning.git
  git_branch: main
  django_settings_module: elearning.settings.production
  domain: appsec.cc
  certbot_email: CHANGEME         # email for Let's Encrypt notifications
  certbot_staging: false          # set true for first test run to avoid rate limits
  gunicorn_workers: 3
  gunicorn_bind: "127.0.0.1:8000"
  platform_name: "E-Learning Platform"   # shown on certificates

### vault.yml — produce as a commented template (not yet encrypted):

  vault_db_password: CHANGEME
  vault_django_secret_key: CHANGEME
  vault_entra_client_id: CHANGEME
  vault_entra_client_secret: CHANGEME
  vault_entra_tenant_id: CHANGEME

  # To encrypt: ansible-vault encrypt group_vars/all/vault.yml

---

## Template Details

### env.j2 (/opt/elearning/.env):

  DJANGO_SECRET_KEY={{ vault_django_secret_key }}
  DJANGO_SETTINGS_MODULE={{ django_settings_module }}
  DATABASE_URL=postgres://elearning_user:{{ vault_db_password }}@localhost/elearning_db
  ENTRA_CLIENT_ID={{ vault_entra_client_id }}
  ENTRA_CLIENT_SECRET={{ vault_entra_client_secret }}
  ENTRA_TENANT_ID={{ vault_entra_tenant_id }}
  ALLOWED_HOSTS={{ domain }},www.{{ domain }}
  PLATFORM_NAME={{ platform_name }}

### gunicorn.service.j2:

  [Unit]
  Description=Gunicorn for E-Learning Platform
  After=network.target postgresql.service

  [Service]
  User={{ app_user }}
  WorkingDirectory={{ app_dir }}
  EnvironmentFile={{ app_dir }}/.env
  ExecStart={{ venv_dir }}/bin/gunicorn elearning.wsgi:application \
      --bind {{ gunicorn_bind }} \
      --workers {{ gunicorn_workers }}
  Restart=on-failure

  [Install]
  WantedBy=multi-user.target

---

## Coding Style Rules

- Use the ansible.builtin.* module namespace explicitly on every task.
- Use become: true only where root is required; run app-level tasks as the elearning
  user (become_user: elearning) where possible.
- Every task must have a descriptive name: field.
- Use handlers for all service reloads/restarts — never use state: restarted inline.
- Use notify: on the git task to trigger Gunicorn restart only when code actually changes.
- Do not hard-code any IP, password, secret, or domain in task files — use variables.

---

## Inventory

hosts.yml must use the ubuntu SSH user, SSH key authentication, and 152.228.128.186 IP:

  all:
    hosts:
      elearning_server:
        ansible_host: 152.228.128.186
        ansible_user: ubuntu
        ansible_ssh_private_key_file: ~/.ssh/id_rsa   # adjust path if needed

---

## Smoke-Test Checklist

After producing the Ansible playbook, also produce a smoke-test checklist of commands
to run from a local machine after the playbook completes, to verify each role:

  1. SSH connectivity:         ssh ubuntu@<SERVER_IP> "hostname"
  2. Gunicorn service:         ssh ubuntu@<SERVER_IP> "systemctl is-active elearning-gunicorn"
  3. Nginx service:            ssh ubuntu@<SERVER_IP> "systemctl is-active nginx"
  4. PostgreSQL service:       ssh ubuntu@<SERVER_IP> "systemctl is-active postgresql"
  5. HTTP redirect:            curl -I http://appsec.cc/  → expect 301 to https://
  6. HTTPS home page:          curl -s -o /dev/null -w "%{http_code}" https://appsec.cc/
                               → expect 200 or 302 (login redirect)
  7. Static file served:       curl -I https://appsec.cc/static/css/...  → expect 200
  8. Let's Encrypt cert valid: curl -v https://appsec.cc/ 2>&1 | grep "SSL certificate"
  9. Gunicorn logs:            ssh ubuntu@<SERVER_IP> "journalctl -u elearning-gunicorn -n 50"
  10. Nginx error log:         ssh ubuntu@<SERVER_IP> "tail -n 50 /var/log/nginx/error.log"
```
