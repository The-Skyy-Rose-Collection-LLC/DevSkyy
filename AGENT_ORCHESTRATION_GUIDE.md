# Enterprise Agent Orchestration Guide

## Overview

DevSkyy now features an enterprise-grade multi-agent orchestration system with:
- **Agent Orchestrator**: Manages agent lifecycle, dependencies, and coordination
- **Security Manager**: Provides authentication, authorization, and audit logging
- **Agent Registry**: Automatic agent discovery and registration
- **BaseAgent V2**: Self-healing agents with ML-powered monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                      Agent Registry                          │
│  - Auto-discovery                                           │
│  - Registration                                             │
│  - Workflow management                                      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                   Agent Orchestrator                         │
│  - Dependency resolution                                    │
│  - Load balancing                                           │
│  - Circuit breaker                                          │
│  - Inter-agent communication                                │
└─────┬────────┬────────┬────────┬────────┬──────────────────┘
      │        │        │        │        │
┌─────▼──┐ ┌──▼─────┐ ┌▼──────┐ ┌▼─────┐ ┌▼────────┐
│Scanner │ │ Fixer  │ │Claude │ │E-com │ │Security │
│Agent   │ │ Agent  │ │Sonnet │ │Agent │ │ Agent   │
│V2      │ │ V2     │ │       │ │      │ │         │
└────────┘ └────────┘ └───────┘ └──────┘ └─────────┘
```

## Agent Orchestrator

### Key Features

1. **Dependency Resolution**: Automatically determines execution order based on agent dependencies
2. **Circuit Breaker Pattern**: Protects against cascading failures
3. **Load Balancing**: Distributes tasks across available agents
4. **Performance Tracking**: Monitors execution time and success rates
5. **Inter-Agent Communication**: Shared context for data passing

### Usage

```python
from agent.orchestrator import orchestrator, ExecutionPriority

# Execute a multi-agent task
result = await orchestrator.execute_task(
    task_type="scan_and_fix",
    parameters={"target_path": "./src"},
    required_capabilities=["scan", "fix"],
    priority=ExecutionPriority.HIGH
)
```

### Registering Agents

```python
await orchestrator.register_agent(
    agent=my_agent_instance,
    capabilities=["capability1", "capability2"],
    dependencies=["dependency_agent_name"],
    priority=ExecutionPriority.MEDIUM
)
```

## Security Manager

### Key Features

1. **API Key Management**: Generate, validate, and rotate agent API keys
2. **RBAC**: Role-based access control with fine-grained permissions
3. **Audit Logging**: Complete audit trail of all security events
4. **Rate Limiting**: Prevent abuse and DDoS attacks
5. **Threat Detection**: Automatic blocking of suspicious agents

### Usage

```python
from agent.security_manager import security_manager, SecurityRole

# Generate API key for an agent
api_key = security_manager.generate_api_key(
    agent_name="my_agent",
    role=SecurityRole.SERVICE
)

# Validate API key
key_info = security_manager.validate_api_key(api_key)

# Check permissions
has_access = security_manager.check_permission(
    agent_name="my_agent",
    resource="database",
    permission="write"
)

# Get audit log
audit_log = security_manager.get_audit_log(
    agent_name="my_agent",
    limit=100
)
```

### Security Roles

- **ADMIN**: Full access to all resources
- **OPERATOR**: Read/write/execute operations
- **ANALYST**: Read-only access
- **SERVICE**: Service-to-service communication
- **GUEST**: Limited access

## Agent Registry

### Key Features

1. **Auto-Discovery**: Automatically finds and registers agents
2. **Version Management**: Supports V2 agents with backward compatibility
3. **Hot Reloading**: Reload agents without restarting server
4. **Workflow Management**: Execute predefined multi-agent workflows

### Usage

```python
from agent.registry import registry

# Discover and register all agents
summary = await registry.discover_and_register_all_agents()

# Get an agent
scanner = registry.get_agent("scanner")

# List agents with specific capability
agents = registry.list_agents(capability="scan")

# Health check all agents
health = await registry.health_check_all()

