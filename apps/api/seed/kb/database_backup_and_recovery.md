# Database Backup and Recovery Runbook

## 1. Backup Strategy
- **Continuous WAL Archiving**: Write-Ahead Logs (WAL) are streamed continuously to encrypted Amazon S3 buckets with cross-region replication enabled.
- **Daily Automated Snapshots**: Full automated Postgres snapshots are captured daily at 02:00 AM UTC and retained for 35 days.
- **Weekly Cold Storage Backups**: Compressed, encrypted database dumps are stored in immutable Glacier Vault for 1 year for compliance.

## 2. Recovery Objectives
- **RPO (Recovery Point Objective)**: Less than **5 minutes** of data loss via continuous WAL replay.
- **RTO (Recovery Time Objective)**: Database cluster restored and serving queries within **30 minutes**.

## 3. Point-in-Time Recovery (PITR) Execution
To restore Postgres to a specific point in time (e.g. before an accidental data deletion or migration error):
1. Identify the target timestamp in UTC: e.g. `2026-08-17 14:32:00 UTC`.
2. Provision a new Postgres instance from the most recent pre-incident base snapshot:
   `aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier opspilot-prod --target-db-instance-identifier opspilot-restore --restore-time "2026-08-17T14:32:00Z"`.
3. Verify table counts, row integrity, and pgvector extension status on the restored instance.
4. Update the application connection string `OPSPILOT_DATABASE_URL` to point to the restored instance endpoint and restart backend services.
