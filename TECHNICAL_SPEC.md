# Technical Specification — E-Learning Quiz Platform

**Version:** 4.0  
**Status:** Draft  
**Last updated:** 2026-02-21

### Changelog
| Version | Change |
|---|---|
| 1.0 | Initial specification |
| 2.0 | Added WeasyPrint dependency, certificate_code field on Enrolment, PDF generation view, updated URL map and deployment notes |
| 3.0 | Removed HTTPS / Let's Encrypt — MVP runs over plain HTTP. TLS deferred |
| 4.0 | Reinstated HTTPS. Domain set to appsec.cc. TLS via Let's Encrypt + Certbot (automated, Ansible-managed) |

---

## 1. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Language | Python 3.12 | Stable LTS, widely supported |
| Web framework | Django 5.x | Batteries-included: ORM, templating, admin, auth |
| Database | PostgreSQL 16 | Relational, ACID-compliant, ideal for structured quiz data |
| Frontend styling | Bootstrap 5 | Responsive, mobile-first, no custom CSS required |
| Markdown rendering | `django-markdownify` + `Pygments` | Server-side Markdown to HTML, code syntax highlighting |
| PDF generation | `WeasyPrint` | Renders an HTML/CSS Django template to PDF; no separate layout API needed |
| Authentication | `authlib` + `requests` (MSAL flow) | OAuth 2.0 / OpenID Connect against Microsoft Entra ID |
| App server | Gunicorn | Production WSGI server for Django |
| Web server / reverse proxy | Nginx | Serves static files and media, proxies to Gunicorn |
| Infrastructure provisioning | Ansible | Idempotent setup of the Ubuntu server |
| Operating system | Ubuntu 25.04 (OVH IaaS) | Target deployment environment |

### 1.1 Notable exclusions (kept out of scope for MVP)
- No JavaScript framework (React, Vue, etc.) — server-rendered templates only.
- No Celery / Redis — no background tasks required.
- No Docker — direct deployment on the host OS via Ansible.
- No cloud object storage (S3, Azure Blob) — media files stored on disk, served by Nginx.
- No email notifications.

---

## 2. Application Architecture

```
[Browser]
    │  HTTPS (port 443, Let's Encrypt certificate)
    ▼
[Nginx]
    ├── /static/*  → served directly from disk (Django collectstatic output)
    ├── /media/*   → served directly from disk (uploaded images)
    └── /*         → proxy_pass → [Gunicorn : 8000]
                                        │
                                        ▼
                                 [Django Application]
                                        │
                                        ▼
                                  [PostgreSQL]
```

Django handles all routing, business logic, and HTML rendering. There are no API endpoints — all responses are full HTML pages (server-side rendering via Django templates).

---

## 3. Authentication Flow (Microsoft Entra ID / OAuth 2.0)

The platform uses the **Authorization Code Flow** with OpenID Connect.

```
1. User visits any protected page → redirected to /accounts/login/
2. User clicks "Sign in with Microsoft"
3. Browser redirected to:
   https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize
   with: response_type=code, client_id, redirect_uri, scope=openid profile email
4. User authenticates in Microsoft
5. Microsoft redirects to: /accounts/callback/?code=...&state=...
6. Django backend exchanges the code for tokens (POST to Microsoft token endpoint)
7. Django decodes the id_token (JWT), extracts: oid, email, display name
8. Django upserts a local User record (matched on Entra OID):
   - If new user → create with role=student
   - If existing user → update name/email if changed
9. Django creates a session → user is now logged in
10. Redirect to the originally requested page (or home)
```

### 3.1 Entra ID App Registration (to be configured by the admin)
- Platform: Web
- Redirect URI: `https://appsec.cc/accounts/callback/`
- Supported account types: Single tenant (your organisation only)
- Scopes requested: `openid profile email`
- Certificates & Secrets: one client secret, stored in Django settings via environment variable

### 3.2 Session Management
Django's built-in session framework is used. Sessions are stored in the database (default Django behaviour). Session cookie is `HttpOnly` and `Secure` (HTTPS only). Both flags are set in production settings:
  `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`.

---

