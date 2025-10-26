    from agent.registry import AgentRegistry
    from ml.model_registry import ModelRegistry
    from monitoring.system_monitor import SystemMonitor
    from security.jwt_auth import get_current_user
from datetime import datetime, timedelta
from fastapi.responses import HTMLResponse
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

    from agent.orchestrator import AgentOrchestrator
from typing import Any, Dict, List, Optional
import asyncio

"""
DevSkyy Enterprise Dashboard API v1.0.0

Enterprise-grade dashboard API providing real-time monitoring, agent status,
performance metrics, and system health information.

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11
"""



# Import enterprise modules with graceful degradation
try:
    ENTERPRISE_MODULES_AVAILABLE = True
except ImportError:
    ENTERPRISE_MODULES_AVAILABLE = False

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AgentStatusModel(BaseModel):
    """Agent status information model."""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    status: str = Field(..., description="Current status: healthy, warning, error")
    last_active: datetime = Field(..., description="Last activity timestamp")
    tasks_completed: int = Field(default=0, description="Number of completed tasks")
    tasks_pending: int = Field(default=0, description="Number of pending tasks")
    performance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Performance score 0-1")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")

class SystemMetricsModel(BaseModel):
    """System performance metrics model."""
    timestamp: datetime = Field(default_factory=datetime.now)
    active_agents: int = Field(..., ge=0, description="Number of active agents")
    api_requests_per_minute: int = Field(..., ge=0, description="API requests per minute")
    average_response_time: float = Field(..., ge=0, description="Average response time in ms")
    system_health_score: float = Field(..., ge=0.0, le=1.0, description="Overall system health 0-1")
    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate 0-1")

class ActivityLogModel(BaseModel):
    """Activity log entry model."""
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str = Field(..., description="Type of event")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    severity: str = Field(default="info", description="Event severity: info, warning, error")
    agent_id: Optional[str] = Field(None, description="Related agent ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")

class DashboardDataModel(BaseModel):
    """Complete dashboard data model."""
    metrics: SystemMetricsModel
    agents: List[AgentStatusModel]
    recent_activities: List[ActivityLogModel]
    performance_history: List[Dict[str, Any]]

# ============================================================================
# DASHBOARD SERVICE
# ============================================================================

