# Architecture

## High-Level Stack

### Backend
- FastAPI
- SQLAlchemy 2
- Alembic
- Supabase Postgres
- Supabase Storage
- Supabase Auth

### Admin Web
- Next.js
- TypeScript

### Tester App
- Expo / React Native
- TypeScript
- React Native Web for early web-based UI development
- SQLite on device later for offline sync

## Monorepo Structure

```text

ml-workflow/
  apps/
    api/
    admin-web/
    mobile/
  docs/
Why Monorepo
•	single product
•	shared documentation
•	simpler development workflow
•	easier API and frontend coordination
•	no need for microservice complexity in v1
Auth Model
•	Supabase Auth handles signup, login, password reset, JWT
•	FastAPI validates Supabase JWT
•	Business user state is stored in app_users
•	Approval and role decisions are managed by FastAPI and app tables
Data Model Ownership
•	Supabase Auth stores auth identities
•	App database stores business entities such as app users, submissions, attachments metadata, and audits
File Storage Model
•	actual file bytes stored in Supabase Storage
•	file metadata stored in submission_attachments
•	attachment rows link files to submissions and uploading users
•	bucket should be private
•	FastAPI should generate signed download URLs after permission checks
Core Flows
Signup / Approval
1.	user signs up via Supabase Auth
2.	app calls bootstrap endpoint
3.	app_users row is created with requested role and pending status
4.	admin approves or rejects user
Submission Flow
1.	tester creates ongoing submission
2.	tester edits while ongoing
3.	tester uploads CSV/XLSX file
4.	tester marks submission completed
5.	admin may reopen if correction is needed
Audit Flow
All create, edit, upload, complete, reopen, approve, and reject actions must be audit logged.
Deployment Approach
V1 Local Dev
•	API in Docker
•	admin web in Docker
•	mobile app can be developed on web first
•	Android emulator later
•	Supabase hosted services for auth, database, and storage
Backend Design Principles
•	thin routers
•	service layer for business rules
•	repository layer for data access
•	all mutation endpoints create audit logs
•	separate admin routes from tester routes
