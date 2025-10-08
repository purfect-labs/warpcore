#!/usr/bin/env python3
# 🌊 WARPCORE GO! - Ultra compact launcher with template rendering
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("src/web/templates/main.html") as f:
        template = Template(f.read())
    
    # Render with basic context
    return template.render(
        current_tier='basic',
        current_tier_info={'icon': '🔓', 'name': 'Basic'},
        license_status=None,
        has_feature=lambda x: False,  # All features locked for demo
        available_features=[],
        locked_features=['aws_sso', 'gcp_auth', 'system_status'],
        upgrade_options=['trial', 'professional', 'enterprise']
    )

print("🌊 WARPCORE GO! http://localhost:8000")
uvicorn.run(app, host="0.0.0.0", port=8000)
