# Functional Specification — E-Learning Quiz Platform

**Version:** 4.0  
**Status:** Draft  
**Last updated:** 2026-02-21

### Changelog
| Version | Change |
|---|---|
| 1.0 | Initial specification |
| 2.0 | Added section 9: PDF certificate export |
| 3.0 | No functional changes — HTTPS removed at technical level |
| 4.0 | No functional changes — HTTPS reinstated, domain appsec.cc set (see TECHNICAL_SPEC) |

---

## 1. Purpose and Scope

This document describes what the e-learning platform must do, from the perspective of its users. It is technology-agnostic. All business rules, user interactions, and feature behaviours are defined here.

The platform is a quiz-only learning management system. There is no video, no reading material, and no course structure beyond quizzes. Its primary purpose is to allow an organisation to create and administer multiple-choice assessments, and to allow students to take those assessments at their own pace.

---

## 2. User Roles

The platform has exactly two roles.

### 2.1 Student
A student can browse quizzes, enrol in quizzes, take quizzes, and view their own results. Students cannot see other students' data. Students cannot create, modify, or delete any quiz content.

### 2.2 Admin
An admin can create quizzes and questions, upload images for questions, and consult reporting statistics. Admins cannot modify or delete a quiz once it has been created. Admins cannot take quizzes as students. An admin account is a separate role — a person is either an admin or a student, never both.

---

## 3. Authentication and Access Control

### 3.1 Login
All users must authenticate before accessing any page of the platform. Authentication is delegated entirely to the organisation's Microsoft Entra ID (Azure AD) tenant via OAuth 2.0 / OpenID Connect. The platform does not manage passwords.

On the login page, there is a single "Sign in with Microsoft" button. Clicking it redirects the user to the Microsoft login page. Upon successful authentication, the user is redirected back to the platform.

### 3.2 Role Assignment
A user's role (student or admin) is assigned by an administrator directly in the platform's database (or via Django admin). Role assignment is not automated from Entra ID groups in the MVP. The first time a user logs in via Entra ID, an account is automatically created for them with the default role of **student**. An admin can then elevate the user to admin role if needed.

### 3.3 Access Rules
- Unauthenticated users are redirected to the login page for every route.
- Students cannot access any admin-only page. Attempting to do so results in a "403 Forbidden" page.
- Admins cannot access student quiz-taking pages.

---

## 4. Quiz Management (Admin)

### 4.1 Creating a Quiz
An admin can create a new quiz by providing:

| Field | Description | Constraints |
|---|---|---|
| Title | Short name for the quiz | Required, max 200 characters |
| Description | Optional longer description | Optional, markdown supported |
| Question pool size | Total number of questions stored for this quiz | Must be ≥ 1 |
| Questions shown per attempt | How many questions are randomly selected and shown to a student per attempt | Must be ≤ question pool size, must be ≥ 1 |
| Minimum passing score | The percentage a student must reach to pass | Fixed at 70% in the MVP — displayed but not editable |

### 4.2 Adding Questions to a Quiz
After creating a quiz, an admin can add questions to it one by one. Each question has:

| Field | Description | Constraints |
|---|---|---|
| Question text | The question body | Required, written in Markdown |
| Question type | Single choice or Multiple choice | Required |
| Answer A, B, C, D | The four possible answers | All four are required, plain text |
| Correct answer(s) | Which answer(s) are correct | At least one must be marked correct; for single choice exactly one; for multiple choice at least two |

**Markdown support for question text:** The admin writes question text in a Markdown editor. The text is rendered as formatted HTML when shown to students. Markdown allows headings, bold, italic, code blocks (with syntax highlighting), inline code, and embedded images via the `![alt](url)` syntax.

**Image uploads:** An admin can upload an image via the question editor. After uploading, the platform provides a Markdown snippet (e.g. `![description](/media/questions/filename.png)`) that the admin copies and pastes into the question text field. Images are stored on the server.

### 4.3 Quiz Immutability
Once a quiz has been published (i.e. at least one student has enrolled), the quiz and its questions **cannot be modified or deleted**. This protects the integrity of existing enrolments and attempt records.

