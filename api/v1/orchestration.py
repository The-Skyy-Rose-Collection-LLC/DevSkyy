#!/usr/bin/env python3
"""
DevSkyy Multi-AI Orchestration API Endpoints
Production-ready REST API for orchestration system management

Author: DevSkyy Team
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import sys
import os

# Add orchestration module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'ai_orchestration'))

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Initialize router
router = APIRouter()

# Pydantic models for request/response validation
class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system health status")
    partnerships: Dict[str, Dict[str, Any]] = Field(..., description="Partnership health details")
    last_updated: datetime = Field(..., description="Last health check timestamp")

class MetricsResponse(BaseModel):
    partnership_type: str = Field(..., description="Partnership type")
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    timestamp: datetime = Field(..., description="Metrics collection timestamp")

class DecisionRequest(BaseModel):
    context: Dict[str, Any] = Field(..., description="Decision context parameters")

class DecisionResponse(BaseModel):
    decision: str = Field(..., description="Strategic decision")
    rationale: str = Field(..., description="Decision rationale")
    implementation_plan: List[Dict[str, Any]] = Field(..., description="Implementation phases")
    success_metrics: List[str] = Field(..., description="Success criteria")
    risk_mitigation: List[str] = Field(..., description="Risk mitigation strategies")

class PartnershipStatus(BaseModel):
    id: str = Field(..., description="Partnership identifier")
    name: str = Field(..., description="Partnership name")
    health: str = Field(..., description="Partnership health status")
    progress: float = Field(..., description="Overall progress percentage")
    deliverables: List[Dict[str, Any]] = Field(..., description="Deliverable status")

class DeliverableUpdate(BaseModel):
    completion_percentage: float = Field(..., ge=0, le=100, description="Completion percentage")
    status: str = Field(..., description="Current status description")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")

# Dependency for authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user info"""
    try:
        # In production, validate JWT token here
        # For now, return a mock user
        return {"user_id": "orchestration_admin", "role": "admin"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Initialize orchestration system
async def get_orchestration_system():
    """Get orchestration system instance"""
    try:
        from claude_central_command import ClaudeCentralCommand
        return ClaudeCentralCommand()
    except ImportError as e:
        logger.error(f"Failed to import orchestration system: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestration system not available"
        )

# Health and Status Endpoints
@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_orchestration_health(
    current_user: dict = Depends(get_current_user)
) -> HealthResponse:
    """Get overall orchestration system health status"""
    
    try:
        central_command = await get_orchestration_system()
        
        # Collect health data from all partnerships
        partnerships_health = {}
        
        try:
            from claude_central_command import PartnershipType
            
            for partnership_type in PartnershipType:
                metrics = await central_command._get_partnership_performance(partnership_type)
                
                # Determine health status based on metrics
                health_score = 0
                metric_count = 0
                
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        if "uptime" in key.lower():
                            health_score += min(value, 100)
                        elif "response_time" in key.lower():
                            health_score += max(0, 100 - value/10)  # Lower is better
                        elif "score" in key.lower() or "rate" in key.lower():
                            health_score += min(value, 100)
                        else:
                            health_score += min(value, 100)
                        metric_count += 1
                
                avg_health = health_score / max(metric_count, 1)
                
                if avg_health >= 90:
                    health_status = "excellent"
                elif avg_health >= 75:
                    health_status = "good"
                elif avg_health >= 60:
                    health_status = "fair"
                else:
                    health_status = "poor"
                
                partnerships_health[partnership_type.value] = {
                    "health": health_status,
                    "score": round(avg_health, 1),
                    **{k: v for k, v in metrics.items() if isinstance(v, (int, float))}
                }
        
        except Exception as e:
            logger.warning(f"Error collecting partnership health: {e}")
            partnerships_health = {"error": "Unable to collect partnership health"}
        
        # Determine overall system status
        if partnerships_health and "error" not in partnerships_health:
            health_scores = [p.get("score", 0) for p in partnerships_health.values()]
            avg_system_health = sum(health_scores) / len(health_scores)
            
            if avg_system_health >= 85:
                overall_status = "healthy"
            elif avg_system_health >= 70:
                overall_status = "degraded"
            else:
                overall_status = "critical"
        else:
            overall_status = "unknown"
        
        return HealthResponse(
            status=overall_status,
            partnerships=partnerships_health,
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/metrics", response_model=List[MetricsResponse], tags=["Metrics"])
async def get_all_metrics(
    current_user: dict = Depends(get_current_user)
) -> List[MetricsResponse]:
    """Get real-time metrics from all partnerships"""
    
    try:
        central_command = await get_orchestration_system()
        from claude_central_command import PartnershipType
        
        all_metrics = []
        timestamp = datetime.now()
        
        for partnership_type in PartnershipType:
            try:
                metrics = await central_command._get_partnership_performance(partnership_type)
                
                all_metrics.append(MetricsResponse(
                    partnership_type=partnership_type.value,
                    metrics=metrics,
                    timestamp=timestamp
                ))
                
            except Exception as e:
                logger.warning(f"Failed to get metrics for {partnership_type}: {e}")
                all_metrics.append(MetricsResponse(
                    partnership_type=partnership_type.value,
                    metrics={"error": f"Metrics unavailable: {str(e)}"},
                    timestamp=timestamp
                ))
        
        return all_metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics collection failed: {str(e)}"
        )

@router.get("/metrics/{partnership_type}", response_model=MetricsResponse, tags=["Metrics"])
async def get_partnership_metrics(
    partnership_type: str,
    current_user: dict = Depends(get_current_user)
) -> MetricsResponse:
    """Get real-time metrics for specific partnership"""
    
    try:
        central_command = await get_orchestration_system()
        from claude_central_command import PartnershipType
        
        # Validate partnership type
        valid_types = [pt.value for pt in PartnershipType]
        if partnership_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid partnership type. Valid types: {valid_types}"
            )
        
        # Find the enum value
        partnership_enum = None
        for pt in PartnershipType:
            if pt.value == partnership_type:
                partnership_enum = pt
                break
        
        if not partnership_enum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Partnership type not found: {partnership_type}"
            )
        
        metrics = await central_command._get_partnership_performance(partnership_enum)
        
        return MetricsResponse(
            partnership_type=partnership_type,
            metrics=metrics,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Partnership metrics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Partnership metrics failed: {str(e)}"
        )

