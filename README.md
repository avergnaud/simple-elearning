# simple-elearning

## tech tips

ansible all -m ping -i inventory --ask-vault-pass

ansible-galaxy collection install -r requirements.yml

ansible-playbook -i inventory site.yml --ask-vault-pass

systemctl restart elearning-gunicorn.service


## Firewall (UFW)

Configured by the `base` Ansible role. Rules are loaded before UFW is enabled to prevent lockouts.

### Incoming

| Port | Protocol | Action | Purpose |
|------|----------|--------|---------|
| 22 | TCP | LIMIT | SSH — rate-limited (max 6 attempts / 30 s per IP) |
| 80 | TCP | ALLOW | HTTP — Nginx redirect to HTTPS + Let's Encrypt renewal |
| 443 | TCP | ALLOW | HTTPS — web application traffic |

### Outgoing

| Port | Protocol | Action | Purpose |
|------|----------|--------|---------|
| 53 | UDP + TCP | ALLOW | DNS — hostname resolution for apt, Let's Encrypt, APIs |
| 80 | TCP | ALLOW | HTTP — apt package list downloads |
| 443 | TCP | ALLOW | HTTPS — apt, Let's Encrypt ACME, external API calls |

All other traffic (in and out) is denied by default. Notable blocked ports: PostgreSQL (5432), Gunicorn (8000).

Both IPv4 and IPv6 are covered — UFW applies each rule to both stacks automatically.

Check status: `sudo ufw status`