# Execute workflow
result = await registry.execute_workflow(
    workflow_name="scan_and_fix",
    parameters={"target_path": "./src"}
)
```

### Predefined Workflows

1. **scan_and_fix**: Scan codebase → Apply fixes
2. **content_pipeline**: Generate content → SEO optimize → Publish
3. **ecommerce_order**: Validate → Check inventory → Process payment

## BaseAgent V2

### Key Features

1. **Self-Healing**: Automatic retry and error recovery
2. **Circuit Breaker**: Prevents cascading failures
3. **ML-Powered Monitoring**: Anomaly detection using statistical analysis
4. **Health Checks**: Comprehensive diagnostics
5. **Performance Tracking**: Response times and success rates

### Creating a V2 Agent

```python
from agent.modules.base_agent import BaseAgent

class MyAgentV2(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="My Agent", version="2.0.0")

    async def initialize(self) -> bool:
        """Initialize agent resources"""
        try:
            # Your initialization code
            self.status = BaseAgent.AgentStatus.HEALTHY
            return True
        except Exception as e:
            self.status = BaseAgent.AgentStatus.FAILED
            return False

    async def execute_core_function(self, **kwargs) -> Dict[str, Any]:
        """Core agent functionality"""
        # Your agent logic
        return {"result": "success"}

    @BaseAgent.with_healing
    async def my_method(self, data):
        """Method with automatic self-healing"""
        # Your code with automatic retry on failure
        pass
```

### Agent Status Levels

- **HEALTHY**: Operating normally
- **DEGRADED**: Reduced performance but functional
- **RECOVERING**: Self-healing in progress
- **FAILED**: Requires intervention
- **INITIALIZING**: Starting up

## API Endpoints

### Orchestrator Endpoints

```
GET  /api/agents/orchestrator/health
     → Get orchestrator health status

GET  /api/agents/orchestrator/metrics
     → Get performance metrics for all agents

GET  /api/agents/orchestrator/dependencies
     → Get agent dependency graph

POST /api/agents/orchestrator/execute
     → Execute a multi-agent task
     Body: {
       "task_type": "string",
       "parameters": {},
       "required_capabilities": ["string"],
       "priority": "high|medium|low"
     }
```

### Registry Endpoints

```
GET  /api/agents/registry/list
     → List all registered agents

GET  /api/agents/registry/info/{agent_name}
     → Get detailed agent information

POST /api/agents/registry/discover
     → Trigger agent discovery

GET  /api/agents/registry/health
     → Health check all agents

POST /api/agents/registry/workflow
     → Execute a workflow
     Body: {
       "workflow_name": "string",
       "parameters": {}
     }

POST /api/agents/registry/reload/{agent_name}
     → Hot reload an agent
```

### Security Endpoints

```
POST /api/security/api-key/generate
     → Generate new API key
     Body: {
       "agent_name": "string",
       "role": "admin|operator|service|analyst|guest"
     }

POST /api/security/api-key/validate
     → Validate API key
     Body: {
       "api_key": "string"
     }

DELETE /api/security/api-key/{key_id}
     → Revoke API key

GET  /api/security/audit-log
     → Get audit log
     Query: ?agent_name=string&event_type=string&limit=100

GET  /api/security/summary
     → Get security summary statistics

POST /api/security/check-permission
     → Check if agent has permission
     Body: {
       "agent_name": "string",
       "resource": "string",
       "permission": "read|write|execute|admin"
     }
```

### Agent-Specific Endpoints

```
POST /api/agents/scanner/scan
     → Execute scanner agent
     Body: {
       "scan_type": "full|security|performance|quick",
       "target_path": "./",
       "include_live_check": true
     }

POST /api/agents/fixer/fix
     → Execute fixer agent
     Body: {
       "fix_type": "auto|security|performance|format",
       "scan_results": {},
       "target_files": [],
       "dry_run": false
     }

GET  /api/agents/{agent_name}/health
     → Get agent health status

GET  /api/agents/{agent_name}/history
     → Get agent execution history
```

## Multi-Agent Dependencies

### Dependency Graph

```
Scanner
└─> Fixer (depends on Scanner for scan results)

Claude Sonnet
├─> SEO Agent (depends on Claude for content generation)
├─> Social Media Agent (depends on Claude for posts)
└─> Email Agent (depends on Claude for templates)

E-commerce Agent
├─> Inventory Agent (depends on product data)
├─> Financial Agent (depends on order data)
└─> SEO Agent (depends on product data)

