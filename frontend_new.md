# splanly — Frontend Design Document

## App Name
**splanly** by SkilledCA Enterprises

## Tech Stack
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Deployed on Vercel

---

## Authentication

### Login
**POST /api/v1/auth/login**
```json
Request: { "email": "string", "password": "string" }
Response: { "access_token": "string", "refresh_token": "string", "token_type": "bearer" }
```

### Refresh Token
**POST /api/v1/auth/refresh**
```json
Request: { "refresh_token": "string" }
Response: { "access_token": "string", "refresh_token": "string", "token_type": "bearer" }
```

### Get Current User
**GET /api/v1/auth/me** (Bearer token required)
```json
Response: {
  "user": { "id": 423, "email": "admin@pkf.in", "display_name": "Admin", "is_active": true },
  "firms": [
    { "firm": { "id": 1, "name": "PKF Sridhar & Santhanam", "code": "PKF" }, "role": "admin" }
  ],
  "active_firm_id": 1
}
```

### Switch Firm
**POST /api/v1/auth/firm/switch**
```json
Request: { "firm_id": 1 }
Response: { "access_token": "string", "refresh_token": "string", "token_type": "bearer" }
```

---

## Dashboard

### Get Dashboard Stats
**GET /api/v1/dashboard** (Bearer token + firm_id required)
```json
Response: {
  "total_members": 54,
  "total_clients": 12,
  "active_engagements": 8,
  "current_assignments": 23,
  "bench_count": 15,
  "pending_leaves": 3,
  "upcoming_leaves": 5
}
```

---

## Team Members

### List Team Members
**GET /api/v1/team-members?limit=50&offset=0&q=search&is_active=true&business_role=staff&branch_id=1**
```json
Response: {
  "items": [
    {
      "id": 1,
      "name": "Rajesh Kumar",
      "email": "rajesh.kumar@pkfindia.com",
      "employee_code": "EMP001",
      "business_role": "partner",
      "is_active": true,
      "branch_id": 1,
      "seniority_level": "Senior"
    }
  ],
  "total": 54,
  "limit": 50,
  "offset": 0
}
```

### Get Team Member
**GET /api/v1/team-members/{id}**
```json
Response: {
  "id": 1,
  "name": "Rajesh Kumar",
  "email": "rajesh.kumar@pkfindia.com",
  "employee_code": "EMP001",
  "business_role": "partner",
  "is_oversight_only": false,
  "seniority_level": "Senior",
  "date_of_joining": "2020-01-15",
  "date_of_relieving": null,
  "is_active": true,
  "branch_id": 1
}
```

### Create Team Member
**POST /api/v1/team-members**
```json
Request: {
  "name": "New Member",
  "email": "new@pkfindia.com",
  "employee_code": "EMP055",
  "business_role": "staff",
  "seniority_level": "Junior",
  "date_of_joining": "2026-01-01",
  "branch_id": 1
}
Response: { "id": 55, "name": "New Member", "email": "new@pkfindia.com" }
```

### Update Team Member
**PATCH /api/v1/team-members/{id}**
```json
Request: { "name": "Updated Name", "seniority_level": "Senior" }
Response: { "id": 1, "name": "Updated Name", "email": "..." }
```

### Delete Team Member (soft)
**DELETE /api/v1/team-members/{id}**
```json
Response: { "detail": "Team member deactivated" }
```

### Business Roles
`partner`, `director`, `ca_manager`, `paid_assistant`, `staff`, `article`, `data_analyst`

---

## Clients

### List Clients
**GET /api/v1/clients?limit=50&offset=0&q=search&is_active=true**
```json
Response: {
  "items": [
    { "id": 1, "name": "Acme Corp", "code": "ACM01", "industry": "Manufacturing", "is_active": true }
  ],
  "total": 12, "limit": 50, "offset": 0
}
```

### Get Client
**GET /api/v1/clients/{id}**
```json
Response: { "id": 1, "name": "Acme Corp", "code": "ACM01", "industry": "Manufacturing", "is_active": true }
```

### Create Client
**POST /api/v1/clients**
```json
Request: { "name": "New Client", "code": "NC01", "industry": "IT" }
Response: { "id": 13, "name": "New Client", "code": "NC01" }
```

### Update Client
**PATCH /api/v1/clients/{id}**
```json
Request: { "name": "Updated Name" }
Response: { "id": 1, "name": "Updated Name", "code": "ACM01" }
```

### Delete Client (soft)
**DELETE /api/v1/clients/{id}**
```json
Response: { "detail": "Client deactivated" }
```

---

## Engagements

