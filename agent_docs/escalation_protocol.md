# Escalation Protocol

**Purpose**: Define when and how agents must escalate decisions to CEO/human approval.

---

## Escalation Framework

### Decision Authority Matrix
```
┌─────────────────────────────────────────────────────────────┐
│                     DECISION AUTHORITY                       │
├──────────────────┬──────────────────────────────────────────┤
│   Agent Auto     │  Price changes < 10%                     │
│   (Execute)      │  Inventory adjustments                   │
│                  │  Content updates (brand compliant)       │
│                  │  Order processing (standard)             │
├──────────────────┼──────────────────────────────────────────┤
│   Log & Notify   │  Price changes 10-20%                    │
│   (Execute +     │  Low inventory alerts                    │
│    Alert)        │  Customer complaints                     │
│                  │  Performance anomalies                   │
├──────────────────┼──────────────────────────────────────────┤
│   CEO Approval   │  Price changes > 20%                     │
│   Required       │  Customer refunds                        │
│   (STOP)         │  Inventory deletions                     │
│                  │  New product launches                    │
│                  │  Marketing campaigns                     │
│                  │  Vendor relationships                    │
│                  │  Financial commitments                   │
└──────────────────┴──────────────────────────────────────────┘
```

---

## Escalation Triggers

### Tier 1: Auto-Execute (No Escalation)
These actions can be performed autonomously:

| Category | Allowed Actions |
|----------|-----------------|
| Content | Update descriptions, fix typos, add images |
| Inventory | Stock count updates, reorder alerts |
| Orders | Process standard orders, update shipping |
| 3D | Generate models, apply try-on |
| Analytics | Generate reports, track metrics |

### Tier 2: Execute + Notify
Perform action but send notification:

| Trigger | Notification Method | Recipient |
|---------|---------------------|-----------|
| Price change 10-20% | Slack + Email | CEO |
| Inventory < 5 units | Slack | Operations |
| Customer complaint | Email | Customer Service Lead |
| API error rate > 1% | PagerDuty | DevOps |
| 3D processing failure | Slack | 3D Team |

### Tier 3: CEO Approval Required
**STOP and wait for explicit approval:**

| Trigger | Why Escalate | Approval Method |
|---------|--------------|-----------------|
| Price change > 20% | Revenue impact | Slack confirmation |
| Customer refund | Financial impact | Email approval |
| Inventory deletion | Data loss risk | Written confirmation |
| New product publish | Brand alignment | Review meeting |
| Marketing spend | Budget impact | Written approval |
| Vendor contract | Legal/financial | Signed approval |
| Security incident | Risk management | Immediate call |

---

## Escalation Process

### Step-by-Step Flow
```
┌────────────────────────────────────────────────────────────┐
│                    ESCALATION FLOW                          │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DETECT    Agent identifies escalation trigger           │
│       │                                                     │
│       ▼                                                     │
│  2. PAUSE     Agent stops current operation                 │
│       │                                                     │
│       ▼                                                     │
│  3. LOG       Record escalation in /logs/escalations.log   │
│       │                                                     │
│       ▼                                                     │
│  4. NOTIFY    Send escalation via appropriate channel       │
│       │                                                     │
│       ▼                                                     │
│  5. WAIT      Agent waits for response (with timeout)       │
│       │                                                     │
│       ▼                                                     │
│  6. RECEIVE   Get approval/denial/modification              │
│       │                                                     │
│       ▼                                                     │
│  7. EXECUTE   Proceed based on response                     │
│       │                                                     │
│       ▼                                                     │
│  8. CONFIRM   Log outcome and notify stakeholders           │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Escalation Request Format
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class EscalationType(Enum):
    PRICE_CHANGE = "price_change"
    REFUND = "refund"
    INVENTORY_DELETE = "inventory_delete"
    NEW_PRODUCT = "new_product"
    MARKETING = "marketing"
    VENDOR = "vendor"
    SECURITY = "security"
    OTHER = "other"

@dataclass
class EscalationRequest:
    id: str
    type: EscalationType
    agent_id: str
    timestamp: datetime
    summary: str
    details: dict
    impact: str
    recommendation: str
    urgency: str  # "immediate", "today", "this_week"
    timeout_hours: int
    status: str = "pending"  # pending, approved, denied, modified
    response: Optional[str] = None
    responded_at: Optional[datetime] = None
```

