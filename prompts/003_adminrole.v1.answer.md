The task is added at the end of ansible/roles/app/tasks/main.yml. Here's what it does:

Runs manage.py shell -c with an inline Python snippet after migrations and collectstatic.
Idempotent: prints ALREADY_ADMIN if the user is already promoted — Ansible reports no change.
Safe before first login: if the user hasn't logged in yet (account not created), it prints USER_NOT_FOUND and exits cleanly — no error, no change reported.
Sets both role = "admin" (gates the app's admin panel via AdminRequiredMixin) and is_staff = True (grants access to /admin/).
changed_when only fires when PROMOTED appears in stdout, so the playbook correctly reports a change only when the promotion actually happens.