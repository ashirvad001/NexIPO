import pdfplumber
import re
from typing import Dict, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF processing utility for extracting and cleaning prospectus text."""
    
    @staticmethod
    def extract_text(pdf_path: str) -> Tuple[str, Dict]:
        """Extract text using pdfplumber"""
        try:
            full_text = []
            metadata = {
                "total_pages": 0,
                "method": "pdfplumber",
                "has_images": False,
                "has_tables": False
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                metadata["total_pages"] = len(pdf.pages)
                
                # OPTIMIZATION: Process only the first 50 pages and skip slow table extraction
                # This drastically reduces the time it takes to "download" and process the RHP
                pages_to_process = pdf.pages[:50]
                
                for page_num, page in enumerate(pages_to_process, 1):
                    text = page.extract_text()
                    if text:
                        full_text.append(f"\n--- Page {page_num} ---\n")
                        full_text.append(text)
                    
                    # Table extraction is extremely slow in pdfplumber, skipping for performance
                    # tables = page.extract_tables()
                    
                    # if page.images:
                    #     metadata["has_images"] = True
            
            if len(pdf.pages) > 50:
                full_text.append("\n... [Text extraction limited to first 50 pages for performance] ...\n")
            
            return "\n".join(full_text), metadata
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extracted text"""
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = text.replace('\x00', '')
        text = text.replace('\ufffd', '')
        return text.strip()
    
    @staticmethod
    def extract_sections(text: str) -> Dict[str, str]:
        """Extract common prospectus sections"""
        sections = {}
        
        section_patterns = {
            "company_overview": r"(?i)(company overview|about (?:the )?company|business overview)",
            "risk_factors": r"(?i)risk factors?",
            "financial_information": r"(?i)(financial information|financial statements?|financials)",
            "management": r"(?i)(management|board of directors|key managerial personnel)",
            "objects_of_issue": r"(?i)(objects? of (?:the )?issue|use of proceeds)",
            "industry_overview": r"(?i)industry overview",
            "competitive_strengths": r"(?i)(competitive (?:strengths?|advantages?))",
            "business_strategy": r"(?i)(business strategy|growth strategy)",
        }
        
        for section_name, pattern in section_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                start_pos = match.start()
                next_section_pos = len(text)
                for other_pattern in section_patterns.values():
                    if other_pattern == pattern:
                        continue
                    next_matches = re.finditer(other_pattern, text[start_pos + 100:])
                    for next_match in next_matches:
                        next_section_pos = min(next_section_pos, start_pos + 100 + next_match.start())
                        break
                
                section_text = text[start_pos:next_section_pos]
                sections[section_name] = section_text[:5000]
                break
        
        return sections
    
    @staticmethod
    def get_pdf_info(pdf_path: str) -> Dict:
        """Get PDF metadata"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return {
                    "page_count": len(pdf.pages),
                    "metadata": pdf.metadata,
                    "file_size_mb": Path(pdf_path).stat().st_size / (1024 * 1024),
                }
        except Exception as e:
            logger.error(f"Failed to get PDF info: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _process_prospectus_sync(pdf_path: str) -> Dict:
        """Complete prospectus processing pipeline (synchronous)"""
        try:
            pdf_info = PDFProcessor.get_pdf_info(pdf_path)
            raw_text, extraction_metadata = PDFProcessor.extract_text(pdf_path)
            cleaned_text = PDFProcessor.clean_text(raw_text)
            sections = PDFProcessor.extract_sections(cleaned_text)
            
            return {
                "raw_text": raw_text[:100000],
                "cleaned_text": cleaned_text[:100000],
                "sections": sections,
                "pdf_info": pdf_info,
                "extraction_metadata": extraction_metadata,
                "success": True,
                "word_count": len(cleaned_text.split()),
                "char_count": len(cleaned_text),
            }
            
        except Exception as e:
            logger.error(f"Prospectus processing failed: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def process_prospectus(pdf_path: str) -> Dict:
        """Complete prospectus processing pipeline asynchronously"""
        import asyncio
        return await asyncio.to_thread(PDFProcessor._process_prospectus_sync, pdf_path)
