# Post-Mortem Template

**Incident ID**: INC-[TYPE]-YYYYMMDD-HHmm
**Date**: YYYY-MM-DD
**Incident Commander**: [Name]
**Document Owner**: [Name]
**Status**: [Draft / Final]

---

## Executive Summary

*Brief 2-3 paragraph summary for executives covering:*

- What happened
- Impact to business/customers
- Root cause
- Key actions taken
- Preventive measures

**Impact Snapshot:**

- Severity: [CRITICAL / HIGH / MEDIUM / LOW]
- Duration: [X hours Y minutes]
- Affected Services: [List]
- Customer Impact: [X users / $Y revenue]
- Data Compromised: [YES/NO - details]

---

## Incident Details

### Incident Type

- [ ] Security Incident (Breach, Attack, Vulnerability)
- [ ] Service Outage (Infrastructure, Application, Database)
- [ ] Data Incident (Loss, Corruption, Leak)
- [ ] Performance Degradation
- [ ] Other: ___________

### Severity Classification

**Final Severity**: [CRITICAL / HIGH / MEDIUM / LOW]

**Justification**:

- Business Impact: [Description]
- Technical Impact: [Description]
- Customer Impact: [Description]
- Reputational Impact: [Description]

### Affected Systems & Services

| System/Service | Impact Level | Downtime | Recovery Time |
|----------------|--------------|----------|---------------|
| Production API | Complete outage | 3h 45m | 4h 15m |
| Database | Degraded | 2h | 3h |
| Example Service | Partial | 1h 30m | 2h |

---

## Timeline

*All times in UTC. Include key events only.*

### Detection Phase

| Time (UTC) | Event | Owner | Notes |
|------------|-------|-------|-------|
| 2025-12-19 14:23 | First alert triggered | Automated monitoring | CloudWatch alarm: high error rate |
| 2025-12-19 14:25 | On-call engineer paged | PagerDuty | @engineer-name |
| 2025-12-19 14:27 | Incident confirmed | @engineer-name | Verified not false positive |
| 2025-12-19 14:30 | Incident declared | @engineer-name | Created war room #incident-* |

### Investigation Phase

| Time (UTC) | Event | Owner | Notes |
|------------|-------|-------|-------|
| 2025-12-19 14:35 | Root cause identified | @engineer-name | SQL query timeout issue |
| 2025-12-19 14:40 | Impact assessment complete | @incident-commander | ~5000 users affected |

### Mitigation Phase

| Time (UTC) | Event | Owner | Notes |
|------------|-------|-------|-------|
| 2025-12-19 14:45 | Mitigation started | @devops-lead | Scaling database read replicas |
| 2025-12-19 15:00 | Partial restoration | @devops-lead | 50% of traffic restored |
| 2025-12-19 15:30 | Full restoration | @devops-lead | All services operational |

### Recovery Phase

| Time (UTC) | Event | Owner | Notes |
|------------|-------|-------|-------|
| 2025-12-19 15:45 | Monitoring normalized | @engineer-name | Error rates back to baseline |
| 2025-12-19 16:00 | Incident resolved | @incident-commander | All metrics normal |
| 2025-12-19 16:30 | Post-incident monitoring | @engineer-name | Enhanced monitoring for 24h |

**Total Duration**:

- Time to Detect: [X minutes]
- Time to Acknowledge: [X minutes]
- Time to Mitigate: [X hours Y minutes]
- Time to Resolve: [X hours Y minutes]
- Total Incident Duration: [X hours Y minutes]

---

## Impact Assessment

### Customer Impact

- **Users Affected**: [X users / Y% of total]
- **User Experience**: [Complete outage / Degraded / Intermittent errors]
- **Geography**: [All regions / Specific regions: US, EU, etc.]
- **Customer Segment**: [All / Enterprise / Free tier / etc.]

**Customer-Facing Impact**:

- Unable to [specific functionality]
- Slow response times (average [X]ms)
- Error messages: "[Error text]"
- Failed transactions: [X]

### Business Impact

- **Revenue Loss**: $[Amount] (estimated)
  - Lost transactions: [X transactions]
  - Subscription cancellations: [X]
  - Refunds issued: $[Amount]
