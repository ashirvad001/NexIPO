import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import aiofiles 
import magic  
from fastapi import UploadFile, HTTPException, status

from app.core.config import get_settings
from app.core.mongodb import get_prospectus_collection, get_file_metadata_collection
from app.utils.pdf_processor import PDFProcessor

settings = get_settings()


class FileService:
    """Service for handling file uploads, storage, and processing"""
    
    ALLOWED_EXTENSIONS = {'.pdf'}
    ALLOWED_MIME_TYPES = {'application/pdf'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR = Path("uploads/prospectus")
    
    @classmethod
    def setup_upload_directory(cls):
        """Create upload directory if it doesn't exist"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    async def validate_file(cls, file: UploadFile) -> None:
        """Validate uploaded file"""
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )
        
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {cls.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        header = await file.read(2048)
        await file.seek(0)
        
        mime = magic.from_buffer(header, mime=True)
        if mime not in cls.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Expected PDF, got {mime}"
            )
    
    @classmethod
    async def save_file(cls, file: UploadFile) -> str:
        """Save uploaded file to disk"""
        cls.setup_upload_directory()
        
        file_id = f"{uuid.uuid4()}{Path(file.filename).suffix}"
        file_path = cls.UPLOAD_DIR / file_id
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_id
    
    @classmethod
    async def delete_file(cls, file_id: str) -> bool:
        """Delete file from disk"""
        file_path = cls.UPLOAD_DIR / file_id
        
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    @classmethod
    def get_file_path(cls, file_id: str) -> Path:
        """Get full path to file"""
        return cls.UPLOAD_DIR / file_id
    
    @classmethod
    async def upload_prospectus(cls, ipo_id: int, file: UploadFile) -> dict:
        """Upload and process IPO prospectus"""
        await cls.validate_file(file)
        file_id = await cls.save_file(file)
        file_path = cls.get_file_path(file_id)
        
        try:
            processed_data = await PDFProcessor.process_prospectus(str(file_path))
            
            if not processed_data.get("success"):
                await cls.delete_file(file_id)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"PDF processing failed: {processed_data.get('error')}"
                )
            
            prospectus_collection = await get_prospectus_collection()
            file_metadata_collection = await get_file_metadata_collection()
            
            prospectus_doc = {
                "ipo_id": ipo_id,
                "file_id": file_id,
                "raw_text": processed_data["raw_text"],
                "cleaned_text": processed_data["cleaned_text"],
                "sections": processed_data["sections"],
                "created_at": datetime.utcnow(),
                "word_count": processed_data["word_count"],
                "char_count": processed_data["char_count"],
            }
            
            prospectus_result = await prospectus_collection.insert_one(prospectus_doc)
            
            file_metadata = {
                "file_id": file_id,
                "ipo_id": ipo_id,
                "original_filename": file.filename,
                "file_size": file_path.stat().st_size,
                "mime_type": file.content_type,
                "uploaded_at": datetime.utcnow(),
                "pdf_info": processed_data["pdf_info"],
                "extraction_metadata": processed_data["extraction_metadata"],
                "mongodb_id": str(prospectus_result.inserted_id),
            }
            
            await file_metadata_collection.insert_one(file_metadata)
            
            return {
                "file_id": file_id,
                "original_filename": file.filename,
                "file_size": file_path.stat().st_size,
                "page_count": processed_data["pdf_info"].get("page_count"),
                "word_count": processed_data["word_count"],
                "sections_extracted": list(processed_data["sections"].keys()),
                "uploaded_at": datetime.utcnow().isoformat(),
                "success": True,
            }
            
        except Exception as e:
            await cls.delete_file(file_id)
            raise
    
    @classmethod
    async def get_prospectus(cls, ipo_id: int) -> Optional[dict]:
        """Get prospectus data for an IPO"""
        collection = await get_prospectus_collection()
        prospectus = await collection.find_one(
            {"ipo_id": ipo_id},
            sort=[("created_at", -1)]
        )
        
        if prospectus:
            prospectus["_id"] = str(prospectus["_id"])
            return prospectus
        return None
    
    @classmethod
    async def get_file_metadata(cls, file_id: str) -> Optional[dict]:
        """Get file metadata"""
        collection = await get_file_metadata_collection()
        metadata = await collection.find_one({"file_id": file_id})
        
        if metadata:
            metadata["_id"] = str(metadata["_id"])
            return metadata
        return None
    
    @classmethod
    async def delete_prospectus(cls, ipo_id: int) -> bool:
        """Delete prospectus data and file for an IPO"""
        prospectus = await cls.get_prospectus(ipo_id)
        if not prospectus:
            return False
        
        file_id = prospectus.get("file_id")
        
        prospectus_collection = await get_prospectus_collection()
        file_metadata_collection = await get_file_metadata_collection()
        
        await prospectus_collection.delete_many({"ipo_id": ipo_id})
        await file_metadata_collection.delete_many({"ipo_id": ipo_id})
        
        if file_id:
            await cls.delete_file(file_id)
        
        return True