### List Engagements
**GET /api/v1/engagements?limit=50&offset=0&q=search&is_active=true&status=active**
```json
Response: {
  "items": [
    {
      "id": 1,
      "name": "Annual Audit FY26",
      "client_id": 1,
      "client_name": "Acme Corp",
      "engagement_type": "statutory_audit",
      "status": "active",
      "start_date": "2026-04-01",
      "end_date": "2026-09-30",
      "is_active": true
    }
  ],
  "total": 8, "limit": 50, "offset": 0
}
```

### Get Engagement
**GET /api/v1/engagements/{id}**
```json
Response: {
  "id": 1,
  "name": "Annual Audit FY26",
  "client_id": 1,
  "client_name": "Acme Corp",
  "engagement_type": "statutory_audit",
  "recurrence_pattern": "annual",
  "status": "active",
  "start_date": "2026-04-01",
  "end_date": "2026-09-30",
  "is_active": true
}
```

### Create Engagement
**POST /api/v1/engagements**
```json
Request: {
  "client_id": 1,
  "name": "New Audit",
  "engagement_type": "statutory_audit",
  "recurrence_pattern": "annual",
  "start_date": "2026-04-01",
  "end_date": "2026-09-30"
}
Response: { "id": 9, "name": "New Audit" }
```

### Update Engagement
**PATCH /api/v1/engagements/{id}**
```json
Request: { "status": "completed" }
Response: { "id": 1, "name": "Annual Audit FY26" }
```

### Delete Engagement (soft)
**DELETE /api/v1/engagements/{id}**
```json
Response: { "detail": "Engagement deactivated" }
```

### Engagement Types
`statutory_audit`, `internal_audit`, `tax_audit`, `consulting`, `special_assignment`, `other`

### Recurrence Patterns
`one_off`, `weekly`, `fortnightly`, `monthly`, `quarterly`, `annual`

### Engagement Status
`active`, `on_hold`, `completed`, `lost_client`

---

## Assignments

### List Assignments
**GET /api/v1/assignments?limit=50&offset=0&team_member_id=1&engagement_instance_id=1**
```json
Response: {
  "items": [
    {
      "id": 1,
      "team_member_id": 1,
      "team_member_name": "Rajesh Kumar",
      "engagement_instance_id": 5,
      "role_on_engagement": "Lead Auditor",
      "allocation_percent": 50,
      "start_date": "2026-04-01",
      "end_date": "2026-06-30"
    }
  ],
  "total": 23, "limit": 50, "offset": 0
}
```

### Create Assignment
**POST /api/v1/assignments**
```json
Request: {
  "team_member_id": 1,
  "engagement_instance_id": 5,
  "allocation_percent": 50,
  "start_date": "2026-04-01",
  "end_date": "2026-06-30",
  "role_on_engagement": "Lead Auditor"
}
Response: { "id": 24, "team_member_id": 1 }
```

### Update Assignment
**PATCH /api/v1/assignments/{id}**
```json
Request: { "allocation_percent": 75 }
Response: { "id": 1, "team_member_id": 1 }
```

### Allocation Rules (enforced)
- allocation_percent: 1-100
- end_date >= start_date
- Assignment dates must fall within engagement instance dates
- Total allocation per team member <= 100%
- Cannot overlap with approved leave
- TeamMember must be active

---

## Leaves

### List Leaves
**GET /api/v1/leaves?limit=50&offset=0&team_member_id=1&status=pending**
```json
Response: {
  "items": [
    {
      "id": 1,
      "team_member_id": 1,
      "team_member_name": "Rajesh Kumar",
      "leave_type": "vacation",
      "status": "pending",
      "start_date": "2026-05-01",
      "end_date": "2026-05-05",
      "reason": "Family vacation"
    }
  ],
  "total": 3, "limit": 50, "offset": 0
}
```

### Create Leave
**POST /api/v1/leaves**
```json
Request: {
  "team_member_id": 1,
  "leave_type": "vacation",
  "start_date": "2026-05-01",
  "end_date": "2026-05-05",
  "reason": "Family vacation"
}
Response: { "id": 4, "team_member_id": 1 }
```

### Update Leave
**PATCH /api/v1/leaves/{id}**
```json
Request: { "status": "approved" }
Response: { "id": 1, "status": "approved" }
```

### Leave Types
`sick`, `vacation`, `exam_leave`, `other`

### Leave Status
`pending`, `approved`, `rejected`

---

## Extension Requests