> **Implementation note for the MVP:** For simplicity, quizzes are considered "locked" immediately after creation. Admins can add questions to a quiz that has no enrolments yet, but once the first student enrols, the quiz is fully locked. This rule is enforced by the application.

### 4.4 No Quiz Deletion
Admins cannot delete quizzes. This is intentional — historical attempt data must be preserved.

---

## 5. Student Experience

### 5.1 Quiz Catalogue
After logging in, a student lands on the quiz catalogue — a list of all available quizzes. For each quiz, the student can see:
- Quiz title
- Short description
- Number of questions shown per attempt
- Whether they are already enrolled
- Their current enrolment status (not enrolled / enrolled / passed)

### 5.2 Quiz Enrolment
A student can enrol in any quiz by clicking an "Enrol" button on the quiz catalogue or quiz detail page. Enrolment is immediate — no admin approval is required. A student can only be enrolled once per quiz (the enrolment record is unique per student/quiz pair).

### 5.3 Taking a Quiz
From the quiz detail page, an enrolled student can start a new attempt at any time. Starting an attempt:
1. Randomly selects N questions from the quiz's question pool (where N = "questions shown per attempt").
2. Presents all selected questions on a single page, in random order.
3. For each question, displays the question text (rendered Markdown) and the four answer options (A, B, C, D) in random order.
4. For single-choice questions, answers are presented as radio buttons (only one can be selected).
5. For multiple-choice questions, answers are presented as checkboxes. The student is clearly informed that multiple answers may be correct.

The student submits all answers at once using a single "Submit Quiz" button at the bottom of the page. There is no question-by-question navigation — all questions are visible on one scrollable page.

### 5.4 Scoring Logic
After submission, the platform calculates the score as follows:

- Each question is worth one point.
- For a question to earn its point, the student's selection must **exactly match** the set of correct answers — no partial credit.
  - Single choice: the selected answer must be the correct answer.
  - Multiple choice: every correct answer must be checked, and no incorrect answer must be checked. If the student selects 2 out of 3 correct answers, the question scores zero.
- Final score = (number of correct questions / total questions shown) × 100, rounded to one decimal place.
- The attempt is marked as **passed** if the final score ≥ 70%.

### 5.5 Results Page
Immediately after submission, the student sees a results page showing:
- **Pass or Fail** — prominently displayed (e.g. green banner for pass, red for fail).
- **Score** — e.g. "You scored 75.0% (15/20 correct)".
- **Question review** — for every question shown in the attempt:
  - The question text (rendered Markdown).
  - All four answer options, annotated:
    - Correct answers highlighted in green.
    - Answers the student selected highlighted (green if correct, red if incorrect).
    - Answers the student did not select and that are correct are also shown in green (so the student knows what they missed).

### 5.6 Retrying a Quiz
A student can start a new attempt immediately after seeing their results, as many times as they wish. There is no cooldown. Each new attempt randomly re-selects questions from the pool, so a student who retries may encounter different questions.

A student who has already passed can still start new attempts (for practice), but their status in the catalogue remains "passed".

### 5.7 No Attempt History for Students
Students do not see a history of their past attempts. They only see their current status (passed / not passed) per quiz. The platform tracks attempts internally for admin reporting purposes.

---

## 6. Admin Reporting

Admins have access to a reporting section with the following views:

### 6.1 Quiz Summary Report
For each quiz:
- Total number of enrolled students.
- Total number of attempts across all students.
- Overall pass rate: percentage of attempts that resulted in a pass.
- Average score across all attempts (as a percentage).

### 6.2 Per-Student Report (drill-down from Quiz Summary)
For a selected quiz, a table showing each enrolled student with:
- Student name and email.
- Number of attempts made.
- Best score achieved (highest percentage across all their attempts).
- Pass/Fail status (passed = at least one attempt was a pass).
- Date of first attempt and date of most recent attempt.

### 6.3 Student Overview Report
A cross-quiz view showing, for each student:
- Student name and email.
- List of quizzes enrolled in.
- Status per quiz (passed / not passed).
- Total number of attempts made across all quizzes.

