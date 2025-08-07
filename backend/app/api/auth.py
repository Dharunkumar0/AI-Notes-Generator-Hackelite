from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import get_collection
from app.models.user import UserCreate, UserInDB, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

class FirebaseAuthRequest(BaseModel):
    id_token: str

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

async def verify_firebase_token(id_token: str) -> dict:
    """Verify Firebase ID token."""
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={settings.firebase_api_key}"
        payload = {"idToken": id_token}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if "users" in data and len(data["users"]) > 0:
                return data["users"][0]
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
                
    except httpx.HTTPStatusError as e:
        logger.error(f"Firebase API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Get current authenticated user."""
    try:
        firebase_user = await verify_firebase_token(credentials.credentials)
        
        # Get user from database
        users_collection = get_collection("users")
        user_doc = await users_collection.find_one({"firebase_uid": firebase_user["localId"]})
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )

@router.post("/login", response_model=AuthResponse)
async def login(auth_request: FirebaseAuthRequest):
    """Login with Firebase ID token."""
    try:
        # Verify Firebase token
        firebase_user = await verify_firebase_token(auth_request.id_token)
        
        # Get or create user in database
        users_collection = get_collection("users")
        
        # Check if user exists
        existing_user = await users_collection.find_one({"firebase_uid": firebase_user["localId"]})
        
        if existing_user:
            # Update last login
            await users_collection.update_one(
                {"firebase_uid": firebase_user["localId"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            existing_user["_id"] = str(existing_user["_id"])  # Convert ObjectId to string
            user = UserResponse(**existing_user)
        else:
            # Create new user
            user_data = UserCreate(
                email=firebase_user["email"],
                display_name=firebase_user.get("displayName"),
                photo_url=firebase_user.get("photoUrl"),
                firebase_uid=firebase_user["localId"]
            )
            
            # Create new user document
            user_in_db = UserInDB(**user_data.dict())
            user_dict = user_in_db.model_dump(by_alias=True)
            
            # Insert into database
            result = await users_collection.insert_one(user_dict)
            
            # Create response with all fields
            user_dict["_id"] = str(result.inserted_id)  # Convert ObjectId to string
            user = UserResponse(**user_dict)
        
        return AuthResponse(
            user=user,
            access_token=auth_request.id_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        logger.error(f"Firebase user data: {firebase_user if 'firebase_user' in locals() else 'Not available'}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user profile."""
    try:
        users_collection = get_collection("users")
        
        # Build update data
        update_data = {}
        if profile_data.display_name is not None:
            update_data["display_name"] = profile_data.display_name
        if profile_data.email is not None:
            update_data["email"] = profile_data.email
        
        if not update_data:
            return current_user
        
        # Update user in database
        await users_collection.update_one(
            {"firebase_uid": current_user.firebase_uid},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await users_collection.find_one({"firebase_uid": current_user.firebase_uid})
        updated_user["_id"] = str(updated_user["_id"])
        
        return UserResponse(**updated_user)
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/logout")
async def logout():
    """Logout user (client-side token invalidation)."""
    return {"message": "Logged out successfully"}

@router.delete("/account")
async def delete_account(current_user: UserResponse = Depends(get_current_user)):
    """Delete user account."""
    try:
        users_collection = get_collection("users")
        history_collection = get_collection("history")
        
        # Delete user data
        await users_collection.delete_one({"firebase_uid": current_user.firebase_uid})
        await history_collection.delete_many({"user_id": str(current_user.id)})
        
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        ) 