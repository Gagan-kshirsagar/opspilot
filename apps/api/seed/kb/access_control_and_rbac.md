# Access Control and Role-Based Access (RBAC) Policy

## 1. System Roles Hierarchy
OpsPilot implements four distinct user roles:

1. **Admin**:
   - Full system access.
   - Can create, update, and delete users and teams.
   - Can resolve and manage incidents across all services.
   - Can trigger knowledge base ingestion and configure environment secrets.
2. **Manager**:
   - Can create and update users within assigned teams.
   - Can resolve and update incidents.
   - Read-only access to global settings.
3. **Viewer**:
   - Read-only access across all services, incidents, user lists, and knowledge base docs.
   - Can query the AI Chat / Knowledge Base interface.
   - Cannot mutate system state or resolve incidents.
4. **Guest**:
   - Ephemeral session for preview and demonstration purposes.
   - Read-only access to dashboards, services, incidents, and Q&A chat.

## 2. Principle of Least Privilege (PoLP)
- Production database direct write access is strictly prohibited for personal accounts; write operations must occur via audited service accounts.
- Emergency production database access ("Break-Glass") requires dual approval from two Engineering Leads and automatically expires after 4 hours.
- All administrative actions (user creation, deletion, incident resolution) are logged with user ID and timestamp for compliance audits.
