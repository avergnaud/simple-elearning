The Django project itself hasn't been created yet — the repository only has specs, Ansible, and requirements.txt. There is no manage.py, no elearning/ settings package, no apps — nothing.

You need to scaffold the Django project locally and commit it before the playbook can continue. The rough steps:

# In your local project root
pip install django==5.1.*

# Scaffold the project (creates manage.py and elearning/ package)
django-admin startproject elearning .

# Create the settings split (base/development/production)
mkdir elearning/settings
# ... then build out settings/base.py, development.py, production.py

# Create the apps
python manage.py startapp accounts
python manage.py startapp quizzes
python manage.py startapp enrolments
python manage.py startapp reporting
mkdir apps
mv accounts apps/ && mv quizzes apps/ && mv enrolments apps/ && mv reporting apps/

Please scaffold the full Django project structure now. I can create all the files according to the specs (FUNCTIONAL_SPEC.md + TECHNICAL_SPEC.md) — manage.py, settings, models, views, URLs, templates, etc.