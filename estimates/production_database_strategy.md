# EFData Production Database Strategy

## Current State
- PostgreSQL on local network (192.168.1.184)
- ~50,000 records across 8 economic components
- Database name: econdata
- No SSL, basic password auth

## Ideal Production Setup

### 1. Managed PostgreSQL Service (Recommended)
**Best options for your budget:**

#### DigitalOcean Managed PostgreSQL
- **Cost**: $15/month (1GB RAM, 10GB storage)
- **Pros**: Automatic backups, SSL included, 99.5% uptime SLA
- **Setup time**: 10 minutes
- **Good for**: Getting started quickly with minimal ops burden

#### AWS RDS PostgreSQL
- **Cost**: ~$20/month (t4g.micro, 20GB storage)
- **Pros**: Industry standard, great monitoring, automated backups
- **Cons**: More complex setup, AWS learning curve

#### Supabase
- **Cost**: Free tier (500MB), then $25/month
- **Pros**: PostgreSQL + instant REST API, great for prototyping
- **Cons**: Vendor lock-in risk

### 2. Security Requirements

#### Non-negotiables:
```yaml
# Production database MUST have:
ssl_mode: require
password_complexity: high  # 16+ chars, mixed case, numbers, symbols
connection_limit: 10  # Prevent connection exhaustion
backup_retention: 7_days
point_in_time_recovery: enabled
```

#### Network Security:
- Whitelist only your app servers
- No public internet access
- VPN or SSH tunnel for admin access

### 3. Performance Optimization

#### Indexes needed:
```sql
-- Already critical for your queries
CREATE INDEX idx_time_component ON fact_circular_flow(time_key, component_key);
CREATE INDEX idx_date_value ON dim_time(date_value);
CREATE INDEX idx_component_code ON dim_circular_flow_component(component_code);

-- For API performance
CREATE INDEX idx_date_range ON fact_circular_flow(time_key) 
  WHERE time_key > (SELECT time_key FROM dim_time WHERE date_value > '2020-01-01');
```

#### Connection Pooling:
- Use PgBouncer or similar
- Pool size: 20-30 connections
- Prevents "too many connections" errors

### 4. Backup Strategy

#### Automated Backups:
- Daily full backups (3 AM)
- Keep 7 daily, 4 weekly, 12 monthly
- Test restore monthly

#### Backup Script:
```bash
#!/bin/bash
# Run via cron: 0 3 * * * /path/to/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="efdata"

# Backup with compression
pg_dump -h $PSQL_HOST -U $PSQL_USER -d $DB_NAME | gzip > $BACKUP_DIR/efdata_$DATE.sql.gz

# Upload to S3/Backblaze B2 (cheap storage)
aws s3 cp $BACKUP_DIR/efdata_$DATE.sql.gz s3://efdata-backups/

# Keep only 7 local backups
find $BACKUP_DIR -name "efdata_*.sql.gz" -mtime +7 -delete
```

### 5. Monitoring

#### Essential Metrics:
- Query performance (slow query log)
- Connection count
- Disk usage growth rate
- Replication lag (if using read replicas)

#### Free Monitoring:
- DigitalOcean/AWS built-in metrics
- Grafana + Prometheus (self-hosted)
- PgHero (simple Rails app)

### 6. Disaster Recovery

#### RPO/RTO Targets:
- Recovery Point Objective: 1 hour (max data loss)
- Recovery Time Objective: 2 hours (max downtime)

#### Implementation:
1. Automated backups every hour
2. Standby replica in different availability zone
3. Documented restore procedure
4. Test restore quarterly

### 7. Cost-Effective Growth Path

#### Phase 1 (Now - 6 months): $15-25/month
- DigitalOcean managed PostgreSQL
- Single node, 10GB storage
- Daily backups

#### Phase 2 (6-12 months): $50-100/month
- Add read replica for API queries
- Increase storage to 50GB
- Add monitoring

#### Phase 3 (12+ months): $200+/month
- Multi-region setup
- Dedicated CPU instances
- Advanced monitoring/alerting

### 8. Migration Checklist

- [ ] Set up managed database
- [ ] Enable SSL
- [ ] Configure automated backups
- [ ] Update .env with new credentials
- [ ] Test connection from Docker
- [ ] Migrate data with pg_dump/restore
- [ ] Update DNS/connection strings
- [ ] Test all API endpoints
- [ ] Monitor for 24 hours
- [ ] Destroy old database

### 9. Quick Start Commands

```bash
# Export from current DB
pg_dump -h 192.168.1.184 -U websinthe -d econdata > efdata_export.sql

# Import to new DB
psql -h new-host.db.com -U efdata_user -d efdata < efdata_export.sql

# Test connection
psql -h new-host.db.com -U efdata_user -d efdata -c "SELECT COUNT(*) FROM fact_circular_flow;"
```

### 10. Emergency Contacts

Keep these handy:
- Database provider support
- Your backup location credentials
- Secondary admin with access
- Client notification template

---

**Bottom Line**: Start with DigitalOcean managed PostgreSQL at $15/month. It's the sweet spot of cost, features, and simplicity for your current scale. You can migrate in under an hour and sleep better at night.