- **SLA Violations**: [X customer SLAs breached]
- **SLA Credits**: $[Amount] owed
- **Support Tickets**: [X tickets created]
- **Public Relations**: [Social media mentions, press coverage]

### Technical Impact

- **Systems Affected**: [List all systems]
- **Data Integrity**: [OK / Compromised - details]
- **Data Loss**: [None / X records / X GB]
- **Services Degraded**: [List]
- **Security Posture**: [Unchanged / Compromised - details]

### Regulatory & Legal Impact

- **Regulatory Reporting Required**: [YES/NO]
  - GDPR: [YES/NO - within 72h]
  - HIPAA: [YES/NO - within 60 days]
  - PCI DSS: [YES/NO - immediate]
  - State laws: [YES/NO - varies]
- **Legal Implications**: [Description]
- **Compliance Violations**: [List any violations]

---

## Root Cause Analysis

### The Five Whys

1. **Why did the incident occur?**
   - [First-level cause]

2. **Why did [first-level cause] happen?**
   - [Second-level cause]

3. **Why did [second-level cause] happen?**
   - [Third-level cause]

4. **Why did [third-level cause] happen?**
   - [Fourth-level cause]

5. **Why did [fourth-level cause] happen?**
   - [ROOT CAUSE]

### Root Cause Summary

**Primary Root Cause**:
[Detailed explanation of the fundamental cause]

**Contributing Factors**:

1. [Factor 1]
2. [Factor 2]
3. [Factor 3]

**Why Was This Not Prevented?**

- Detection gaps: [Explanation]
- Process gaps: [Explanation]
- Technical gaps: [Explanation]
- Training gaps: [Explanation]

**Example**:

```
Primary Root Cause:
Database query timeout due to missing index on frequently queried column.

Contributing Factors:
1. No query performance monitoring on new feature
2. Load testing did not include production-scale data
3. Database index creation not part of deployment checklist
4. No automated query plan analysis in CI/CD

Why Was This Not Prevented?
- No slow query alerts configured on production database
- Code review didn't catch missing index (not in checklist)
- Staging environment had limited data (didn't surface issue)
```

---

## What Went Well

*List things that worked well during incident response*

### Detection & Alerting

- ✅ Automated monitoring detected issue within 2 minutes
- ✅ On-call engineer responded immediately
- ✅ Clear alert message with actionable information

### Response & Communication

- ✅ War room created quickly, team assembled in 5 minutes
- ✅ Clear incident commander designation
- ✅ Regular status updates to stakeholders
- ✅ Customer communication sent within 30 minutes

### Technical Response

- ✅ Runbooks were up-to-date and helpful
- ✅ Database scaling executed smoothly
- ✅ Rollback procedure worked as expected

### Tools & Processes

- ✅ Logging provided sufficient detail for RCA
- ✅ Monitoring dashboards were accurate
- ✅ Backup systems functioned correctly

---

## What Went Wrong

*List failures, gaps, and issues during incident*

### Detection & Alerting

- ❌ Should have detected earlier (query performance degrading for 2 hours prior)
- ❌ Alert didn't include severity level
- ❌ No automated escalation after 5 minutes

### Response & Communication

- ❌ Initial diagnosis was incorrect (wasted 15 minutes)
- ❌ Customer communication template was outdated
- ❌ Executive team wasn't notified for 45 minutes
- ❌ War room was chaotic, multiple people talking over each other

### Technical Response

- ❌ Didn't have staging environment to test fix
- ❌ Mitigation took longer than expected (unclear docs)
- ❌ Rollback initially failed (config issue)

### Tools & Processes

- ❌ Runbook was missing critical step
- ❌ Didn't have access to production database initially
- ❌ No documented escalation path
- ❌ Load balancer logs not retained long enough for analysis

---

## Action Items

*All action items must have: clear description, owner, due date, priority*

### Priority: CRITICAL (Must complete within 7 days)

