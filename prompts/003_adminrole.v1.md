The admin role comes from a role field on the User model (apps/accounts/models.py:36-41). Here's how it works:

Every new user starts as student — when someone first logs in via Microsoft Entra ID (OAuth), their account is created automatically with role = "student" (the default).

Role is promoted manually — there is no self-service way to become an admin. An existing administrator must change the role field to "admin" directly, either:

Through the Django built-in admin interface (/admin/) — accessible to users with is_staff = True
Or directly in the database
is_admin is just a property (line 64-66) that returns True when role == "admin". It's what AdminRequiredMixin checks to gate access to the admin panel.

So in short: role assignment is a manual, database-level operation — by design, it's not automated from Entra ID groups in this MVP.

I want the following user to be admin:
a.vergnaud@catamania.com

Please modify the ansible playbook accordingly.