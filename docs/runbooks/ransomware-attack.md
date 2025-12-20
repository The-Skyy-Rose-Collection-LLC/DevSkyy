# Ransomware Attack Response

**Severity Level**: CRITICAL
**Last Updated**: 2025-12-19
**Owner**: Security Operations Team, IT Operations
**Related**: [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

## Overview

Ransomware encrypts files and demands payment for decryption. This runbook covers detection, containment, recovery from backups, and preventing spread across the infrastructure.

## Detection

### Alert Triggers

**Automated Alerts:**

- Mass file encryption detected (file extension changes)
- Unusual file modification patterns
- Ransom notes detected in directories
- Encrypted file detection (entropy analysis)
- Backup deletion attempts
- Shadow copy deletion (Windows)
- Suspicious process execution (encryptors)
- Unusual network traffic to known ransomware C2 servers
- EDR alerts for known ransomware families

**Behavioral Indicators:**

- Rapid mass file modifications
- File extensions changed to .encrypted, .locked, .crypted
- READ_ME.txt or RANSOM_NOTE files appearing
- Desktop wallpaper changed to ransom message
- Systems becoming unresponsive
- Database files encrypted

### How to Identify

1. **File System Analysis**

   ```bash
   # Check for mass file modifications
   find /var/www /opt/skyyrose -type f -mtime -1 | wc -l
   # Unusually high number indicates possible encryption

   # Check for encrypted file extensions
   find / -type f \( -name "*.encrypted" -o -name "*.locked" -o -name "*.crypted" \) 2>/dev/null

   # Look for ransom notes
   find / -type f \( -name "*RANSOM*" -o -name "*READ*ME*" -o -name "*DECRYPT*" \) 2>/dev/null

   # Check file entropy (high entropy = encrypted)
   python scripts/check_file_entropy.py --path /var/www
   ```

2. **Process Analysis**

   ```bash
   # Look for suspicious processes
   ps aux | grep -E "(crypt|lock|ransom)" -i

   # Check recently started processes
   ps -eo pid,lstart,cmd --sort=start_time | tail -20

   # Check for known ransomware process names
   ps aux | grep -E "(cerber|locky|ryuk|darkside|conti)" -i
   ```

3. **Network Analysis**

   ```bash
   # Check for C2 communications
   netstat -tunap | grep ESTABLISHED | awk '{print $5}' | cut -d: -f1 | sort | uniq

   # Check DNS queries to suspicious domains
   grep -E "(\.onion|\.bit|suspicious-tld)" /var/log/syslog

   # Monitor for data exfiltration
   iftop -t -s 1 -L 100
   ```

4. **EDR/Antivirus Logs**

   ```bash
   # Check ClamAV logs
   grep -i "ransomware\|trojan\.ransom" /var/log/clamav/clamav.log

   # Check system logs for encryption attempts
   journalctl --since "1 hour ago" | grep -i "encrypt\|ransom"
   ```

5. **Backup Status Check**

   ```bash
   # Verify backups are intact
   ls -lh /backups/ | tail -20

   # Check backup integrity
   tar -tzf /backups/latest-backup.tar.gz >/dev/null 2>&1 && echo "OK" || echo "CORRUPTED"

   # Check cloud backups
   aws s3 ls s3://skyyrose-backups/ --recursive | tail -20
   ```

## Triage

### Severity Assessment

**CRITICAL - Code Red:**

- Production databases encrypted
- Multiple servers affected
- Backups deleted or encrypted
- Active lateral movement detected
- Customer data encrypted
- Payment systems down

**HIGH - Urgent Response:**

- Single system encrypted
- Backups intact and verified
- Contained to isolated network segment
- Non-production systems only

**MEDIUM - Contained Incident:**

- Ransomware detected and blocked
- No encryption occurred
- EDR successfully prevented execution

### Initial Containment Steps

**IMMEDIATE ACTIONS (within 5 minutes) - DO NOT DELAY:**

1. **ISOLATE INFECTED SYSTEMS - DO NOT SHUT DOWN**

   ```bash
   # Disconnect network interfaces (keeps system running for forensics)
   ip link set eth0 down
   ip link set wlan0 down

   # Alternative: block all traffic via iptables
   iptables -P INPUT DROP
   iptables -P OUTPUT DROP
   iptables -P FORWARD DROP

   # On other systems, block infected host
   ufw deny from <INFECTED_IP>
   ```

   **CRITICAL: Do NOT power off infected systems yet - running memory contains decryption keys**

2. **Prevent Spread**

   ```bash
   # Isolate entire network segment if spread detected
   # Disable network shares
   systemctl stop smbd nmbd
   umount -a -t cifs

   # Block SMB/RDP network-wide
   iptables -A INPUT -p tcp --dport 445 -j DROP
   iptables -A INPUT -p tcp --dport 3389 -j DROP

   # Disable network discovery
   systemctl stop avahi-daemon
   ```

3. **Protect Backups**

   ```bash
   # Make backups immutable immediately
   chattr +i /backups/*.tar.gz

   # Disconnect backup systems from network
   ip link set eth0 down  # On backup server

   # Enable S3 versioning and object lock (if not already)
   aws s3api put-bucket-versioning --bucket skyyrose-backups --versioning-configuration Status=Enabled
   aws s3api put-object-lock-configuration --bucket skyyrose-backups --object-lock-configuration 'ObjectLockEnabled=Enabled,Rule={DefaultRetention={Mode=GOVERNANCE,Days=30}}'
   ```

4. **Preserve Evidence**

   ```bash
   # Capture memory dump (contains potential decryption keys)
   dd if=/dev/mem of=/forensics/memory-dump-$(hostname)-$(date +%Y%m%d-%H%M%S).raw bs=1M

   # Capture disk image (before powering off)
   dd if=/dev/sda of=/forensics/disk-image-$(hostname)-$(date +%Y%m%d-%H%M%S).img bs=4M

   # Capture volatile data
   ps aux > /forensics/processes.txt
   netstat -tunap > /forensics/network.txt
   lsof > /forensics/open-files.txt
   ```

5. **Kill Ransomware Process**

   ```bash
   # Identify encryption process
   ps aux | sort -nk 3 | tail -10  # High CPU usage

   # Kill immediately
   kill -9 <RANSOMWARE_PID>

   # Prevent persistence
   systemctl disable <suspicious-service>
   rm /etc/systemd/system/<suspicious-service>
   ```

### Escalation Procedures

**CRITICAL Ransomware - IMMEDIATE ALL-HANDS:**

1. **Call** Security Lead: [PHONE] - **NOW**
2. **Call** CTO: [PHONE] - **NOW**
3. **Call** CEO: [PHONE] - **NOW**
4. **Activate** disaster recovery team
5. **Create** war room: `#incident-ransomware-YYYYMMDD`
6. **Conference call**: All senior leadership - **NOW**
7. **Notify** cyber insurance provider
8. **Notify** FBI Cyber Division (IC3.gov)
9. **Contact** professional incident response firm
10. **Alert** legal counsel

**DO NOT:**

- Pay ransom without executive and legal approval
- Delete infected systems (evidence)
- Communicate with attackers without coordination

## Investigation

### Forensic Analysis

1. **Identify Ransomware Variant**

   ```bash
   # Upload ransom note to ID Ransomware
   # Visit: https://id-ransomware.malwarehunterteam.com/

   # Check encrypted file headers
   hexdump -C /path/to/encrypted/file.encrypted | head

   # Search for known ransomware signatures
   clamscan -r --detect-pua=yes /infected/system/

   # Check for ransomware IOCs
   python scripts/check_ransomware_iocs.py --system /infected/
   ```

2. **Determine Entry Point**

   ```bash
   # Check for phishing emails (common vector)
   grep -r "suspicious-domain.com" /var/mail/

   # Check for RDP brute force
   grep "Failed password" /var/log/auth.log | tail -100

   # Check for vulnerability exploitation
   grep -E "(exploit|shellcode|payload)" /var/log/nginx/access.log

   # Check for malicious downloads
   grep -E "\.exe|\.dll|\.bat|\.ps1" /var/log/nginx/access.log
   ```

3. **Assess Damage**

   ```bash
   # Count encrypted files
   find / -type f -name "*.encrypted" 2>/dev/null | wc -l

   # Identify critical encrypted data
   find /var/lib/postgresql -name "*.encrypted" 2>/dev/null
   find /var/www/uploads -name "*.encrypted" 2>/dev/null

   # Check database status
   psql $DATABASE_URL -c "SELECT 1;" 2>&1
   # If error, database may be encrypted
   ```

4. **Check for Data Exfiltration**

   ```bash
   # Review network logs for large uploads
   awk '$10 > 100000000 {print $1, $7, $10}' /var/log/nginx/access.log

   # Check for connections to file-sharing sites
   grep -E "(mega\.nz|anonfiles|sendspace)" /var/log/squid/access.log
   ```

### Data Collection Checklist

- [ ] Ransomware variant identified
- [ ] Entry point determined
- [ ] Timeline of infection
- [ ] Affected systems inventory
- [ ] Encrypted files count
- [ ] Backup status verified
- [ ] Data exfiltration assessment
- [ ] Ransom amount demanded
- [ ] Attacker contact information
- [ ] IOCs collected
- [ ] Forensic images captured

## Remediation

### Recovery Process

**DO NOT PAY RANSOM unless authorized by CEO, Legal, and Insurance**

**Option 1: Restore from Backups (PREFERRED)**

1. **Verify Backup Integrity**

   ```bash
   # Test backup restoration on isolated system
   # Create test environment
   docker run -it --network none ubuntu:latest /bin/bash

   # Restore backup to test environment
   tar -xzf /backups/skyyrose-backup-YYYYMMDD.tar.gz -C /tmp/restore-test/

   # Verify data integrity
   md5sum /tmp/restore-test/important-file.db
   # Compare with pre-attack hash

   # Test database restoration
   psql -h localhost -U postgres -d test_restore < /backups/database-backup.sql
   ```

2. **Prepare Clean Infrastructure**

   ```bash
   # Provision new clean servers
   ansible-playbook playbooks/provision-clean-servers.yml

   # Harden new systems
   ansible-playbook playbooks/security-hardening.yml

   # Install latest security patches
   ansible all -m apt -a "upgrade=dist"
   ```

3. **Restore from Backup**

   ```bash
   # Restore application files
   tar -xzf /backups/skyyrose-app-YYYYMMDD.tar.gz -C /opt/skyyrose/

   # Restore database
   pg_restore -d skyyrose /backups/database-YYYYMMDD.dump

   # Verify restoration
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
   # Compare with expected count

   # Restore S3 data
   aws s3 sync s3://skyyrose-backups/YYYYMMDD/ s3://skyyrose-production/
   ```

4. **Verify System Integrity**

   ```bash
   # Check for malware in restored systems
   clamscan -r /opt/skyyrose/

   # Verify file checksums
   sha256sum -c /backups/checksums.txt

   # Check for backdoors
   rkhunter --check --skip-keypress
   ```

**Option 2: Decryption (if tool available)**

1. **Search for Decryption Tools**

   ```bash
   # Check NoMoreRansom project
   # Visit: https://www.nomoreransom.org/

   # Check vendor decryption tools
   # Kaspersky, Avast, Emsisoft offer free decryptors

   # Download appropriate decryptor
   wget https://trusted-source.com/decryptor-tool
   ```

2. **Test Decryption**

   ```bash
   # Test on non-critical files first
   ./decryptor --test /path/to/encrypted/test.file

   # If successful, proceed with full decryption
   ./decryptor --all /infected/directory/
   ```

**Option 3: Pay Ransom (LAST RESORT - requires approvals)**

Only consider if:

- No backups available
- Critical business data unrecoverable
- Data exfiltration threatens public disclosure
- CEO, Legal, and Insurance all approve
- Law enforcement notified

**We do NOT recommend paying as it:**

- Funds criminal operations
- Provides no guarantee of decryption
- May target you again
- Violates sanctions in some cases

### Eradication

1. **Remove Ransomware**

   ```bash
   # Scan and remove malware
   clamscan -r --remove /

   # Remove persistence mechanisms
   crontab -r  # Remove malicious cron jobs
   rm -rf /etc/systemd/system/<malicious-service>
   systemctl daemon-reload

   # Remove malicious users
   userdel <malicious-user>
   ```

2. **Patch Vulnerabilities**

   ```bash
   # Update all packages
   apt update && apt upgrade -y

   # Patch specific vulnerabilities
   apt install --only-upgrade <vulnerable-package>

   # Disable RDP if not needed
   systemctl disable rdp
   ```

3. **Change All Credentials**

   ```bash
   # Force password reset for all users
   psql $DATABASE_URL -c "UPDATE users SET password_reset_required = true;"

   # Rotate all API keys
   python scripts/rotate_all_api_keys.py

   # Regenerate SSH keys
   ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N ""

   # Rotate database passwords
   psql $DATABASE_URL -c "ALTER USER skyyrose_api PASSWORD '$(openssl rand -base64 32)';"
   ```

## Recovery

### Service Restoration

**Phase 1: Containment Verified (0-4 hours)**

- [ ] All infected systems isolated
- [ ] Ransomware processes killed
- [ ] Backups protected and verified
- [ ] Forensic evidence preserved
- [ ] Executive team briefed

**Phase 2: Recovery Planning (4-12 hours)**

- [ ] Backup restoration tested
- [ ] Clean infrastructure provisioned
- [ ] Recovery timeline established
- [ ] Stakeholders notified

**Phase 3: Restoration (12-48 hours)**

- [ ] Systems restored from backup
- [ ] Data integrity verified
- [ ] Security hardening applied
- [ ] Credentials rotated
- [ ] Services gradually restored

**Phase 4: Monitoring (48-72 hours)**

- [ ] Enhanced monitoring active
- [ ] No reinfection detected
- [ ] All services operational
- [ ] User access restored

### Communication Plan

**Internal - Immediate:**

```
@channel @everyone

:rotating_light::rotating_light: **RANSOMWARE ATTACK - CODE RED** :rotating_light::rotating_light:

**DO NOT use company systems until further notice**

**IMMEDIATE ACTIONS**:
1. Disconnect from network NOW
2. Do NOT power off your computer
3. Do NOT open any files or emails
4. Report any suspicious activity to @security-lead

**Status**: Multiple systems infected, disaster recovery in progress

**War Room**: #incident-ransomware-YYYYMMDD
**Emergency Hotline**: [PHONE]

**Next Update**: Every hour on the hour

**Incident Commander**: @security-lead
**DO NOT discuss publicly**
```

**Customer Communication:**

```
Subject: Important Service Update

Dear Customer,

We are currently experiencing a service disruption due to a cybersecurity incident. We have taken immediate action to contain the issue and protect your data.

CURRENT STATUS:
Our services are temporarily unavailable while we restore systems from secure backups.

WHAT WE'RE DOING:
- Systems isolated and contained
- Disaster recovery procedures activated
- Working with cybersecurity experts
- Law enforcement notified

YOUR DATA:
We are investigating but have no evidence customer data was accessed or compromised. We maintain secure, encrypted backups.

ESTIMATED RESTORATION:
We expect to restore services within [TIMEFRAME]. We will provide updates every [FREQUENCY].

Status Page: https://status.skyyrose.com
Support: support@skyyrose.com

We sincerely apologize for this disruption and are working around the clock to restore full service.

Best regards,
SkyyRose Team
```

**Law Enforcement:**

- File IC3 complaint: <https://www.ic3.gov/>
- Contact FBI local field office
- Provide forensic evidence
- Coordinate with investigation

## Post-Mortem

### Key Metrics

- Detection time: [X minutes from initial infection]
- Containment time: [X hours]
- Recovery time: [X hours]
- Systems affected: [X]
- Data encrypted: [X GB]
- Data lost: [X GB]
- Downtime: [X hours]
- Financial impact: $[X]
- Ransom demanded: $[X]
- Ransom paid: $[X] (hopefully $0)

### Preventive Measures

**CRITICAL - Implement IMMEDIATELY:**

- [ ] 3-2-1 backup strategy (3 copies, 2 media types, 1 offsite)
- [ ] Immutable backups (cannot be deleted/encrypted)
- [ ] Offline/air-gapped backup copies
- [ ] Regular backup testing and drills
- [ ] Endpoint Detection and Response (EDR) on all systems
- [ ] Network segmentation
- [ ] Disable RDP or use VPN
- [ ] Multi-factor authentication everywhere
- [ ] Email security gateway (anti-phishing)
- [ ] Application whitelisting

**Short-term (30 days):**

- [ ] Security awareness training (phishing simulations)
- [ ] Vulnerability patching SLA (24-48 hours)
- [ ] Privileged access management (PAM)
- [ ] Security information and event management (SIEM)
- [ ] Incident response retainer with professional firm
- [ ] Cyber insurance review and update

**Long-term (90 days):**

- [ ] Zero-trust architecture implementation
- [ ] Regular penetration testing
- [ ] Red team exercises
- [ ] Security operations center (SOC)
- [ ] Disaster recovery drills (quarterly)
- [ ] Supply chain security assessment

## Contact Information

### Emergency Contacts

| Role | Name | Phone (24/7) | Email |
|------|------|--------------|-------|
| Security Lead | [NAME] | [PHONE] | <security-lead@skyyrose.com> |
| CTO | [NAME] | [PHONE] | <cto@skyyrose.com> |
| CEO | [NAME] | [PHONE] | <ceo@skyyrose.com> |
| Legal Counsel | [NAME] | [PHONE] | <legal@skyyrose.com> |

### External Resources

| Organization | Purpose | Contact |
|--------------|---------|---------|
| FBI Cyber Division | Report ransomware | IC3.gov, [Local field office] |
| Cyber Insurance | File claim | [Policy number], [Phone] |
| Incident Response Firm | Professional help | [Retainer contact] |
| NoMoreRansom | Free decryptors | <https://www.nomoreransom.org> |

## Slack Notification Template

```
:rotating_light::rotating_light::rotating_light: **RANSOMWARE ATTACK DETECTED** :rotating_light::rotating_light::rotating_light:

@channel @security-team @executive-team

**THIS IS NOT A DRILL**

**Incident ID**: INC-RANSOM-YYYYMMDD-HHmm
**Severity**: CRITICAL - CODE RED
**Status**: ACTIVE INCIDENT

**Ransomware Details**:
- Variant: [Identified/Unknown]
- Affected Systems: [X servers]
- Files Encrypted: [Estimated count]
- Ransom Demanded: $[AMOUNT] in Bitcoin

**IMMEDIATE ACTIONS TAKEN**:
- Infected systems ISOLATED (do NOT power off)
- Network segmentation activated
- Backups PROTECTED
- Law enforcement notified
- Disaster recovery initiated

**ALL EMPLOYEES**:
1. DISCONNECT from network immediately
2. DO NOT power off computers
3. DO NOT open any files/emails
4. Report to war room: #incident-ransomware-YYYYMMDD

**WAR ROOM**: #incident-ransomware-YYYYMMDD
**EMERGENCY BRIDGE**: [Conference call link]
**HOTLINE**: [Phone number]

**CRITICAL**: Do NOT discuss publicly. All media to PR@skyyrose.com.

**Incident Commander**: @security-lead
**Technical Lead**: @cto

**Next briefing**: [TIME] (every hour)

**Status**: Backups INTACT - Recovery in progress
```

## Related Runbooks

- [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)
- [Data Breach](/Users/coreyfoster/DevSkyy/docs/runbooks/data-breach.md)
- [Zero-Day Vulnerability](/Users/coreyfoster/DevSkyy/docs/runbooks/zero-day-vulnerability.md)

## Appendix: Ransomware Response Decision Tree

```
Ransomware Detected
    ├─> ISOLATE systems (DO NOT power off)
    ├─> PROTECT backups
    ├─> PRESERVE evidence
    └─> Assess backups
        ├─> Backups INTACT
        │   └─> RESTORE from backups (PREFERRED)
        └─> Backups ENCRYPTED/DELETED
            ├─> Check for decryptor
            │   ├─> Decryptor available → DECRYPT
            │   └─> No decryptor → Consider ransom (LAST RESORT)
            └─> Consult Legal, Insurance, Law Enforcement
```

## Important Reminder

**NEVER pay ransom without:**

1. CEO approval
2. Legal counsel approval
3. Cyber insurance consultation
4. Law enforcement notification
5. Exhausting all recovery options

**Paying ransom:**

- Funds criminal organizations
- No guarantee of decryption
- May violate sanctions laws
- Makes you a repeat target
- Encourages future attacks
