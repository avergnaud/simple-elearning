# CLAUDE.md — Instructions for Claude Code

This file defines how Claude Code must work on this project. Read it entirely before taking any action. These rules are not suggestions — follow them consistently throughout the project.

---

## 1. Project Context

This is a Django e-learning platform (quiz-only). The full feature specification is in `FUNCTIONAL_SPEC.md`. The technical architecture is in `TECHNICAL_SPEC.md`. When in doubt about what to build, refer to those files. Do not invent features or requirements that are not specified there.

This is an MVP. When there is a trade-off between simplicity and sophistication, always choose simplicity.

---

## 2. Before You Write Any Code

1. **Read the relevant spec sections** before implementing any feature.
2. **State your plan** briefly before starting — one sentence per step. Wait for confirmation if the change is large or destructive.
3. **Check for existing code** before creating new files. Never duplicate logic.
4. If you are unsure about a requirement, say so explicitly and ask — do not guess and proceed.

---

## 3. Django Conventions

### 3.1 General
- Use **Django 5.x** features. Do not use deprecated APIs.
- All Django apps live in the `apps/` directory. Register them as `apps.quizzes`, `apps.accounts`, etc.
- Use **class-based views (CBVs)** for all views. Do not use function-based views unless a CBV would be genuinely more complex for that specific case (explain why if so).
- All views that require login must use the `LoginRequiredMixin`.
- All admin-only views must use a custom `AdminRequiredMixin` (to be created in `apps/accounts/mixins.py`) that checks `request.user.role == 'admin'`. Never rely solely on Django's `is_staff` flag for this.

### 3.2 Models
- Use `UUIDField` as the primary key for all models: `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.
- Always define `__str__` methods.
- Always define `class Meta` with at least `verbose_name` and `verbose_name_plural`.
- Add `ordering` to Meta where natural (e.g. quizzes by title, attempts by started_at descending).
- Use `on_delete=models.PROTECT` for foreign keys where deletion should be blocked (most cases here). Use `CASCADE` only when child records are meaningless without the parent.
- Never use `null=True` on string fields (`CharField`, `TextField`) — use `blank=True` and an empty string default instead.

### 3.3 Forms
- Use Django `ModelForm` wherever possible.
- Add field-level validation in the form's `clean_<field>` methods.
- Add cross-field validation in the form's `clean()` method.
- Always use `{% csrf_token %}` in every HTML form.

### 3.4 URLs
- Each app has its own `urls.py`. Include them in the root `urls.py` with a namespace.
- Use `path()` not `re_path()` unless a regex is genuinely required.
- Name every URL pattern. Use the pattern `app_name:view_name` (e.g. `quizzes:detail`, `enrolments:attempt`).
- Always use `reverse()` or `{% url %}` — never hardcode URLs.

### 3.5 Templates
- All templates extend `templates/base.html`.
- Use template inheritance: `{% extends %}`, `{% block %}`, `{% include %}`.
- Keep logic out of templates. If a template requires computed data, compute it in the view and pass it via context.
- Do not use template tags for business logic. Template tags are for presentation only.
- Use `{{ variable|default:"" }}` to handle empty values gracefully.

### 3.6 Settings
- Never put secrets in settings files. All secrets come from environment variables via `python-decouple`:  
  `from decouple import config`  
  `SECRET_KEY = config('DJANGO_SECRET_KEY')`
- Settings are split into `base.py`, `development.py`, `production.py`. Common logic goes in `base.py`.
- `DEBUG` is always `False` in production settings, and must be loaded from an env var.

### 3.7 Database
- Always create migrations after changing models: `python manage.py makemigrations`.
- Never edit existing migration files — create new ones.
- Never use `python manage.py migrate --fake` unless explicitly instructed.
- Use `select_related()` and `prefetch_related()` proactively on querysets that will access related objects, to avoid N+1 query problems.

---

## 4. Code Style

- Follow **PEP 8** strictly.
- Maximum line length: **119 characters**.
- Use **double quotes** for strings.
- Write **docstrings** for every view class and every non-trivial method. Use the Google docstring format.
- Use **type hints** for function signatures where practical.
- Group imports in this order, with a blank line between groups:
  1. Python standard library
  2. Django imports
  3. Third-party libraries
  4. Internal app imports

Example:
```python
import uuid
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from authlib.integrations.django_client import OAuth