| ID | Action Item | Owner | Due Date | Status |
|----|-------------|-------|----------|--------|
| AI-001 | Add database index on `users.email` column | @db-team | 2025-12-26 | 🔴 Open |
| AI-002 | Enable slow query logging with 1s threshold | @devops-team | 2025-12-24 | 🔴 Open |
| AI-003 | Deploy automated query performance monitoring | @backend-team | 2025-12-27 | 🔴 Open |
| AI-004 | Update incident response runbook with missing steps | @security-team | 2025-12-22 | 🔴 Open |

### Priority: HIGH (Must complete within 30 days)

| ID | Action Item | Owner | Due Date | Status |
|----|-------------|-------|----------|--------|
| AI-005 | Implement load testing with production-scale data | @qa-team | 2026-01-15 | 🔴 Open |
| AI-006 | Add query plan analysis to CI/CD pipeline | @devops-team | 2026-01-20 | 🔴 Open |
| AI-007 | Create database performance dashboard | @platform-team | 2026-01-18 | 🔴 Open |
| AI-008 | Update customer communication templates | @support-team | 2026-01-10 | 🔴 Open |
| AI-009 | Conduct incident response training for all engineers | @security-team | 2026-01-25 | 🔴 Open |

### Priority: MEDIUM (Must complete within 90 days)

| ID | Action Item | Owner | Due Date | Status |
|----|-------------|-------|----------|--------|
| AI-010 | Implement automated database index recommendations | @db-team | 2026-03-15 | 🔴 Open |
| AI-011 | Enhance staging environment to match production scale | @devops-team | 2026-03-20 | 🔴 Open |
| AI-012 | Create executive communication playbook | @cto | 2026-02-28 | 🔴 Open |
| AI-013 | Implement automated escalation in PagerDuty | @devops-team | 2026-02-15 | 🔴 Open |

### Long-term Improvements

| ID | Action Item | Owner | Due Date | Status |
|----|-------------|-------|----------|--------|
| AI-014 | Implement chaos engineering practices | @platform-team | 2026-06-30 | 🔴 Open |
| AI-015 | Build automated recovery systems | @sre-team | 2026-09-30 | 🔴 Open |

**Status Legend**: 🔴 Open | 🟡 In Progress | 🟢 Complete | ⚫ Blocked

---

## Lessons Learned

### What We Learned

1. **Technical Lessons**
   - Database query performance must be monitored in production
   - Staging environments must match production scale
   - Indexes should be part of deployment checklist

2. **Process Lessons**
   - Incident commander role is critical for coordination
   - Customer communication should be automated
   - Executive team needs earlier notification

3. **Cultural Lessons**
   - Team responded well under pressure
   - Need more cross-functional collaboration
   - On-call rotation needs better documentation

### How We'll Improve

1. **Immediate Changes**
   - Deploy missing database indexes
   - Enable slow query monitoring
   - Update runbooks with lessons from this incident

2. **Short-term Changes**
   - Implement comprehensive load testing
   - Enhance monitoring and alerting
   - Improve incident response training

3. **Long-term Changes**
   - Build resilient architecture patterns
   - Implement chaos engineering
   - Create self-healing systems

---

## Prevention Measures

### Technical Preventions

**Implemented**:

- ✅ [Preventive measure with implementation date]

**Planned**:

- 🔴 Add database query performance monitoring (Due: 2025-12-27)
- 🔴 Implement automated index suggestions (Due: 2026-03-15)
- 🔴 Deploy query plan analysis in CI/CD (Due: 2026-01-20)

### Process Preventions

**Implemented**:

- ✅ Updated deployment checklist to include index verification
- ✅ Added RCA step to all incident response procedures

**Planned**:

- 🔴 Quarterly disaster recovery drills
- 🔴 Monthly incident response training
- 🔴 Code review checklist updates

### Detection Improvements

**Implemented**:

- ✅ Enhanced alerting thresholds
- ✅ Added new monitoring dashboards

**Planned**:

- 🔴 Implement predictive alerting (ML-based)
- 🔴 Deploy distributed tracing
- 🔴 Add anomaly detection

---

## Supporting Information

### Related Incidents

- [INC-YYYY-001]: Similar database performance issue (2025-10-15)
- [INC-YYYY-002]: Related to query optimization (2025-08-22)

### Related Documentation