### List Extensions
**GET /api/v1/extensions?status=pending**
```json
Response: {
  "items": [
    {
      "id": 1,
      "team_member_id": 5,
      "team_member_name": "Priya Sharma",
      "engagement_instance_id": 3,
      "allocation_percent": 25,
      "start_date": "2026-07-01",
      "end_date": "2026-09-30",
      "role_on_engagement": "Senior Auditor",
      "reason": "Need additional resource for tax season",
      "status": "pending",
      "requested_by": "Rajesh Kumar",
      "created_at": "2026-07-12T10:00:00"
    }
  ],
  "total": 1
}
```

### Create Extension Request
**POST /api/v1/extensions**
```json
Request: {
  "team_member_id": 5,
  "engagement_instance_id": 3,
  "allocation_percent": 25,
  "start_date": "2026-07-01",
  "end_date": "2026-09-30",
  "role_on_engagement": "Senior Auditor",
  "reason": "Need additional resource for tax season"
}
Response: { "id": 2, "status": "pending", "message": "Extension request submitted for approval" }
```

### Approve Extension
**POST /api/v1/extensions/{id}/approve**
```json
Request: { "note": "Approved" }
Response: { "id": 1, "status": "approved", "detail": "Extension approved and assignment created" }
```

### Reject Extension
**POST /api/v1/extensions/{id}/reject**
```json
Request: { "note": "Not enough budget" }
Response: { "id": 1, "status": "rejected", "detail": "Extension rejected" }
```

---

## Approval Requests

### List Pending Approvals
**GET /api/v1/approval-requests**
```json
Response: {
  "items": [
    {
      "id": 1,
      "resource_type": "assignment",
      "resource_id": null,
      "operation": "create",
      "requested_by_user_id": 423,
      "payload": { "team_member_id": 1, "engagement_instance_id": 5, "allocation_percent": 50 },
      "status": "pending",
      "created_at": "2026-07-12T10:00:00"
    }
  ],
  "total": 1
}
```

### Approve Request
**POST /api/v1/approval-requests/{id}/approve**
```json
Request: { "note": "Looks good" }
Response: { "id": 1, "status": "approved", "detail": "Request approved and applied" }
```

### Reject Request
**POST /api/v1/approval-requests/{id}/reject**
```json
Request: { "note": "Insufficient justification" }
Response: { "id": 1, "status": "rejected", "detail": "Request rejected" }
```

---

## Approval Rules (Admin Settings)

### Get Approval Rules
**GET /admin/settings/list** (web route, returns JSON)
```json
Response: [
  { "key": "bench_rolloff_days", "value": "7", "description": "..." },
  { "key": "bulk_upload_max_rows", "value": "8000", "description": "..." }
]
```

### Resource Types for Approval
`assignment`, `engagement`, `client`, `team_member`, `leave`

### Operation Types
`create`, `update`, `delete`

---

## Registration

### Check Domain
**POST /auth/register/check-domain** (form data)
```
email: user@pkfindia.com
```
→ Redirects to OTP step if domain matches a firm

### Verify OTP
**POST /auth/register/verify-otp** (form data)
```
otp: 123456
```
→ Redirects to password step if OTP valid

### Complete Registration
**POST /auth/register/complete** (form data)
```
display_name: John Doe
password: SecurePass123
confirm_password: SecurePass123
```
→ Creates user, adds to firm as viewer, auto-login

---

## UI Components

### Navigation
- **Navbar (desktop):** Logo → splanly by SkilledCA | Dark mode toggle (moon icon) | User name + Role ▾
- **Sidebar (hamburger):** Logo + Firm name | Nav links with icons | Admin section | Theme colors | Switch Firm | Change Password | Logout
- **User Dropdown:** User info | Change Password | Logout

### Pages

#### Dashboard
- Stat cards: Team Members, Clients, Active Engagements, Current Assignments, Bench, Pending Leaves
- Recent assignments table
- Quick actions

#### Team Members
- Data table with search, filters (business_role, branch, active)
- Pagination
- Create/Edit form with fields: name, email, employee_code, business_role, seniority_level, date_of_joining, branch

#### Clients
- Data table with search, filters
- Create/Edit form with fields: name, code, industry

#### Engagements
- Data table with search, filters (status, client)
- Detail page with instances
- Create/Edit form with fields: client, name, engagement_type, recurrence_pattern, start_date, end_date

#### Assignments
- Data table with search, filters (team_member, engagement_instance)
- Assign Staff page showing all members with allocation status
- Create/Edit form with fields: team_member, engagement_instance, allocation_percent, start_date, end_date, role

#### Leaves
- Data table with search, filters (team_member, status)
- Create/Edit form with fields: team_member, leave_type, start_date, end_date, reason
- Approve/Reject buttons for pending leaves