### Creating an Escalation
```python
async def create_escalation(
    escalation_type: EscalationType,
    agent_id: str,
    summary: str,
    details: dict,
    impact: str,
    recommendation: str,
    urgency: str = "today"
) -> EscalationRequest:
    """
    Create and send an escalation request.
    """

    timeout_map = {
        "immediate": 1,
        "today": 24,
        "this_week": 168
    }

    escalation = EscalationRequest(
        id=generate_escalation_id(),
        type=escalation_type,
        agent_id=agent_id,
        timestamp=datetime.utcnow(),
        summary=summary,
        details=details,
        impact=impact,
        recommendation=recommendation,
        urgency=urgency,
        timeout_hours=timeout_map[urgency]
    )

    # Log the escalation
    await log_escalation(escalation)

    # Send notification
    await send_escalation_notification(escalation)

    return escalation
```

---

## Notification Channels

### Channel Selection
| Urgency | Primary | Backup |
|---------|---------|--------|
| Immediate | Phone Call | SMS + Slack |
| Today | Slack | Email |
| This Week | Email | Slack |

### Notification Templates

#### Slack Message
```
🚨 *ESCALATION REQUIRED*

*Type:* Price Change > 20%
*Product:* SR-TOP-045 (Oakland Skyline Hoodie)
*Current Price:* $140.00
*Proposed Price:* $175.00
*Change:* +25%

*Impact:* Potential revenue increase of $35/unit
*Recommendation:* Approve - aligned with new collection launch

*Urgency:* Today
*Timeout:* 24 hours

React with ✅ to approve, ❌ to deny, or reply with modifications.
```

#### Email Template
```
Subject: [ESCALATION] Price Change Approval Required - SR-TOP-045

Dear CEO,

An agent requires your approval for the following action:

TYPE: Price Change > 20%
PRODUCT: SR-TOP-045 (Oakland Skyline Hoodie)
CURRENT: $140.00
PROPOSED: $175.00
CHANGE: +25%

IMPACT:
- Potential revenue increase of $35/unit
- Aligns with new collection positioning

RECOMMENDATION:
Approve - consistent with premium positioning for new collection launch.

URGENCY: Today (24-hour timeout)

Please reply with:
- APPROVED - to proceed as proposed
- DENIED - to cancel the change
- MODIFIED: [new price] - to proceed with a different price

If no response is received within 24 hours, the change will NOT proceed.

Best regards,
DevSkyy Orchestration System
```

---

## Response Handling

### Valid Responses
| Response | Action |
|----------|--------|
| `APPROVED` | Execute as proposed |
| `DENIED` | Cancel operation, log reason |
| `MODIFIED: [value]` | Execute with modification |
| `DEFER: [date]` | Reschedule for later |
| No response (timeout) | Do NOT execute |

### Processing Responses
```python
async def process_escalation_response(
    escalation_id: str,
    response: str,
    responder: str
) -> dict:
    """
    Process CEO/human response to escalation.
    """

    escalation = await get_escalation(escalation_id)

    if escalation.status != "pending":
        return {"error": "Escalation already resolved"}

    # Parse response
    response_upper = response.upper().strip()

    if response_upper == "APPROVED":
        escalation.status = "approved"
        action = "execute_as_proposed"

    elif response_upper == "DENIED":
        escalation.status = "denied"
        action = "cancel"

    elif response_upper.startswith("MODIFIED:"):
        escalation.status = "modified"
        modification = response_upper.replace("MODIFIED:", "").strip()
        action = f"execute_with_modification:{modification}"

    elif response_upper.startswith("DEFER:"):
        escalation.status = "deferred"
        defer_date = response_upper.replace("DEFER:", "").strip()
        action = f"reschedule:{defer_date}"

    else:
        return {"error": f"Invalid response format: {response}"}

    escalation.response = response
    escalation.responded_at = datetime.utcnow()

    # Update and log
    await update_escalation(escalation)
    await log_escalation_response(escalation, responder)

    # Notify agent
    await notify_agent(escalation.agent_id, "escalation_resolved", {
        "escalation_id": escalation_id,
        "action": action
    })

    return {
        "escalation_id": escalation_id,
        "status": escalation.status,
        "action": action
    }
```

