# Post-Deployment Smoke-Test Checklist

Run these commands from your **local machine** after `ansible-playbook` completes.
Replace `<SERVER_IP>` with `152.228.128.186`.

---

## 1 — SSH connectivity

```bash
ssh ubuntu@<SERVER_IP> "hostname"
```
Expected: the server's hostname printed without errors.

---

## 2 — Gunicorn service

```bash
ssh ubuntu@<SERVER_IP> "systemctl is-active elearning-gunicorn"
```
Expected: `active`

---

## 3 — Nginx service

```bash
ssh ubuntu@<SERVER_IP> "systemctl is-active nginx"
```
Expected: `active`

---

## 4 — PostgreSQL service

```bash
ssh ubuntu@<SERVER_IP> "systemctl is-active postgresql"
```
Expected: `active`

---

## 5 — HTTP → HTTPS redirect

```bash
curl -I http://appsec.cc/
```
Expected: `HTTP/1.1 301 Moved Permanently` with `Location: https://appsec.cc/`

---

## 6 — HTTPS home page reachable

```bash
curl -s -o /dev/null -w "%{http_code}" https://appsec.cc/
```
Expected: `200` (home page) or `302` (redirected to login — both are correct).

---

## 7 — Static file served by Nginx (not Gunicorn)

```bash
curl -I https://appsec.cc/static/admin/css/base.css
```
Expected: `200 OK` with `Server: nginx` header (not proxied through Gunicorn).

---

## 8 — Let's Encrypt certificate is valid and trusted

```bash
curl -v https://appsec.cc/ 2>&1 | grep -E "(SSL certificate|issuer|expire)"
```
Expected: lines showing a valid certificate issued by Let's Encrypt, not expired.

```bash
# Alternative — show full cert chain info:
echo | openssl s_client -connect appsec.cc:443 -servername appsec.cc 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates
```
Expected: issuer includes `Let's Encrypt`, dates show a certificate valid in the future.

---

## 9 — Gunicorn application logs

```bash
ssh ubuntu@<SERVER_IP> "journalctl -u elearning-gunicorn -n 50 --no-pager"
```
Expected: Gunicorn worker boot messages, no Python tracebacks.

---

## 10 — Nginx error log

```bash
ssh ubuntu@<SERVER_IP> "tail -n 50 /var/log/nginx/error.log"
```
Expected: empty or only informational messages, no `connect() failed` or `upstream` errors.

---

## 11 — Database connectivity (optional deeper check)

```bash
ssh ubuntu@<SERVER_IP> \
  "sudo -u elearning /opt/elearning/venv/bin/python /opt/elearning/manage.py \
   dbshell --settings=elearning.settings.production <<< '\q' && echo 'DB OK'"
```
Expected: `DB OK` — confirms Django can connect to PostgreSQL.

---

## 12 — Certbot renewal dry-run

```bash
ssh ubuntu@<SERVER_IP> "certbot renew --dry-run"
```
Expected: `Congratulations, all simulated renewals succeeded` — confirms auto-renewal is working.

---

## Common failure patterns

| Symptom | Likely cause |
|---|---|
| `502 Bad Gateway` | Gunicorn is not running — check `journalctl -u elearning-gunicorn` |
| `403 Forbidden` on `/static/` | Wrong permissions on `{{ static_root }}` — should be owned by `elearning` |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Certbot used staging CA — re-run with `certbot_staging: false` and delete `/etc/letsencrypt/live/appsec.cc/` |
| Django `500` error | Check `journalctl -u elearning-gunicorn` for Python traceback; likely a missing env var in `.env` |
| `certbot: command not found` | `base` role did not run — re-run `ansible-playbook` |