- [Runbook: Database Performance Issues](/Users/coreyfoster/DevSkyy/docs/runbooks/database-performance.md)
- [Architecture: Database Scaling Strategy](/Users/coreyfoster/DevSkyy/docs/architecture/database-scaling.md)
- [Playbook: Incident Response](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

### External References

- CVE-YYYY-XXXXX (if security incident)
- Vendor advisory: [Link]
- Blog post: [Link] (if publicly disclosed)

---

## Metrics & KPIs

### Response Metrics

| Metric | Target | Actual | Met? |
|--------|--------|--------|------|
| Time to Detect | < 5 min | 2 min | ✅ |
| Time to Acknowledge | < 5 min | 2 min | ✅ |
| Time to Triage | < 15 min | 12 min | ✅ |
| Time to Mitigate | < 1 hour | 2h 15m | ❌ |
| Time to Resolve | < 4 hours | 3h 45m | ✅ |

### Incident Costs

| Cost Category | Amount | Notes |
|---------------|--------|-------|
| Revenue Loss | $12,500 | 250 failed transactions @ $50 avg |
| SLA Credits | $8,000 | 20 enterprise customers |
| Support Costs | $2,000 | 4 hours × 10 agents |
| Engineering Time | $15,000 | 30 engineer-hours @ $500/hr |
| **Total Cost** | **$37,500** | |

### Service Metrics

| Metric | Before Incident | During Incident | After Incident |
|--------|-----------------|-----------------|----------------|
| Availability | 99.99% | 95.2% | 99.99% |
| Error Rate | 0.01% | 15.3% | 0.01% |
| Response Time (p95) | 120ms | 8500ms | 115ms |
| Request Rate | 1000 req/s | 150 req/s | 1000 req/s |

---

## Post-Mortem Meeting

**Date**: YYYY-MM-DD
**Attendees**: [List all attendees]
**Duration**: [X minutes]
**Recording**: [Link to recording]

### Discussion Notes

- [Key discussion points]
- [Decisions made]
- [Open questions]

### Follow-up Actions

- [ ] Schedule follow-up review in 30 days
- [ ] Share post-mortem with entire engineering team
- [ ] Update public status page incident report
- [ ] Present findings to executive team
- [ ] Archive incident data and forensics

---

## Sign-off

**Incident Commander**: _________________________ Date: _______
**Technical Lead**: _________________________ Date: _______
**CTO/VP Engineering**: _________________________ Date: _______

---

## Appendix

### A. Technical Details

**System Architecture Diagram**:
[Include or link to architecture diagram]

**Configuration Changes**:

```yaml
# Before
database:
  max_connections: 100
  query_timeout: 30s

# After
database:
  max_connections: 200
  query_timeout: 10s
  slow_query_log: enabled
  slow_query_threshold: 1s
```

### B. Data & Queries

**Database Queries Used in Investigation**:

```sql
-- Identify slow queries
SELECT query, calls, mean_time, max_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;

-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100000
  AND attname NOT IN (
    SELECT indexdef FROM pg_indexes
  );
```

### C. Communication Samples

**Customer Communication (Initial)**:

```
Subject: Service Disruption Notice

We are currently experiencing technical difficulties affecting [service].
Our team is actively working on resolution.

Status updates: https://status.skyyrose.com
Expected resolution: [Time]
```

**Customer Communication (Resolution)**:

```
Subject: Service Restored

Services have been fully restored as of [Time].

What happened: [Brief explanation]
Impact: [Description]
Prevention: [What we're doing]

We apologize for the inconvenience.
```

### D. Incident Response Timeline (Detailed)

[More detailed timeline with screenshots, logs, etc.]

---

**Document Version**: 1.0
**Last Updated**: YYYY-MM-DD
**Next Review**: YYYY-MM-DD
**Classification**: [Internal / Public]

---

## Template Usage Instructions

1. **Fill out within 48 hours of incident resolution**
2. **Schedule post-mortem meeting within 1 week**
3. **Complete all action items within specified timeframes**
4. **Share with all stakeholders**
5. **Archive for future reference**
6. **Update runbooks based on learnings**

**Remember**: The goal is learning and improvement, not blame.