#### Bench Dashboard
- On-bench now (members without current assignment)
- Rolling-off soon (based on bench_rolloff_days setting)

#### Users (Admin)
- Tabbed: All Users | Pending Approvals | Extension Requests | Approval Logs
- User list with role badges, edit/deactivate
- Approve/Reject buttons for pending items

#### Settings (Admin)
- Tabbed: General | Approval Rules | Domains
- General: bench_rolloff_days, bulk_upload_max_rows
- Approval Rules: toggle table for resource × operation
- Domains: comma-separated allowed email domains

#### Login
- Email + password form
- Microsoft SSO button (if configured)
- Link to register

#### Register
- 3-step wizard: Email → OTP → Password
- Shows matching firm name after domain check

#### Firm Selector
- Shows all firms user belongs to
- Click to switch firm

---

## Color Palette

### Primary Colors
- Primary: `hsl(188, 70%, 40%)` (teal)
- Primary Foreground: `white`
- Background: `white`
- Foreground: `hsl(188, 50%, 7%)`
- Card: `white`
- Muted: `hsl(188, 20%, 92%)`
- Border: `hsl(188, 20%, 86%)`

### Status Colors
- Success: `hsl(152, 60%, 38%)` (green)
- Warning: `hsl(32, 95%, 48%)` (amber)
- Error: `hsl(0, 72%, 51%)` (red)
- Info: `hsl(188, 65%, 45%)` (teal)

### Role Colors
- Admin: primary badge
- Moderator: secondary badge
- Viewer: default badge

---

## Data Models (TypeScript)

```typescript
interface User {
  id: number;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
}

interface Firm {
  id: number;
  name: string;
  code: string;
  logo_url: string | null;
  allowed_domains: string | null;
  is_active: boolean;
}

interface FirmUser {
  firm: Firm;
  role: "admin" | "moderator" | "viewer";
}

interface TeamMember {
  id: number;
  firm_id: number;
  branch_id: number | null;
  employee_code: string | null;
  name: string;
  email: string;
  business_role: BusinessRole;
  is_oversight_only: boolean;
  seniority_level: string | null;
  date_of_joining: string | null;
  date_of_relieving: string | null;
  is_active: boolean;
}

interface Client {
  id: number;
  firm_id: number;
  name: string;
  code: string | null;
  industry: string | null;
  is_active: boolean;
}

interface Engagement {
  id: number;
  client_id: number;
  client_name: string | null;
  name: string;
  engagement_type: EngagementType;
  recurrence_pattern: RecurrencePattern;
  start_date: string;
  end_date: string | null;
  status: EngagementStatus;
  is_active: boolean;
}

interface Assignment {
  id: number;
  team_member_id: number;
  team_member_name: string | null;
  engagement_instance_id: number;
  role_on_engagement: string | null;
  allocation_percent: number;
  start_date: string;
  end_date: string;
}

interface Leave {
  id: number;
  team_member_id: number;
  team_member_name: string | null;
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  status: LeaveStatus;
  reason: string | null;
}

interface ExtensionRequest {
  id: number;
  team_member_id: number;
  team_member_name: string | null;
  engagement_instance_id: number;
  allocation_percent: number;
  start_date: string;
  end_date: string;
  role_on_engagement: string | null;
  reason: string | null;
  status: "pending" | "approved" | "rejected";
  requested_by: string | null;
  created_at: string;
}

interface ApprovalRequest {
  id: number;
  resource_type: ResourceType;
  resource_id: number | null;
  operation: OperationType;
  requested_by_user_id: number;
  payload: Record<string, any>;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

type BusinessRole = "partner" | "director" | "ca_manager" | "paid_assistant" | "staff" | "article" | "data_analyst";
type EngagementType = "statutory_audit" | "internal_audit" | "tax_audit" | "consulting" | "special_assignment" | "other";
type RecurrencePattern = "one_off" | "weekly" | "fortnightly" | "monthly" | "quarterly" | "annual";
type EngagementStatus = "active" | "on_hold" | "completed" | "lost_client";
type LeaveType = "sick" | "vacation" | "exam_leave" | "other";
type LeaveStatus = "pending" | "approved" | "rejected";
type ResourceType = "assignment" | "engagement" | "client" | "team_member" | "leave";
type OperationType = "create" | "update" | "delete";
```

---

## API Base URL
- **Local:** `http://localhost:8000`
- **Production:** `https://pm-tool-5pg6.onrender.com`

## Auth Header
```
Authorization: Bearer <access_token>
```