## 4. Django Project Structure

```
elearning/                        ← Django project root
├── manage.py
├── elearning/                    ← Project settings package
│   ├── settings/
│   │   ├── base.py               ← Common settings
│   │   ├── development.py        ← Dev overrides (DEBUG=True, SQLite optional)
│   │   └── production.py         ← Production overrides (read from env vars)
│   ├── urls.py                   ← Root URL configuration
│   └── wsgi.py
├── apps/
│   ├── accounts/                 ← Authentication, user model, OAuth callback
│   ├── quizzes/                  ← Quiz, Question, Answer models and views
│   ├── enrolments/               ← Enrolment and Attempt models and views
│   └── reporting/                ← Admin reporting views
├── templates/                    ← All HTML templates
│   ├── base.html                 ← Master layout (Bootstrap navbar, footer)
│   ├── accounts/
│   ├── quizzes/
│   ├── enrolments/
│   └── reporting/
├── static/                       ← Static assets (Bootstrap CSS/JS via CDN or local)
├── media/                        ← Uploaded images (gitignored)
└── requirements.txt
```

---

## 5. Data Model

### 5.1 Entity-Relationship Overview

```
User ──< Enrolment >── Quiz ──< Question ──< Answer
              │
              └──< Attempt ──< AttemptQuestion ──< AttemptAnswer
```

### 5.2 Table Definitions

#### `User` (extends AbstractBaseUser or uses AbstractUser)
| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Auto-generated |
| `entra_oid` | CharField(36), unique | The `oid` claim from Entra ID JWT — used to match returning users |
| `email` | EmailField, unique | From Entra ID `email` or `preferred_username` claim |
| `display_name` | CharField(200) | From Entra ID `name` claim |
| `role` | CharField(10) | `'student'` or `'admin'` — default `'student'` |
| `is_active` | BooleanField | Default True |
| `date_joined` | DateTimeField | Auto |
| `last_login` | DateTimeField | Auto |

#### `Quiz`
| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `title` | CharField(200) | |
| `description` | TextField, blank | Markdown |
| `questions_shown` | PositiveIntegerField | How many questions per attempt |
| `passing_score` | DecimalField | Fixed at 70.0 in MVP |
| `created_by` | FK → User | The admin who created it |
| `created_at` | DateTimeField | Auto |
| `is_locked` | BooleanField | True once first enrolment exists; prevents adding more questions |

#### `Question`
| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `quiz` | FK → Quiz | |
| `text` | TextField | Markdown |
| `question_type` | CharField(10) | `'single'` or `'multiple'` |
| `order` | PositiveIntegerField | Display order in admin; randomised for students |
| `created_at` | DateTimeField | Auto |

#### `Answer`
| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `question` | FK → Question | |
| `text` | CharField(500) | Plain text |
| `is_correct` | BooleanField | |
| `order` | PositiveIntegerField | Randomised per attempt |

#### `Enrolment`
| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `student` | FK → User | |
| `quiz` | FK → Quiz | |
| `enrolled_at` | DateTimeField | Auto |
| `has_passed` | BooleanField | Set to True when any attempt passes; never reverted |
| `passing_attempt` | FK → Attempt, null/blank | Set to the first attempt that resulted in a pass; never updated after that |
| `certificate_code` | UUIDField, unique, null | Generated once when `has_passed` is first set to True; stable forever |
| unique_together | `(student, quiz)` | One enrolment per student per quiz |

#### `Attempt`
| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `enrolment` | FK → Enrolment | |
| `started_at` | DateTimeField | Auto on creation |
| `submitted_at` | DateTimeField | Null until submitted |
| `score_percent` | DecimalField(5,2) | Calculated on submission; null until submitted |
| `passed` | BooleanField | Null until submitted |

#### `AttemptQuestion`
Stores which questions were selected for this attempt, preserving the exact set shown to the student.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `attempt` | FK → Attempt | |
| `question` | FK → Question | |
| `display_order` | PositiveIntegerField | The randomised order shown to this student |