---

## 7. User Interface Guidelines

These are functional UI requirements, not visual design decisions.

- Every page must be usable on mobile (responsive layout).
- The quiz-taking page must be clearly structured: question number, question text, then answer options.
- Multiple-choice questions must clearly indicate to the student that more than one answer may be correct (e.g. a label: "Select all that apply").
- The results page must make pass/fail immediately obvious without scrolling.
- Navigation must include: logo/home link, the user's name, and a logout button.
- Admin pages must be clearly separated from student pages — a distinct "Admin" section in the navigation.

---

## 9. PDF Certificate Export

### 9.1 Purpose
A student who has passed a quiz can download a PDF document that serves as formal proof of completion. The document is structured and professional in appearance. It is intended to be shared with a third party (e.g. a manager, an auditor) as evidence that the student passed the assessment.

### 9.2 Who Can Download

**Students** can download their own certificate from the quiz detail page, but only for quizzes they have passed. The download button is not visible for quizzes they have not yet passed. A student cannot download a certificate for another student.

**Admins** can download the certificate for any student who has passed, from the per-student drill-down report (`/admin-panel/reports/quiz/<quiz_id>/students/`). This allows an admin to distribute or archive certificates on behalf of students.

### 9.3 Certificate Content
The PDF contains the following information, clearly laid out:

| Field | Content |
|---|---|
| Platform name | The name of the organisation / platform (configured in settings) |
| Document title | "Certificate of Completion" or "Proof of Assessment Pass" |
| Student full name | As recorded from Entra ID at login time |
| Quiz title | The full title of the quiz |
| Score achieved | The percentage score of the passing attempt (e.g. "82.5%") |
| Date of passing | The date the student first passed the quiz (not the date of download) |
| Unique verification code | A stable alphanumeric code uniquely identifying this student/quiz completion |

> **Score shown on the PDF:** The score displayed is from the **first attempt that resulted in a pass**, not the best score across all attempts. This is consistent with the meaning of a completion certificate — it records when the student first met the standard, not their peak performance.

### 9.4 Unique Verification Code
The verification code is a UUID generated once, the first time the student passes the quiz. It is permanently associated with the student's enrolment record. Every subsequent PDF download for the same student and quiz always produces the same code.

The code appears on the certificate in a clearly labelled field (e.g. "Verification code: 3f4a..."). Its purpose in the MVP is to allow a third party to cross-reference with an admin, who can look up the code in the platform to confirm authenticity. A public verification URL is out of scope for the MVP but the code is designed to support it in a future version.

### 9.5 Certificate Availability
- The certificate is only available (the download button is only visible / the URL only responds) when `enrolment.has_passed = True`.
- Attempting to access the certificate URL for a non-passed enrolment results in a 403 response (or a redirect to the quiz detail page with an explanatory message).
- A student who has passed and then accumulates further attempts does not lose access to their certificate.

### 9.6 PDF Format
- Orientation: **Portrait**, A4.
- Style: Plain, structured, professional — no decorative borders or imagery beyond the platform name as a heading.
- The PDF is generated on demand (not pre-generated and stored). It is streamed directly to the browser as a file download.
- The suggested filename for the downloaded file is: `certificate_{quiz-title-slug}_{student-name-slug}.pdf`

---

## 8. Glossary

| Term | Definition |
|---|---|
| Quiz | A set of questions on a topic, with a defined question pool and presentation count |
| Question pool | The total set of questions stored for a given quiz |
| Attempt | A single instance of a student taking a quiz (selecting N questions, answering, submitting) |
| Enrolment | The relationship between a student and a quiz — created when the student clicks "Enrol" |
| Passing score | The minimum percentage (70%) required to pass a quiz |
| Single choice | A question type where exactly one answer is correct (radio buttons) |
| Multiple choice | A question type where two or more answers are correct (checkboxes) |
| Markdown | A lightweight markup language used for question text formatting |
| Certificate | A PDF document issued to a student as proof they passed a specific quiz |
| Verification code | A stable UUID tied to a student's passing enrolment, printed on the certificate for authenticity checks |
