from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.file_service import FileService
from app.services.ipo_service import IPOService
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload/prospectus/{ipo_id}")
async def upload_prospectus(
    ipo_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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

# -------------------------------------------------------------
# RHP Automated Downloads & Viewing
# -------------------------------------------------------------
import os
from . import * # satisfy linter, implicit

@router.get("/rhp/search/{company_name}")
async def search_rhp_online(company_name: str):
    """
    Search for RHP online and return download links directly 
    (Placeholder format in case we want to stream straight link vs scrape)
    """
    from app.services.rhp_downloader import RHPDownloader
    downloader = RHPDownloader()
    
    # Just try Chittorgarh search for now to see if we find a link
    search_query = company_name.replace(" ", "+")
    search_url = f"https://www.chittorgarh.com/search.asp?q={search_query}"
    
    return {
        "success": True,
        "search_url": search_url,
        "message": "Direct link extraction requires full download flow currently. Call /rhp/download."
    }

@router.post("/rhp/download/{ipo_id}")
async def download_rhp_for_ipo(
    ipo_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Automatically download RHP from online sources
    """
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(status_code=404, detail="IPO not found")
        
    from app.services.rhp_downloader import RHPDownloader
    downloader = RHPDownloader()
    
    download_dir = os.path.join(os.getcwd(), "tmp_downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    result = await downloader.process_ipo(ipo, download_dir)
    return result

@router.get("/rhp/view/{ipo_id}")
async def view_rhp(
    ipo_id: int,
    db: Session = Depends(get_db)
):
    """
    Return RHP PDF with inline disposition for in-browser viewing
    """
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo or not ipo.prospectus_file_id:
        raise HTTPException(status_code=404, detail="Prospectus not found for this IPO")
        
    file_path = FileService.get_file_path(ipo.prospectus_file_id)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File on disk missing")
        
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={ipo.symbol or ipo.company_name}_RHP.pdf"}
    )