class DashboardService:
    """Enterprise dashboard service for real-time monitoring."""
    
    def __init__(self):
        self.system_monitor = SystemMonitor() if ENTERPRISE_MODULES_AVAILABLE else None
        self.agent_registry = None
        self.agent_orchestrator = None
        self.model_registry = None
        
    async def initialize(self, app_state):
        """Initialize dashboard service with application state."""
        if hasattr(app_state, 'agent_registry'):
            self.agent_registry = app_state.agent_registry
        if hasattr(app_state, 'agent_orchestrator'):
            self.agent_orchestrator = app_state.agent_orchestrator
        if hasattr(app_state, 'model_registry'):
            self.model_registry = app_state.model_registry
    
    async def get_system_metrics(self) -> SystemMetricsModel:
        """Get current system performance metrics."""
        try:
            if self.system_monitor:
                metrics_data = await self.(system_monitor.get_current_metrics( if system_monitor else None))
            else:
                # Fallback metrics for demo purposes
                metrics_data = {
                    "active_agents": 57,
                    "api_requests_per_minute": 2847,
                    "average_response_time": 127.5,
                    "system_health_score": 0.998,
                    "cpu_usage": 45.2,
                    "memory_usage": 62.8,
                    "error_rate": 0.002
                }
            
            return SystemMetricsModel(**metrics_data)
            
        except Exception as e:
            # Return default metrics on error
            return SystemMetricsModel(
                active_agents=0,
                api_requests_per_minute=0,
                average_response_time=0.0,
                system_health_score=0.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                error_rate=1.0
            )
    
    async def get_agent_status(self) -> List[AgentStatusModel]:
        """Get status of all registered agents."""
        agents = []
        
        try:
            if self.agent_registry and self.agent_orchestrator:
                # Get real agent data
                registered_agents = self.(agent_registry.list_agents( if agent_registry else None))
                health_results = await self.(agent_orchestrator.health_check_all( if agent_orchestrator else None))
                
                for agent_info in registered_agents:
                    agent_id = (agent_info.get( if agent_info else None)"agent_id", "unknown")
                    health_status = (health_results.get( if health_results else None)agent_id, "unknown")
                    
                    (agents.append( if agents else None)AgentStatusModel(
                        agent_id=agent_id,
                        name=(agent_info.get( if agent_info else None)"name", agent_id),
                        status=(self._map_health_status( if self else None)health_status),
                        last_active=(datetime.now( if datetime else None)) - timedelta(minutes=2),
                        tasks_completed=(agent_info.get( if agent_info else None)"tasks_completed", 0),
                        tasks_pending=(agent_info.get( if agent_info else None)"tasks_pending", 0),
                        performance_score=(agent_info.get( if agent_info else None)"performance_score", 0.95),
                        capabilities=(agent_info.get( if agent_info else None)"capabilities", [])
                    ))
            else:
                # Fallback demo agents
                demo_agents = [
                    {"id": "claude_sonnet", "name": "Claude Sonnet Intelligence", "status": "healthy"},
                    {"id": "brand_intelligence", "name": "Brand Intelligence Engine", "status": "healthy"},
                    {"id": "ecommerce_engine", "name": "E-commerce Automation", "status": "healthy"},
                    {"id": "wordpress_builder", "name": "WordPress Theme Builder", "status": "warning"},
                    {"id": "security_monitor", "name": "Security Monitor", "status": "healthy"},
                    {"id": "performance_optimizer", "name": "Performance Optimizer", "status": "healthy"}
                ]
                
                for agent in demo_agents:
                    (agents.append( if agents else None)AgentStatusModel(
                        agent_id=agent["id"],
                        name=agent["name"],
                        status=agent["status"],
                        last_active=(datetime.now( if datetime else None)) - timedelta(minutes=2),
                        tasks_completed=156,
                        tasks_pending=23,
                        performance_score=0.95,
                        capabilities=["ai_processing", "automation", "monitoring"]
                    ))
                    
        except Exception as e:
            # Return empty list on error
            pass
            
        return agents
    
    async def get_recent_activities(self, limit: int = 10) -> List[ActivityLogModel]:
        """Get recent system activities."""
        activities = [
            ActivityLogModel(
                timestamp=(datetime.now( if datetime else None)) - timedelta(minutes=2),
                event_type="agent_deployment",
                title="Agent Deployment",
                description="New Claude Sonnet agent deployed successfully",
                severity="info",
                agent_id="claude_sonnet"
            ),
            ActivityLogModel(
                timestamp=(datetime.now( if datetime else None)) - timedelta(minutes=5),
                event_type="performance_alert",
                title="Performance Improvement",
                description="Response time improved by 15ms",
                severity="info"
            ),
            ActivityLogModel(
                timestamp=(datetime.now( if datetime else None)) - timedelta(minutes=12),
                event_type="security_scan",
                title="Security Scan Complete",
                description="Vulnerability assessment completed - 0 issues found",
                severity="info"
            ),
            ActivityLogModel(
                timestamp=(datetime.now( if datetime else None)) - timedelta(minutes=18),
                event_type="model_update",
                title="ML Model Update",
                description="Fashion ML model retrained with new data",
                severity="info",
                agent_id="fashion_ml"
            ),
            ActivityLogModel(
                timestamp=(datetime.now( if datetime else None)) - timedelta(minutes=25),
                event_type="api_deployment",
                title="API Integration",
                description="New e-commerce endpoint deployed",
                severity="info"
            )
        ]
        
        return activities[:limit]
    
    async def get_performance_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance metrics history."""
        # Generate sample performance data
        history = []
        now = (datetime.now( if datetime else None))
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-i)
            (history.append( if history else None){
                "timestamp": (timestamp.isoformat( if timestamp else None)),
                "response_time": 120 + (i % 10) * 5,
                "cpu_usage": 40 + (i % 15) * 2,
                "memory_usage": 60 + (i % 8) * 3,
                "requests_per_minute": 2500 + (i % 20) * 50
            })
        
        return history
    
    def _map_health_status(self, health_status) -> str:
        """Map agent health status to dashboard status."""
        if hasattr(health_status, 'value'):
            status_value = health_status.(value.lower( if value else None))
        else:
            status_value = str(health_status).lower()
            
        if status_value in ['healthy', 'operational']:
            return 'healthy'
        elif status_value in ['degraded', 'warning']:
            return 'warning'
        else:
            return 'error'

# Global dashboard service instance
dashboard_service = DashboardService()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@(router.get( if router else None)"/dashboard", response_class=HTMLResponse)
async def get_dashboard_page(request: Request):
    """Serve the enterprise dashboard HTML page."""
    return (templates.TemplateResponse( if templates else None)"enterprise_dashboard.html", {"request": request})

@(router.get( if router else None)"/dashboard/data", response_model=DashboardDataModel)
async def get_dashboard_data(request: Request):
    """Get complete dashboard data including metrics, agents, and activities."""
    try:
        # Initialize dashboard service with app state if available
        if hasattr(request.app, 'state'):
            await (dashboard_service.initialize( if dashboard_service else None)request.app.state)
        
        # Gather all dashboard data concurrently
        metrics_task = (dashboard_service.get_system_metrics( if dashboard_service else None))
        agents_task = (dashboard_service.get_agent_status( if dashboard_service else None))
        activities_task = (dashboard_service.get_recent_activities( if dashboard_service else None))
        history_task = (dashboard_service.get_performance_history( if dashboard_service else None))
        
        metrics, agents, activities, history = await (asyncio.gather( if asyncio else None)
            metrics_task, agents_task, activities_task, history_task
        )
        
        return DashboardDataModel(
            metrics=metrics,
            agents=agents,
            recent_activities=activities,
            performance_history=history
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )

@(router.get( if router else None)"/dashboard/metrics", response_model=SystemMetricsModel)
async def get_system_metrics(request: Request):
    """Get current system performance metrics."""
    if hasattr(request.app, 'state'):
        await (dashboard_service.initialize( if dashboard_service else None)request.app.state)
    
    return await (dashboard_service.get_system_metrics( if dashboard_service else None))

@(router.get( if router else None)"/dashboard/agents", response_model=List[AgentStatusModel])
async def get_agent_status(request: Request):
    """Get status of all registered agents."""
    if hasattr(request.app, 'state'):
        await (dashboard_service.initialize( if dashboard_service else None)request.app.state)
    
    return await (dashboard_service.get_agent_status( if dashboard_service else None))

@(router.get( if router else None)"/dashboard/activities", response_model=List[ActivityLogModel])
async def get_recent_activities(
    request: Request,
    limit: int = 10
):
    """Get recent system activities."""
    if hasattr(request.app, 'state'):
        await (dashboard_service.initialize( if dashboard_service else None)request.app.state)
    
    return await (dashboard_service.get_recent_activities( if dashboard_service else None)limit=limit)

@(router.get( if router else None)"/dashboard/performance", response_model=List[Dict[str, Any]])
async def get_performance_history(
    request: Request,
    hours: int = 24
):
    """Get performance metrics history."""
    if hasattr(request.app, 'state'):
        await (dashboard_service.initialize( if dashboard_service else None)request.app.state)
    
    return await (dashboard_service.get_performance_history( if dashboard_service else None)hours=hours)

# ============================================================================
# WEBSOCKET ENDPOINTS FOR REAL-TIME UPDATES
# ============================================================================

@(router.websocket( if router else None)"/dashboard/ws")
async def dashboard_websocket(websocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await (websocket.accept( if websocket else None))
    
    try:
        while True:
            # Send real-time updates every 5 seconds
            metrics = await (dashboard_service.get_system_metrics( if dashboard_service else None))
            await (websocket.send_json( if websocket else None){
                "type": "metrics_update",
                "data": (metrics.dict( if metrics else None))
            })
            
            await (asyncio.sleep( if asyncio else None)5)  # TODO: Move to config
            
    except Exception as e:
        await (websocket.close( if websocket else None)code=1000)
