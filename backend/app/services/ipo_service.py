from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from datetime import datetime
import math

from app.models.ipo import IPO, IPOStatus
from app.schemas.ipo import IPOCreate, IPOUpdate, IPOFilter


class IPOService:
    """
    Service layer for IPO operations.
    Handles business logic and database interactions.
    """
    
    @staticmethod
    def create_ipo(db: Session, ipo_data: IPOCreate) -> IPO:
        """
        Create a new IPO entry.
        
        Args:
            db: Database session
            ipo_data: IPO creation data
            
        Returns:
            Created IPO object
        """
        db_ipo = IPO(**ipo_data.model_dump())
        db.add(db_ipo)
        db.commit()
        db.refresh(db_ipo)
        return db_ipo
    
    @staticmethod
    def get_ipo_by_id(db: Session, ipo_id: int) -> Optional[IPO]:
        """
        Get IPO by ID.
        
        Args:
            db: Database session
            ipo_id: IPO identifier
            
        Returns:
            IPO object or None
        """
        return db.query(IPO).filter(IPO.id == ipo_id).first()
    
    @staticmethod
    def get_ipo_by_symbol(db: Session, symbol: str) -> Optional[IPO]:
        """
        Get IPO by symbol.
        
        Args:
            db: Database session
            symbol: IPO symbol/ticker
            
        Returns:
            IPO object or None
        """
        return db.query(IPO).filter(IPO.symbol == symbol).first()
    
    @staticmethod
    def get_ipos(
        db: Session,
        filters: Optional[IPOFilter] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[IPO], int]:
        """
        Get paginated list of IPOs with filters.
        
        Args:
            db: Database session
            filters: Filter parameters
            skip: Number of records to skip
            limit: Maximum records to return
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Tuple of (IPO list, total count)
        """
        query = db.query(IPO)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.filter(IPO.status == filters.status)
            
            if filters.ipo_type:
                query = query.filter(IPO.ipo_type == filters.ipo_type)
            
            if filters.industry_sector:
                query = query.filter(IPO.industry_sector == filters.industry_sector)
            
            if filters.min_issue_size:
                query = query.filter(IPO.issue_size_rs_cr >= filters.min_issue_size)
            
            if filters.max_issue_size:
                query = query.filter(IPO.issue_size_rs_cr <= filters.max_issue_size)
            
            if filters.min_subscription:
                query = query.filter(IPO.total_subscription >= filters.min_subscription)
            
            if filters.min_risk_score is not None:
                query = query.filter(IPO.risk_score >= filters.min_risk_score)
            
            if filters.max_risk_score is not None:
                query = query.filter(IPO.risk_score <= filters.max_risk_score)
            
            if filters.search:
                search_pattern = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        IPO.company_name.ilike(search_pattern),
                        IPO.symbol.ilike(search_pattern)
                    )
                )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(IPO, sort_by, IPO.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        ipos = query.offset(skip).limit(limit).all()
        
        return ipos, total
    
    @staticmethod
    def update_ipo(db: Session, ipo_id: int, ipo_data: IPOUpdate) -> Optional[IPO]:
        """
        Update an existing IPO.
        
        Args:
            db: Database session
            ipo_id: IPO identifier
            ipo_data: Update data
            
        Returns:
            Updated IPO object or None
        """
        db_ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
        if not db_ipo:
            return None
        
        # Update only provided fields
        update_data = ipo_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_ipo, field, value)
        
        db.commit()
        db.refresh(db_ipo)
        return db_ipo
    
    @staticmethod
    def delete_ipo(db: Session, ipo_id: int) -> bool:
        """
        Delete an IPO.
        
        Args:
            db: Database session
            ipo_id: IPO identifier
            
        Returns:
            True if deleted, False if not found
        """
        db_ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
        if not db_ipo:
            return False
        
        db.delete(db_ipo)
        db.commit()
        return True
    
    @staticmethod
    def get_active_ipos(db: Session) -> List[IPO]:
        """
        Get currently open IPOs.
        
        Returns:
            List of active IPOs
        """
        now = datetime.now()
        return db.query(IPO).filter(
            and_(
                IPO.status == IPOStatus.OPEN,
                IPO.open_date <= now,
                IPO.close_date >= now
            )
        ).all()
    
    @staticmethod
    def get_upcoming_ipos(db: Session, limit: int = 10) -> List[IPO]:
        """
        Get upcoming IPOs sorted by open date.
        
        Returns:
            List of upcoming IPOs
        """
        return db.query(IPO).filter(
            IPO.status == IPOStatus.UPCOMING
        ).order_by(IPO.open_date.asc()).limit(limit).all()
    
    @staticmethod
    def update_ml_risk_score(
        db: Session,
        ipo_id: int,
        risk_score: float,
        risk_category: str
    ) -> Optional[IPO]:
        """
        Update ML risk assessment for an IPO.
        
        Args:
            db: Database session
            ipo_id: IPO identifier
            risk_score: Risk score (0-100)
            risk_category: Risk category (low/medium/high)
            
        Returns:
            Updated IPO object or None
        """
        db_ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
        if not db_ipo:
            return None
        
        db_ipo.risk_score = risk_score
        db_ipo.risk_category = risk_category
        db_ipo.ml_processed = True
        db_ipo.ml_processed_at = datetime.now()
        
        db.commit()
        db.refresh(db_ipo)
        return db_ipo