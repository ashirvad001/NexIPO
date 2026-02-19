from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.file_service import FileService
from app.services.ipo_service import IPOService

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload/prospectus/{ipo_id}")
async def upload_prospectus(
    ipo_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload prospectus PDF for an IPO"""
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    result = await FileService.upload_prospectus(ipo_id, file)
    
    IPOService.update_ipo(db, ipo_id, {
        "prospectus_file_id": result["file_id"]
    })
    
    return {
        "message": "Prospectus uploaded and processed successfully",
        "ipo_id": ipo_id,
        "company_name": ipo.company_name,
        **result
    }


@router.get("/prospectus/{ipo_id}")
async def get_prospectus(
    ipo_id: int,
    include_full_text: bool = False,
    db: Session = Depends(get_db)
):
    """Get prospectus data for an IPO"""
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    prospectus = await FileService.get_prospectus(ipo_id)
    if not prospectus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prospectus found for IPO {ipo_id}"
        )
    
    if not include_full_text:
        prospectus.pop("raw_text", None)
        prospectus.pop("cleaned_text", None)
    
    return {
        "ipo_id": ipo_id,
        "company_name": ipo.company_name,
        "prospectus": prospectus
    }


@router.get("/prospectus/{ipo_id}/sections")
async def get_prospectus_sections(
    ipo_id: int,
    db: Session = Depends(get_db)
):
    """Get extracted sections from prospectus"""
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    prospectus = await FileService.get_prospectus(ipo_id)
    if not prospectus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prospectus found for IPO {ipo_id}"
        )
    
    return {
        "ipo_id": ipo_id,
        "company_name": ipo.company_name,
        "sections": prospectus.get("sections", {}),
        "available_sections": list(prospectus.get("sections", {}).keys())
    }


@router.get("/prospectus/{ipo_id}/section/{section_name}")
async def get_prospectus_section(
    ipo_id: int,
    section_name: str,
    db: Session = Depends(get_db)
):
    """Get specific section from prospectus"""
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    prospectus = await FileService.get_prospectus(ipo_id)
    if not prospectus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prospectus found for IPO {ipo_id}"
        )
    
    sections = prospectus.get("sections", {})
    if section_name not in sections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section '{section_name}' not found. Available: {list(sections.keys())}"
        )
    
    return {
        "ipo_id": ipo_id,
        "company_name": ipo.company_name,
        "section_name": section_name,
        "content": sections[section_name]
    }


@router.get("/download/prospectus/{ipo_id}")
async def download_prospectus(
    ipo_id: int,
    db: Session = Depends(get_db)
):
    """Download original prospectus PDF file"""
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    if not ipo.prospectus_file_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prospectus file for IPO {ipo_id}"
        )
    
    file_path = FileService.get_file_path(ipo.prospectus_file_id)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospectus file not found on server"
        )
    
    metadata = await FileService.get_file_metadata(ipo.prospectus_file_id)
    original_filename = metadata.get("original_filename", "prospectus.pdf") if metadata else "prospectus.pdf"
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=original_filename
    )


@router.delete("/prospectus/{ipo_id}")
async def delete_prospectus(
    ipo_id: int,
    db: Session = Depends(get_db)
):
    """Delete prospectus data and file for an IPO"""
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    deleted = await FileService.delete_prospectus(ipo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prospectus found for IPO {ipo_id}"
        )
    
    IPOService.update_ipo(db, ipo_id, {
        "prospectus_file_id": None
    })
    
    return {
        "message": "Prospectus deleted successfully",
        "ipo_id": ipo_id,
        "company_name": ipo.company_name
    }


@router.get("/metadata/{file_id}")
async def get_file_metadata(file_id: str):
    """Get metadata for a specific file"""
    metadata = await FileService.get_file_metadata(file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File metadata not found for {file_id}"
        )
    
    return metadata
