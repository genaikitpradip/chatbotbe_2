from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from models import UserCreate, UserLogin, UserPublic, TokenResponse
from database import get_database
from security import hash_password, verify_password, create_access_token, get_current_user
import uuid
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic)
async def register(payload: UserCreate):
    db = get_database()
    existing = await db.users.find_one({"email": payload.email.lower().strip()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = {
         "_id": str(uuid.uuid4()),
        # "_id": payload.email.lower().strip(),  # use email as _id for simplicity
        "email": payload.email.lower().strip(),
        "name": payload.name,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.utcnow(),
    }
    await db.users.insert_one(doc)
    doc["_id"] = str(doc["_id"])
    return UserPublic(**doc)

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    db = get_database()
    user = await db.users.find_one({"email": payload.email.lower().strip()})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Use user's _id (email here) as sub
    token = create_access_token({"sub": str(user["_id"])})
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserPublic)
async def me(current=Depends(get_current_user)):
    # normalize/return safe fields
    return UserPublic(
        _id=current["_id"],
        email=current["email"],
        name=current.get("name"),
        created_at=current.get("created_at"),
    )
