import os
import secrets
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import hashlib

from models.schemas import (
    LoginRequest, RegisterRequest, UserResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from utils.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

async def check_brute_force(db: AsyncIOMotorDatabase, identifier: str) -> None:
    attempt = await db.login_attempts.find_one({"identifier": identifier})
    if attempt and attempt["count"] >= 5:
        lockout_until = attempt["locked_until"]
        if lockout_until and lockout_until > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail=f"Too many login attempts. Try again after {lockout_until.isoformat()}")

async def record_failed_login(db: AsyncIOMotorDatabase, identifier: str) -> None:
    existing = await db.login_attempts.find_one({"identifier": identifier})
    if existing:
        new_count = existing["count"] + 1
        locked_until = None
        if new_count >= 5:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$set": {"count": new_count, "locked_until": locked_until, "last_attempt": datetime.now(timezone.utc)}}
        )
    else:
        await db.login_attempts.insert_one({
            "identifier": identifier,
            "count": 1,
            "locked_until": None,
            "last_attempt": datetime.now(timezone.utc)
        })

async def clear_login_attempts(db: AsyncIOMotorDatabase, identifier: str) -> None:
    await db.login_attempts.delete_many({"identifier": identifier})

@router.post("/register")
async def register(request: RegisterRequest, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = request.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = hash_password(request.password)
    user_doc = {
        "email": email,
        "password_hash": hashed_pw,
        "name": request.name,
        "role": request.role.value,
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(
        key="access_token", value=access_token, httponly=True,
        secure=False, samesite="lax", max_age=900, path="/"
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True,
        secure=False, samesite="lax", max_age=604800, path="/"
    )
    
    return UserResponse(
        id=user_id,
        email=email,
        name=request.name,
        role=request.role.value,
        created_at=user_doc["created_at"]
    )

@router.post("/login")
async def login(request_obj: LoginRequest, response: Response, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = request_obj.email.lower()
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"{client_ip}:{email}"
    
    await check_brute_force(db, identifier)
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(request_obj.password, user["password_hash"]):
        await record_failed_login(db, identifier)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    await clear_login_attempts(db, identifier)
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(
        key="access_token", value=access_token, httponly=True,
        secure=False, samesite="lax", max_age=900, path="/"
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True,
        secure=False, samesite="lax", max_age=604800, path="/"
    )
    
    return UserResponse(
        id=user_id,
        email=email,
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"]
    )

@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    await get_current_user(request, db)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_me(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await get_current_user(request, db)
    return UserResponse(
        id=user["_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"]
    )

@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    import jwt
    from utils.auth import get_jwt_secret, JWT_ALGORITHM
    
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_id = str(user["_id"])
        access_token = create_access_token(user_id, user["email"])
        
        response.set_cookie(
            key="access_token", value=access_token, httponly=True,
            secure=False, samesite="lax", max_age=900, path="/"
        )
        
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = request.email.lower()
    user = await db.users.find_one({"email": email})
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    
    token = secrets.token_urlsafe(32)
    await db.password_reset_tokens.insert_one({
        "token": token,
        "user_id": user["_id"],
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    print(f"\n{'='*60}")
    print(f"PASSWORD RESET LINK FOR {email}:")
    print(f"{reset_link}")
    print(f"{'='*60}\n")
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    token_doc = await db.password_reset_tokens.find_one({"token": request.token, "used": False})
    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if token_doc["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")
    
    hashed_pw = hash_password(request.new_password)
    await db.users.update_one(
        {"_id": token_doc["user_id"]},
        {"$set": {"password_hash": hashed_pw}}
    )
    
    await db.password_reset_tokens.update_one(
        {"token": request.token},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password reset successful"}