# Strategic Decision Engine
@router.post("/decisions", response_model=DecisionResponse, tags=["Strategy"])
async def make_strategic_decision(
    request: DecisionRequest,
    current_user: dict = Depends(get_current_user)
) -> DecisionResponse:
    """Submit decision context and get strategic recommendations"""
    
    try:
        central_command = await get_orchestration_system()
        
        # Validate decision context
        if not request.context:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decision context is required"
            )
        
        # Make strategic decision
        decision_result = await central_command.strategic_decision_engine(request.context)
        
        return DecisionResponse(
            decision=decision_result.get("decision", "UNKNOWN"),
            rationale=decision_result.get("rationale", "No rationale provided"),
            implementation_plan=decision_result.get("implementation_plan", []),
            success_metrics=decision_result.get("success_metrics", []),
            risk_mitigation=decision_result.get("risk_mitigation", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Strategic decision failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategic decision failed: {str(e)}"
        )

# Partnership Management
@router.get("/partnerships", response_model=List[PartnershipStatus], tags=["Partnerships"])
async def get_all_partnerships(
    current_user: dict = Depends(get_current_user)
) -> List[PartnershipStatus]:
    """Get status of all partnerships"""
    
    try:
        central_command = await get_orchestration_system()
        from claude_central_command import PartnershipType
        
        partnerships = []
        
        for partnership_type in PartnershipType:
            try:
                # Get partnership configuration
                partnership_config = central_command.partnerships.get(partnership_type, {})
                
                # Get deliverable progress
                deliverables_progress = await central_command._check_deliverable_progress(partnership_type)
                
                # Calculate overall progress
                if deliverables_progress:
                    progress_values = [v for v in deliverables_progress.values() if isinstance(v, (int, float))]
                    overall_progress = sum(progress_values) / len(progress_values) if progress_values else 0
                else:
                    overall_progress = 0
                
                # Format deliverables
                deliverables = [
                    {"name": name, "progress": progress}
                    for name, progress in deliverables_progress.items()
                ]
                
                # Determine health status
                if overall_progress >= 85:
                    health = "excellent"
                elif overall_progress >= 70:
                    health = "good"
                elif overall_progress >= 50:
                    health = "fair"
                else:
                    health = "poor"
                
                partnerships.append(PartnershipStatus(
                    id=partnership_type.value,
                    name=partnership_config.get("name", f"{partnership_type.value} Partnership"),
                    health=health,
                    progress=round(overall_progress, 1),
                    deliverables=deliverables
                ))
                
            except Exception as e:
                logger.warning(f"Failed to get status for {partnership_type}: {e}")
                partnerships.append(PartnershipStatus(
                    id=partnership_type.value,
                    name=f"{partnership_type.value} Partnership",
                    health="unknown",
                    progress=0.0,
                    deliverables=[{"name": "error", "progress": 0, "error": str(e)}]
                ))
        
        return partnerships
        
    except Exception as e:
        logger.error(f"Partnership status failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Partnership status failed: {str(e)}"
        )

@router.get("/partnerships/{partnership_id}/status", response_model=PartnershipStatus, tags=["Partnerships"])
async def get_partnership_status(
    partnership_id: str,
    current_user: dict = Depends(get_current_user)
) -> PartnershipStatus:
    """Get status of specific partnership"""
    
    try:
        # Get all partnerships and filter for the requested one
        all_partnerships = await get_all_partnerships(current_user)
        
        for partnership in all_partnerships:
            if partnership.id == partnership_id:
                return partnership
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partnership not found: {partnership_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Partnership status failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Partnership status failed: {str(e)}"
        )

# System Information
@router.get("/info", tags=["System"])
async def get_system_info(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get orchestration system information"""
    
    try:
        return {
            "system": "DevSkyy Multi-AI Orchestration System",
            "version": "1.0.0",
            "status": "operational",
            "partnerships": 4,
            "features": [
                "Real-time metrics collection",
                "Strategic decision engine",
                "Partnership coordination",
                "Performance monitoring",
                "ROI optimization"
            ],
            "api_version": "v1",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System info failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System info failed: {str(e)}"
        )
