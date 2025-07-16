"""
API Key management API routes.

@author malou
@since 2025-01-08
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.schemas.common import SuccessResponse, ErrorResponse
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyListResponse,
    APIKeyStatsResponse
)
from app.services.api_key_service import APIKeyService
from app.utils.logger import LoggerAdapter

logger = LoggerAdapter(__name__)
router = APIRouter(tags=["api-keys"])

async def get_api_key_service(session: AsyncSession = Depends(get_async_db)) -> APIKeyService:
    """Get API key service instance."""
    return APIKeyService(session)


@router.post("/", response_model=SuccessResponse[APIKeyResponse])
async def create_api_key(
    api_key_data: APIKeyCreate,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Create a new API key.
    
    @param api_key_data: APIKeyCreate - API key creation data
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyResponse] - Created API key information
    @throws HTTPException - If creation fails
    """
    try:
        logger.info(f"Creating API key for user: {api_key_data.user_id}")
        api_key = await api_key_service.create_api_key(api_key_data)
        
        logger.info(f"API key created successfully: {api_key.id}")
        return SuccessResponse(
            data=APIKeyResponse.model_validate(api_key),
            message="API key created successfully"
        )
    except ValueError as e:
        logger.error(f"Failed to create API key: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=SuccessResponse[APIKeyListResponse])
async def list_api_keys(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Get list of API keys with pagination and filtering.
    
    @param skip: int - Number of records to skip
    @param limit: int - Number of records to return
    @param user_id: Optional[uuid.UUID] - Filter by user ID
    @param is_active: Optional[bool] - Filter by active status
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyListResponse] - List of API keys
    """
    try:
        logger.info(f"Getting API keys list: skip={skip}, limit={limit}")
        api_keys, total = await api_key_service.get_api_keys(
            skip=skip,
            limit=limit,
            user_id=user_id,
            is_active=is_active
        )
        
        api_key_responses = [APIKeyResponse.model_validate(api_key) for api_key in api_keys]
        
        return SuccessResponse(
            data=APIKeyListResponse(
                api_keys=api_key_responses,
                total=total,
                skip=skip,
                limit=limit
            ),
            message="API keys retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get API keys list: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{api_key_id}", response_model=SuccessResponse[APIKeyResponse])
async def get_api_key(
    api_key_id: int,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Get API key by ID.
    
    @param api_key_id: int - API key ID
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyResponse] - API key information
    @throws HTTPException - If API key not found
    """
    try:
        logger.info(f"Getting API key: {api_key_id}")
        api_key = await api_key_service.get_api_key_by_id(api_key_id)
        
        if not api_key:
            logger.warning(f"API key not found: {api_key_id}")
            raise HTTPException(status_code=404, detail="API key not found")
        
        return SuccessResponse(
            data=APIKeyResponse.model_validate(api_key),
            message="API key retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{api_key_id}", response_model=SuccessResponse[APIKeyResponse])
async def update_api_key(
    api_key_id: int,
    api_key_data: APIKeyUpdate,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Update API key information.
    
    @param api_key_id: int - API key ID
    @param api_key_data: APIKeyUpdate - API key update data
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyResponse] - Updated API key information
    @throws HTTPException - If API key not found or update fails
    """
    try:
        logger.info(f"Updating API key: {api_key_id}")
        api_key = await api_key_service.update_api_key(api_key_id, api_key_data)
        
        if not api_key:
            logger.warning(f"API key not found for update: {api_key_id}")
            raise HTTPException(status_code=404, detail="API key not found")
        
        logger.info(f"API key updated successfully: {api_key_id}")
        return SuccessResponse(
            data=APIKeyResponse.model_validate(api_key),
            message="API key updated successfully"
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Failed to update API key: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{api_key_id}", response_model=SuccessResponse[dict])
async def delete_api_key(
    api_key_id: int,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Delete API key (soft delete).
    
    @param api_key_id: int - API key ID
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[dict] - Success message
    @throws HTTPException - If API key not found
    """
    try:
        logger.info(f"Deleting API key: {api_key_id}")
        success = await api_key_service.delete_api_key(api_key_id)
        
        if not success:
            logger.warning(f"API key not found for deletion: {api_key_id}")
            raise HTTPException(status_code=404, detail="API key not found")
        
        logger.info(f"API key deleted successfully: {api_key_id}")
        return SuccessResponse(
            data={"api_key_id": api_key_id},
            message="API key deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{api_key_id}/rotate", response_model=SuccessResponse[APIKeyResponse])
async def rotate_api_key(
    api_key_id: int,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Rotate API key (generate new key).
    
    @param api_key_id: int - API key ID
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyResponse] - API key with new key value
    @throws HTTPException - If API key not found
    """
    try:
        logger.info(f"Rotating API key: {api_key_id}")
        api_key = await api_key_service.rotate_api_key(api_key_id)
        
        if not api_key:
            logger.warning(f"API key not found for rotation: {api_key_id}")
            raise HTTPException(status_code=404, detail="API key not found")
        
        logger.info(f"API key rotated successfully: {api_key_id}")
        return SuccessResponse(
            data=APIKeyResponse.model_validate(api_key),
            message="API key rotated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rotate API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}", response_model=SuccessResponse[APIKeyListResponse])
async def get_user_api_keys(
    user_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Get API keys for a specific user.
    
    @param user_id: uuid.UUID - User ID
    @param skip: int - Number of records to skip
    @param limit: int - Number of records to return
    @param is_active: Optional[bool] - Filter by active status
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyListResponse] - List of user's API keys
    """
    try:
        logger.info(f"Getting API keys for user: {user_id}")
        api_keys, total = await api_key_service.get_api_keys(
            skip=skip,
            limit=limit,
            user_id=user_id,
            is_active=is_active
        )
        
        api_key_responses = [APIKeyResponse.model_validate(api_key) for api_key in api_keys]
        
        return SuccessResponse(
            data=APIKeyListResponse(
                api_keys=api_key_responses,
                total=total,
                skip=skip,
                limit=limit
            ),
            message="User API keys retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get user API keys: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/overview", response_model=SuccessResponse[APIKeyStatsResponse])
async def get_api_key_stats(
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Get API key statistics.
    
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyStatsResponse] - API key statistics
    """
    try:
        logger.info("Getting API key statistics")
        stats = await api_key_service.get_api_key_stats()
        
        return SuccessResponse(
            data=stats,
            message="API key statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get API key stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{api_key_id}/activate", response_model=SuccessResponse[APIKeyResponse])
async def activate_api_key(
    api_key_id: int,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Activate an API key.
    
    @param api_key_id: int - API key ID
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyResponse] - Activated API key information
    @throws HTTPException - If API key not found
    """
    try:
        logger.info(f"Activating API key: {api_key_id}")
        api_key = await api_key_service.activate_api_key(api_key_id)
        
        if not api_key:
            logger.warning(f"API key not found for activation: {api_key_id}")
            raise HTTPException(status_code=404, detail="API key not found")
        
        logger.info(f"API key activated successfully: {api_key_id}")
        return SuccessResponse(
            data=APIKeyResponse.model_validate(api_key),
            message="API key activated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{api_key_id}/deactivate", response_model=SuccessResponse[APIKeyResponse])
async def deactivate_api_key(
    api_key_id: int,
    api_key_service: APIKeyService = Depends(get_api_key_service)
):
    """
    Deactivate an API key.
    
    @param api_key_id: int - API key ID
    @param api_key_service: APIKeyService - API key service instance
    @return SuccessResponse[APIKeyResponse] - Deactivated API key information
    @throws HTTPException - If API key not found
    """
    try:
        logger.info(f"Deactivating API key: {api_key_id}")
        api_key = await api_key_service.deactivate_api_key(api_key_id)
        
        if not api_key:
            logger.warning(f"API key not found for deactivation: {api_key_id}")
            raise HTTPException(status_code=404, detail="API key not found")
        
        logger.info(f"API key deactivated successfully: {api_key_id}")
        return SuccessResponse(
            data=APIKeyResponse.model_validate(api_key),
            message="API key deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 