#### `AttemptAnswer`
Stores which answers the student selected for each question in this attempt.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `attempt_question` | FK → AttemptQuestion | |
| `answer` | FK → Answer | |
| `is_selected` | BooleanField | True if the student checked this answer |

> **Why store all answers, not just selected ones?**  
> Storing all answers with `is_selected=True/False` allows the results page to display all options with correct/incorrect annotations without additional queries. It also allows answer order to be preserved per attempt.

---

## 6. URL Structure

### Student-facing URLs
```
/                                → Redirect to /quizzes/ or /login/
/accounts/login/                 → Login page (Sign in with Microsoft button)
/accounts/callback/              → OAuth callback handler
/accounts/logout/                → Logout
/quizzes/                        → Quiz catalogue (student home)
/quizzes/<quiz_id>/              → Quiz detail page (description, enrol button or start button)
/quizzes/<quiz_id>/enrol/        → POST: enrol in quiz, redirect to quiz detail
/quizzes/<quiz_id>/attempt/      → GET: display quiz form | POST: submit answers
/quizzes/<quiz_id>/results/<attempt_id>/           → Results page (pass/fail, score, review)
/quizzes/<quiz_id>/certificate/                    → PDF download (student, own passed enrolment only)
```

### Admin URLs
```
/admin-panel/                    → Admin home / dashboard
/admin-panel/quizzes/            → List all quizzes
/admin-panel/quizzes/create/     → Create new quiz
/admin-panel/quizzes/<quiz_id>/  → Quiz detail (view questions, add questions)
/admin-panel/quizzes/<quiz_id>/questions/add/    → Add question form
/admin-panel/media/upload/       → Image upload endpoint (returns markdown snippet)
/admin-panel/reports/            → Reporting home
/admin-panel/reports/quiz/<quiz_id>/             → Quiz summary report
/admin-panel/reports/quiz/<quiz_id>/students/    → Per-student drill-down
/admin-panel/reports/students/   → Student overview report
/admin-panel/reports/certificate/<enrolment_id>/ → PDF download (admin, any passed enrolment)
```

> **Note:** Django's built-in `/admin/` (the Django admin site) is enabled for superuser database management but is **not** the primary admin interface for end-users. The `/admin-panel/` routes above are the purpose-built interface.

---

## 7. Business Logic: Attempt Lifecycle

```python
# Pseudo-code — not actual code

def start_attempt(student, quiz):
    enrolment = get_enrolment(student, quiz)  # must exist
    questions = random.sample(quiz.questions.all(), quiz.questions_shown)
    attempt = Attempt.create(enrolment=enrolment)
    for i, question in enumerate(questions):
        aq = AttemptQuestion.create(attempt=attempt, question=question, display_order=i)
        answers = list(question.answers.all())
        random.shuffle(answers)
        for answer in answers:
            AttemptAnswer.create(attempt_question=aq, answer=answer, is_selected=False)
    return attempt

def submit_attempt(attempt, submitted_answers):
    # submitted_answers: dict of {attempt_question_id: [answer_id, ...]}
    correct_count = 0
    for aq in attempt.attempt_questions.all():
        selected_ids = set(submitted_answers.get(str(aq.id), []))
        correct_ids = set(aq.question.answers.filter(is_correct=True).values_list('id', flat=True))
        for aa in aq.attempt_answers.all():
            aa.is_selected = str(aa.answer_id) in selected_ids
            aa.save()
        if selected_ids == correct_ids:
            correct_count += 1
    total = attempt.attempt_questions.count()
    attempt.score_percent = round((correct_count / total) * 100, 1)
    attempt.passed = attempt.score_percent >= attempt.enrolment.quiz.passing_score
    attempt.submitted_at = now()
    attempt.save()
    if attempt.passed:
        enrolment = attempt.enrolment
        if not enrolment.has_passed:
            # First time passing: record the passing attempt and generate the certificate code
            enrolment.has_passed = True
            enrolment.passing_attempt = attempt
            enrolment.certificate_code = uuid.uuid4()
            enrolment.save()
    return attempt
```

---

## 8. Image Upload Handling