from apps.accounts.models import User
```

---

## 5. Security Rules

- **Never** disable CSRF protection on any view.
- **Never** use `mark_safe()` on user-provided content. Only use it on server-rendered Markdown output after it has been sanitised by the Markdown renderer.
- **Never** expose internal IDs in ways that allow enumeration. UUIDs in URLs are acceptable; sequential integers are not.
- **Never** put `.env` or any file containing secrets under version control.
- All file uploads must be validated: check extension and use `Pillow` to verify the file is a real image before saving.
- Restrict uploaded filename characters — generate a new UUID filename server-side, ignoring the original filename.

---

## 6. Frontend Rules

- Use **Bootstrap 5** classes exclusively for all styling. No custom CSS unless absolutely unavoidable.
- If a minor CSS override is genuinely necessary, put it in a `<style>` block inside the relevant template's `{% block extra_css %}`, not in a separate `.css` file.
- Do not use any JavaScript framework or library (no jQuery, no Alpine.js, no HTMX). The only JavaScript loaded is Bootstrap's own bundle (included in `base.html`).
- If a page needs minor JavaScript behaviour (e.g. confirming a destructive action), write vanilla JS in a `{% block extra_js %}` block at the bottom of that specific template.
- The quiz-taking page uses a standard HTML form with `<input type="radio">` and `<input type="checkbox">`. No dynamic question loading.
- All Bootstrap containers use `container` (not `container-fluid`) for a readable line width on large screens.
- The certificate PDF template (`templates/certificates/certificate.html`) is **standalone** — it must not extend `base.html`, must not load Bootstrap, and must use only inline CSS. WeasyPrint does not support all CSS features; keep styles minimal and print-safe (avoid flexbox, avoid external font loading unless explicitly tested).

---

## 7. Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| App names | Lowercase, plural noun | `quizzes`, `accounts`, `enrolments` |
| Model names | PascalCase, singular | `Quiz`, `AttemptQuestion` |
| View names | PascalCase, suffixed with verb + View | `QuizDetailView`, `AttemptSubmitView` |
| URL names | lowercase with hyphens | `quiz-detail`, `attempt-submit` |
| Template files | lowercase with hyphens | `quiz-detail.html`, `attempt-form.html` |
| Template directories | match app name | `templates/quizzes/quiz-detail.html` |
| Form names | PascalCase, suffixed with Form | `QuizCreateForm`, `QuestionAddForm` |
| Context variable names | lowercase snake_case | `quiz_list`, `current_attempt` |

---

## 8. What to Do When Stuck

- If a library's API is unclear, check its official documentation before guessing.
- If a Django behaviour is uncertain, prefer the explicit approach over the implicit one.
- If you cannot achieve something without violating one of the rules above, stop and explain the problem rather than silently breaking the rule.
- Do not silently ignore an error. If a migration fails, a view throws a 500, or a test fails — report it and reason through it.

---

## 9. Testing

> Testing is out of scope for the MVP but noted here for future reference.

When tests are added, they will use Django's built-in `TestCase`. Tests will live in `tests/` inside each app. Each view, form, and model method with business logic will have a corresponding test. Do not write tests unless explicitly asked — but do not write code that is untestable (e.g. logic inside templates).

---

## 10. Deployment and Ops Rules

- The target deployment environment is **Ubuntu 25.04** on OVH, managed by **Ansible**. Do not suggest Docker, Kubernetes, or cloud services.
- The WSGI server is **Gunicorn** with 3 workers. Do not suggest uWSGI or Daphne.
- Static files are served by **Nginx** after `collectstatic`. Do not configure Django to serve static files in production.
- Media files (uploaded images) are stored in `MEDIA_ROOT` on disk and served by **Nginx** from `/media/`.
- All Ansible tasks must be **idempotent** — running the playbook twice must not cause errors or duplicate state.
- The domain is `appsec.cc`. Use this in Nginx `server_name`, `ALLOWED_HOSTS`, and the Entra ID redirect URI.
- HTTPS is **mandatory**. The Nginx config must include both an HTTP→HTTPS redirect block (port 80) and the main HTTPS server block (port 443). Never configure Django to serve over plain HTTP in production.
- The Let's Encrypt certificate lives at `/etc/letsencrypt/live/appsec.cc/`. Do not move, copy, or symlink certificate files manually — let Certbot manage them entirely.

---

## 11. Git Hygiene (if managing commits)

- Commit messages follow the format: `type: short description`  
  Types: `feat`, `fix`, `refactor`, `style`, `docs`, `chore`  
  Example: `feat: add quiz enrolment view`
- Never commit migration files alongside model changes and view changes in the same commit. Migrations get their own commit.
- Never commit `.env`, `*.pyc`, `__pycache__/`, or `media/` directories.

---

## 12. Quick Reference — Key Files

| File | Purpose |
|---|---|
| `FUNCTIONAL_SPEC.md` | What to build — features, business rules, user stories |
| `TECHNICAL_SPEC.md` | How to build it — stack, schema, URLs, auth flow |
| `CLAUDE.md` | This file — how Claude Code must work |
| `apps/accounts/models.py` | Custom User model |
| `apps/accounts/views.py` | OAuth login/callback/logout views |
| `apps/quizzes/models.py` | Quiz, Question, Answer models |
| `apps/enrolments/models.py` | Enrolment, Attempt, AttemptQuestion, AttemptAnswer models |
| `apps/enrolments/views.py` | Enrolment, Attempt, certificate download views (student) |
| `apps/reporting/views.py` | Admin reporting views + admin certificate download view |
| `templates/certificates/certificate.html` | Standalone PDF template (no Bootstrap, inline CSS only) |
| `elearning/settings/base.py` | Shared Django settings — domain is `appsec.cc` |
| `elearning/urls.py` | Root URL configuration |
| `templates/base.html` | Master HTML layout |
