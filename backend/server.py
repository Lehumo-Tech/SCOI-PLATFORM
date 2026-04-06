from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from datetime import datetime, timezone

from routes import auth, entities, audit, assets, watchlist
from utils.auth import hash_password, verify_password
from services.seed_data import seed_mock_data

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="SCOI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(entities.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    app.state.db = db
    
    await db.users.create_index("email", unique=True)
    await db.entities.create_index("hashed_id")
    await db.entities.create_index("type")
    await db.entities.create_index("raw_name")
    await db.relationships.create_index("from_entity_id")
    await db.relationships.create_index("to_entity_id")
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.login_attempts.create_index("identifier")
    await db.watchlist.create_index([("user_id", 1), ("entity_id", 1)], unique=True)
    await db.alerts.create_index("watchlist_item_id")
    await db.alerts.create_index("created_at")
    
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@scoi.gov.za")
    admin_password = os.environ.get("ADMIN_PASSWORD", "SCOI2026!Admin")
    
    existing_admin = await db.users.find_one({"email": admin_email})
    if existing_admin is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "name": "System Administrator",
            "role": "admin",
            "created_at": datetime.now(timezone.utc)
        })
        logging.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing_admin["password_hash"]):
        hashed = hash_password(admin_password)
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hashed}}
        )
        logging.info(f"Admin password updated: {admin_email}")
    
    test_user_email = "investigator@scoi.gov.za"
    test_user_password = "Investigator2026!"
    
    existing_test = await db.users.find_one({"email": test_user_email})
    if existing_test is None:
        hashed = hash_password(test_user_password)
        await db.users.insert_one({
            "email": test_user_email,
            "password_hash": hashed,
            "name": "Test Investigator",
            "role": "investigator",
            "created_at": datetime.now(timezone.utc)
        })
        logging.info(f"Test user created: {test_user_email}")
    
    credentials_content = f"""# SCOI Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Test Investigator Account
- Email: {test_user_email}
- Password: {test_user_password}
- Role: investigator

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/refresh
- POST /api/auth/forgot-password
- POST /api/auth/reset-password

## Entity Endpoints
- POST /api/entities/
- POST /api/entities/search
- GET /api/entities/{{entity_id}}
- POST /api/entities/relationships
- GET /api/entities/graph/{{entity_id}}
- POST /api/entities/rules/evaluate?entity_id={{id}}
- POST /api/entities/reports/generate

## Audit Endpoints (Admin only)
- GET /api/audit/logs
- GET /api/audit/export
"""
    
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(credentials_content)
    
    logging.info("Startup completed. Test credentials written to /app/memory/test_credentials.md")
    
    await seed_mock_data(db)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SCOI API",
        "version": "1.0.0"
    }

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