- Uploaded via a simple file input on the question creation form.
- Stored at: `MEDIA_ROOT/questions/{uuid}.{ext}` where the UUID is generated server-side.
- Served by Nginx from: `MEDIA_URL = /media/`
- After upload, the view returns a response containing the Markdown snippet:  
  `![image description](/media/questions/abc123.png)`  
  The admin copies this snippet and pastes it into the question text field.
- Allowed file types: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`
- Maximum file size: 5 MB
- Images are never deleted (tied to question history integrity).

---

## 9. PDF Certificate Generation

### 9.1 Library
**WeasyPrint** is used to generate PDFs. It converts a rendered Django HTML template into a PDF binary. This approach is consistent with the rest of the application — no separate layout API or templating language to learn.

WeasyPrint requires system-level dependencies (Pango, Cairo, GDK-PixBuf) that must be installed on the server by Ansible.

### 9.2 Template
A dedicated, print-oriented HTML template is created at:
```
templates/certificates/certificate.html
```
This template does **not** extend `base.html`. It is a standalone HTML document with inline CSS, designed for print output (A4 portrait). It does not load Bootstrap — it uses minimal inline styles only, since WeasyPrint does not support all CSS features and has no need for a responsive grid.

### 9.3 View Logic

Two views handle PDF generation:

**`CertificateDownloadView`** (student-facing, in `apps/enrolments/views.py`):
```python
# Pseudo-code
def get(self, request, quiz_id):
    enrolment = get_object_or_404(Enrolment, student=request.user, quiz_id=quiz_id)
    if not enrolment.has_passed:
        raise PermissionDenied
    return render_certificate_pdf(enrolment)
```

**`AdminCertificateDownloadView`** (admin-facing, in `apps/reporting/views.py`):
```python
# Pseudo-code
def get(self, request, enrolment_id):
    enrolment = get_object_or_404(Enrolment, id=enrolment_id)
    if not enrolment.has_passed:
        raise PermissionDenied
    return render_certificate_pdf(enrolment)
