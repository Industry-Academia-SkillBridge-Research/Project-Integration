"""
SkillScope Config Server
Serves dynamic service port configuration to frontend
Allows changing ports without rebuilding the frontend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SkillScope Config Server")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ServiceConfig(BaseModel):
    """Service configuration"""
    AUTH_API: str
    AGENT_API: str
    SKILL_API: str
    INTERVIEW_API: str
    RECOMMENDATION_API: str


# Service port configuration - Single source of truth
SERVICES_CONFIG = ServiceConfig(
    AUTH_API="http://localhost:8182",
    AGENT_API="http://localhost:8003",
    SKILL_API="http://localhost:8000",
    INTERVIEW_API="http://localhost:8188",
    RECOMMENDATION_API="http://localhost:8001",
)


@app.get("/config", response_model=ServiceConfig)
async def get_config():
    """
    Get all service URLs
    Frontend fetches this once on startup to get all service endpoints
    """
    return SERVICES_CONFIG


@app.get("/config/{service_name}")
async def get_service_config(service_name: str):
    """
    Get specific service URL
    
    Args:
        service_name: One of 'auth', 'agent', 'skill', 'interview', 'recommendation'
    """
    service_mapping = {
        "auth": SERVICES_CONFIG.AUTH_API,
        "agent": SERVICES_CONFIG.AGENT_API,
        "skill": SERVICES_CONFIG.SKILL_API,
        "interview": SERVICES_CONFIG.INTERVIEW_API,
        "recommendation": SERVICES_CONFIG.RECOMMENDATION_API,
    }
    
    if service_name.lower() not in service_mapping:
        return {
            "error": f"Unknown service: {service_name}",
            "available": list(service_mapping.keys())
        }
    
    return {
        "service": service_name,
        "url": service_mapping[service_name.lower()]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "config-server",
        "version": "1.0.0"
    }