---

## Timeout Handling

### Default Timeouts
| Urgency | Timeout | On Timeout |
|---------|---------|------------|
| Immediate | 1 hour | Do NOT execute, escalate to backup |
| Today | 24 hours | Do NOT execute, send reminder |
| This Week | 7 days | Do NOT execute, archive |

### Timeout Processing
```python
async def handle_escalation_timeout(escalation_id: str) -> None:
    """
    Handle escalation that has timed out without response.
    """

    escalation = await get_escalation(escalation_id)

    if escalation.status != "pending":
        return

    escalation.status = "timeout"
    escalation.response = "NO_RESPONSE_RECEIVED"
    escalation.responded_at = datetime.utcnow()

    await update_escalation(escalation)

    # Log timeout
    await log_escalation_timeout(escalation)

    # Notify agent - DO NOT EXECUTE
    await notify_agent(escalation.agent_id, "escalation_timeout", {
        "escalation_id": escalation_id,
        "action": "cancel"
    })

    # Send reminder to CEO if urgent
    if escalation.urgency == "immediate":
        await send_timeout_alert(escalation)
```

---

## Security Escalations

### Security incidents always escalate immediately:

```python
SECURITY_ESCALATION_TRIGGERS = [
    "unauthorized_access_attempt",
    "data_breach_suspected",
    "api_key_exposure",
    "unusual_activity_pattern",
    "failed_auth_spike",
    "malware_detected"
]

async def escalate_security_incident(
    incident_type: str,
    details: dict
) -> None:
    """
    Immediately escalate security incidents.
    """

    # Create urgent escalation
    escalation = await create_escalation(
        escalation_type=EscalationType.SECURITY,
        agent_id="security_monitor",
        summary=f"SECURITY: {incident_type}",
        details=details,
        impact="Potential security breach - immediate attention required",
        recommendation="Review and respond immediately",
        urgency="immediate"
    )

    # Multiple notification channels for security
    await send_sms(CEO_PHONE, f"SECURITY ALERT: {incident_type}")
    await send_slack_urgent(f"🚨 SECURITY: {incident_type}")
    await send_email_priority(CEO_EMAIL, escalation)

    # Automatic protective actions
    if incident_type in ["unauthorized_access_attempt", "api_key_exposure"]:
        await rotate_api_keys()
        await enable_enhanced_logging()
```

---

## Logging Requirements

All escalations must be logged:

```json
{
    "timestamp": "2025-12-02T10:30:00Z",
    "escalation_id": "esc_abc123",
    "type": "price_change",
    "agent_id": "catalog_agent",
    "summary": "Price change > 20% for SR-TOP-045",
    "details": {
        "product_sku": "SR-TOP-045",
        "current_price": 140.00,
        "proposed_price": 175.00,
        "change_percent": 25.0
    },
    "urgency": "today",
    "status": "pending",
    "created_at": "2025-12-02T10:30:00Z",
    "timeout_at": "2025-12-03T10:30:00Z"
}
```

Log location: `/logs/escalations.log`

---

## Audit Trail

All escalations are retained for 2 years:
- Original request
- All notifications sent
- Response received
- Action taken
- Outcome verification

---

**Last Updated**: 2025-12-02
**Owner**: Operations Team
**Review Cycle**: Quarterly