Security Agent (no dependencies, runs first)
```

### Execution Order

The orchestrator automatically determines execution order:

1. **CRITICAL Priority**: Security, Authentication agents
2. **HIGH Priority**: Scanner, E-commerce, Financial agents
3. **MEDIUM Priority**: Content, SEO, AI agents
4. **LOW Priority**: Background, Learning agents

## Performance Optimization

### Circuit Breaker

Automatically opens after 5 consecutive failures, preventing cascading errors:

```python
# Circuit breaker is automatic in orchestrator
# Manually check status:
is_open = orchestrator._is_circuit_open(agent_name="my_agent")
```

### Caching

Agents can use shared context for caching:

```python
# Store data
orchestrator.share_data(key="cache_key", value=data, ttl=300)

# Retrieve data
cached_data = orchestrator.get_shared_data(key="cache_key")
```

### Rate Limiting

Automatic rate limiting in security manager:

```python
# Check rate limit (100 requests per 60 seconds)
allowed = security_manager.check_rate_limit(
    agent_name="my_agent",
    limit=100,
    window_seconds=60
)
```

## Monitoring & Observability

### Health Monitoring

```python
# Get orchestrator health
health = await orchestrator.get_orchestrator_health()

# Get agent metrics
metrics = orchestrator.get_agent_metrics(agent_name="scanner")

# Get execution history
history = orchestrator.execution_history
```

### Metrics Tracked

- Total calls
- Error count
- Average response time
- Success rate
- Circuit breaker status
- Anomalies detected

## Upgrading Existing Agents

### Step 1: Inherit from BaseAgent

```python
from agent.modules.base_agent import BaseAgent

class MyAgentV2(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="My Agent", version="2.0.0")
```

### Step 2: Implement Required Methods

```python
async def initialize(self) -> bool:
    # Initialize resources
    return True

async def execute_core_function(self, **kwargs) -> Dict[str, Any]:
    # Core logic
    return {}
```

### Step 3: Add Self-Healing

```python
@BaseAgent.with_healing
async def my_risky_operation(self):
    # Automatically retries on failure
    pass
```

### Step 4: Register with Orchestrator

The agent registry automatically discovers and registers V2 agents.

## Best Practices

1. **Use V2 Agents**: Always inherit from BaseAgent for new agents
2. **Define Dependencies**: Clearly specify agent dependencies
3. **Set Priorities**: Assign appropriate execution priority
4. **Monitor Health**: Regularly check agent health
5. **Review Audit Logs**: Monitor security events
6. **Use Workflows**: Leverage predefined workflows for common tasks
7. **Handle Errors**: Let BaseAgent's self-healing handle retries
8. **Share Data**: Use shared context for inter-agent communication

## Troubleshooting

### Agent Not Registering

Check:
1. Agent inherits from BaseAgent
2. File name ends with `_v2.py` or `_agent.py`
3. `initialize()` returns True
4. No import errors in agent file

### Circuit Breaker Open

```python
# Reset circuit breaker
orchestrator._reset_circuit_breaker(agent_name="my_agent")
```

### Security Access Denied

```python
# Grant resource access
security_manager.grant_resource_access(
    resource="database",
    agent_name="my_agent"
)
```

### Agent Health FAILED

```python
# Get detailed health info
agent = registry.get_agent("my_agent")
health = await agent.health_check()
print(health)

# Try to recover
await agent.initialize()
```

## Example: Complete Multi-Agent Workflow

```python
from agent.registry import registry
from agent.orchestrator import ExecutionPriority

# Initialize system
await registry.discover_and_register_all_agents()

# Execute scan and fix workflow
result = await registry.execute_workflow(
    workflow_name="scan_and_fix",
    parameters={
        "target_path": "./src",
        "fix_type": "auto",
        "create_backup": True
    }
)

# Check results
if result["status"] == "completed":
    print(f"Scan found {result['scan']['files_scanned']} files")
    print(f"Fixed {result['fix']['files_fixed']} files")
else:
    print(f"Errors: {result.get('errors')}")

# Monitor health
health = await registry.health_check_all()
print(f"{health['healthy_agents']}/{health['total_agents']} agents healthy")
```

## Next Steps

1. Review agent implementations in `agent/modules/backend/`
2. Run agent discovery: `POST /api/agents/registry/discover`
3. Check orchestrator health: `GET /api/agents/orchestrator/health`
4. Execute test workflow: `POST /api/agents/registry/workflow`
5. Monitor security events: `GET /api/security/audit-log`

## Support

For issues or questions:
- Check logs in `enterprise_run.log`
- Review agent health status
- Inspect audit logs for security events
- Contact DevSkyy development team