```

Both views share a common `render_certificate_pdf(enrolment)` helper function that:
1. Fetches the required data (student name, quiz title, score from passing attempt, date, certificate code).
2. Renders `certificates/certificate.html` to an HTML string using Django's `render_to_string`.
3. Passes the HTML string to `weasyprint.HTML(string=html).write_pdf()`.
4. Returns an `HttpResponse` with `Content-Type: application/pdf` and `Content-Disposition: attachment; filename="..."`.

### 9.4 Filename Convention
```
certificate_{quiz-title-slug}_{student-display-name-slug}.pdf
```
Both slugs are generated using Django's `slugify()` utility. Example:
```
certificate_application-security-fundamentals_jane-doe.pdf
```

### 9.5 Data Available to the Certificate Template

| Template variable | Source |
|---|---|
| `student_name` | `enrolment.student.display_name` |
| `quiz_title` | `enrolment.quiz.title` |
| `score_percent` | `enrolment.passing_attempt.score_percent` |
| `passed_date` | `enrolment.passing_attempt.submitted_at` (date only) |
| `certificate_code` | `enrolment.certificate_code` (UUID, formatted as uppercase with hyphens) |
| `platform_name` | `settings.PLATFORM_NAME` (new setting, e.g. `"Acme Corp Learning"`) |
| `generated_at` | Current datetime (for the "document generated on" footer line) |

### 9.6 New Django Setting
```python
# In base.py
PLATFORM_NAME = config("PLATFORM_NAME", default="E-Learning Platform")
```
And in `.env`:
```
PLATFORM_NAME=Acme Corp Learning
```

### 9.7 Server Dependencies (Ansible)
WeasyPrint requires the following system packages, to be added to the Ansible `base` role:
```
libpango-1.0-0
libpangoft2-1.0-0
libgdk-pixbuf2.0-0
libffi-dev
shared-mime-info
```
These are standard Ubuntu packages installable via `apt`.

---

## 10. Security Considerations

| Concern | Mitigation |
|---|---|
| CSRF | Django's built-in CSRF middleware — enabled on all POST forms |
| XSS | Django template auto-escaping; Markdown rendered server-side with a safe allow-list (no raw HTML in Markdown) |
| Clickjacking | Django's `XFrameOptionsMiddleware` — `DENY` |
| Unauthorised access | `@login_required` decorator on all views; role check decorators for admin views |
| Session hijacking | `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True` |
| OAuth state validation | CSRF token used as the `state` parameter in the OAuth flow |
| SQL injection | Django ORM parameterises all queries — no raw SQL |
| Sensitive config | All secrets (client secret, DB password, Django SECRET_KEY) loaded from environment variables — never hardcoded |

---

## 11. Deployment Architecture (Ansible-managed)

### 10.1 Server Setup (Ansible roles)
The Ansible playbook will provision the following roles in order:

1. **`base`** — OS updates, install Python 3.12, PostgreSQL 16, Nginx, Git
2. **`postgres`** — Create DB user, create database, set pg_hba.conf
3. **`app`** — Clone/update repo, create virtualenv, install requirements, run migrations, collectstatic
4. **`gunicorn`** — Install systemd service unit for Gunicorn
5. **`nginx`** — Deploy Nginx site config (HTTP redirect + HTTPS server blocks), enable site, reload Nginx
6. **`ssl`** — Obtain Let's Encrypt certificate for `appsec.cc` via Certbot; configure auto-renewal

### 10.2 Nginx Configuration (key directives)
```nginx
# Redirect all HTTP traffic to HTTPS
server {
    listen 80;
    server_name appsec.cc www.appsec.cc;
    return 301 https://appsec.cc$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl;
    server_name appsec.cc www.appsec.cc;

    ssl_certificate     /etc/letsencrypt/live/appsec.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/appsec.cc/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    location /static/ { alias /var/www/elearning/static/; }
    location /media/  { alias /var/www/elearning/media/;  }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 10.3 Gunicorn systemd Unit
```ini
[Unit]
Description=Gunicorn for E-Learning Platform
After=network.target postgresql.service

[Service]
User=elearning
WorkingDirectory=/opt/elearning
EnvironmentFile=/opt/elearning/.env
ExecStart=/opt/elearning/venv/bin/gunicorn elearning.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 10.4 Environment Variables (`.env` file, not committed to git)
```
DJANGO_SECRET_KEY=...
DJANGO_SETTINGS_MODULE=elearning.settings.production
DATABASE_URL=postgres://elearning_user:password@localhost/elearning_db
ENTRA_CLIENT_ID=...
ENTRA_CLIENT_SECRET=...
ENTRA_TENANT_ID=...
ALLOWED_HOSTS=appsec.cc,www.appsec.cc
```

---

## 12. Dependencies (`requirements.txt`)

```
Django==5.1.*
psycopg2-binary==2.9.*       # PostgreSQL adapter
authlib==1.3.*               # OAuth 2.0 / OpenID Connect
requests==2.32.*             # HTTP client used by authlib
django-markdownify==0.9.*    # Markdown → HTML in templates
Pygments==2.18.*             # Syntax highlighting in code blocks
Pillow==10.*                 # Image validation on upload
weasyprint==62.*             # HTML → PDF rendering for certificates
gunicorn==22.*               # Production WSGI server
python-decouple==3.8.*       # Environment variable loading
whitenoise==6.7.*            # Static file serving (fallback/dev)
```

---

## 13. Bootstrap Integration

Bootstrap 5 is loaded via CDN in the base template:
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
```

No custom CSS file is created at MVP stage. All styling uses Bootstrap utility classes only. The only allowed style customisation is a `<style>` block in `base.html` for minor adjustments (e.g. correct/incorrect answer colour overrides on the results page).

---

## 14. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Concurrent users | Up to 50 simultaneous users (small organisation) |
| Response time | < 500ms for all pages under normal load |
| Browser support | Last 2 versions of Chrome, Firefox, Safari, Edge |
| Mobile support | Fully functional on screens ≥ 320px wide |
| HTTPS | Mandatory — enforced by Nginx. Certificate issued by Let's Encrypt for `appsec.cc`, managed by Certbot |
| Data backup | PostgreSQL daily dump via cron (out of scope for MVP Ansible, noted for future) |
