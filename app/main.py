"""
Main FastAPI application for MCP-UI-Terminology Checker.
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from app.core.config import settings
from app.core.auth import verify_token
from app.core.terminology import TerminologyChecker

app = FastAPI(
    title="MCP-UI-Terminology Checker",
    description="Bilingual UI terminology auditing service (EN ⇄ JP) with LLM integration",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ContextRequest(BaseModel):
    text: str
    lang: str  # "en" or "jp"
    context: Optional[str] = None  # Additional context for LLM

class Issue(BaseModel):
    type: str  # "preferred_synonym", "forbidden_term", "consistency", "clarity"
    original: str
    suggestion: str
    reason: str  # LLM explanation
    start: int
    end: int
    severity: str = "warning"  # "error", "warning", "info"

class ContextResponse(BaseModel):
    issues: List[Issue]
    text: str
    lang: str
    llm_used: bool  # Whether LLM was used for analysis
    provider: Optional[str] = None  # "openai" or "anthropic"

# MCP Tool definitions
class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: dict

class MCPToolResponse(BaseModel):
    tools: List[MCPTool]

# Initialize terminology checker
terminology_checker = TerminologyChecker()

@app.get("/")
async def root():
    return {
        "message": "MCP-UI-Terminology Checker with LLM Integration", 
        "version": "2.0.0",
        "mcp_protocol": "Compatible",
        "llm_providers": ["openai", "anthropic"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "llm_available": bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)
    }

@app.post("/context-request", response_model=ContextResponse)
async def check_terminology(
    request: ContextRequest,
    authorization: str = Header(None)
):
    """
    Main endpoint for LLM-powered terminology checking.
    """
    # Verify token
    if not verify_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    # Validate language
    if request.lang not in ["en", "jp"]:
        raise HTTPException(status_code=400, detail="Language must be 'en' or 'jp'")
    
    # Check terminology with LLM
    issues = await terminology_checker.check_text(
        request.text, 
        request.lang, 
        request.context or ""
    )
    
    # Convert to response format
    formatted_issues = [
        Issue(
            type=issue["type"],
            original=issue["original"],
            suggestion=issue["suggestion"],
            reason=issue.get("reason", "Terminology improvement"),
            start=issue["start"],
            end=issue["end"],
            severity=issue["severity"]
        )
        for issue in issues
    ]
    
    return ContextResponse(
        issues=formatted_issues,
        text=request.text,
        lang=request.lang,
        llm_used=bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY),
        provider=settings.DEFAULT_LLM_PROVIDER if settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY else None
    )

@app.get("/mcp/tools", response_model=MCPToolResponse)
async def list_tools(authorization: str = Header(None)):
    """
    MCP-compatible tools endpoint - lists available terminology tools.
    """
    if not verify_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    return MCPToolResponse(
        tools=[
            MCPTool(
                name="check_ui_terminology",
                description="Analyze UI text for terminology consistency and suggest improvements using LLM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The UI text to analyze"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["en", "jp"],
                            "description": "Language of the text (en for English, jp for Japanese)"
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context about where this text appears (e.g., 'login button', 'error message')"
                        }
                    },
                    "required": ["text", "language"]
                }
            ),
            MCPTool(
                name="get_terminology_rules",
                description="Get the current terminology rules and preferences for a language",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string", 
                            "enum": ["en", "jp"],
                            "description": "Language to get rules for"
                        }
                    },
                    "required": ["language"]
                }
            )
        ]
    )

@app.post("/mcp/call")
async def call_tool(
    tool_name: str,
    arguments: dict,
    authorization: str = Header(None)
):
    """
    MCP-compatible tool execution endpoint.
    """
    if not verify_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    if tool_name == "check_ui_terminology":
        result = await terminology_checker.check_text(
            arguments["text"],
            arguments["language"], 
            arguments.get("context", "")
        )
        return {"result": result}
    
    elif tool_name == "get_terminology_rules":
        # Return terminology guidelines for the language
        provider = terminology_checker.llm_provider
        rules = provider._get_terminology_context(arguments["language"])
        return {"result": {"language": arguments["language"], "rules": rules}}
    
    else:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

@app.get("/resources")
async def list_resources(authorization: str = Header(None)):
    """
    MCP-style resource listing.
    """
    if not verify_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    return {
        "resources": [
            {
                "uri": "terminology://en",
                "name": "English UI Terminology Rules",
                "mimeType": "application/json",
                "description": "Comprehensive English UI terminology guidelines and preferences"
            },
            {
                "uri": "terminology://jp", 
                "name": "Japanese UI Terminology Rules",
                "mimeType": "application/json",
                "description": "Japanese UI terminology guidelines and localization preferences"
            },
            {
                "uri": "llm://analysis",
                "name": "LLM-Powered Analysis",
                "mimeType": "application/json", 
                "description": "Context-aware terminology analysis using Large Language Models"
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 