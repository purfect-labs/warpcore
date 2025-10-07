#!/usr/bin/env python3
"""
Simple WARPCORE License API Test Server
"""

import sys
import uvicorn
from fastapi import FastAPI
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import only what we need for license testing
from src.api.controllers.license_controller import LicenseController

app = FastAPI(title="WARPCORE License API Test", version="1.0.0")

# Initialize license controller
license_controller = LicenseController()

@app.get("/")
def read_root():
    return {"message": "WARPCORE License API Test Server", "status": "running"}

@app.get("/api/license/status")
async def get_license_status():
    """Get current license status"""
    return await license_controller.get_license_status()

@app.post("/api/license/generate")
async def generate_license_key(request: dict):
    """Generate a license key"""
    return await license_controller.generate_custom_license_key(
        user_email=request.get("user_email", "test@example.com"),
        user_name=request.get("user_name", "Test User"),
        days=request.get("days", 30),
        features=request.get("features", ["basic_access"]),
        license_type=request.get("license_type", "trial")
    )

@app.post("/api/license/validate")
async def validate_license(request: dict):
    """Validate a license key"""
    return await license_controller.validate_license(
        license_key=request.get("license_key", "")
    )

@app.post("/api/license/apply")
async def apply_license(request: dict):
    """Apply (activate) a license"""
    return await license_controller.apply_license(
        license_key=request.get("license_key", "")
    )

@app.delete("/api/license/deactivate")
async def deactivate_license():
    """Deactivate current license"""
    return await license_controller.deactivate_license()

if __name__ == "__main__":
    print("🚀 Starting WARPCORE License API Test Server...")
    print("📋 Available endpoints:")
    print("   GET  /                     - Server status")
    print("   GET  /api/license/status   - License status")
    print("   POST /api/license/generate - Generate license")
    print("   POST /api/license/validate - Validate license")
    print("   POST /api/license/apply    - Apply license")
    print("   DELETE /api/license/deactivate - Deactivate license")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")