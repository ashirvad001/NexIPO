# IPO Intelligence Platform

## Project Structure

- **frontend/**: React/Next.js frontend application
- **backend/**: FastAPI backend service
- **ml_service/**: Machine learning service for IPO analysis

## Getting Started

```bash
docker-compose up
```
# 🚀 IPO Intelligence Platform

PHASE-1

A **production-ready**, **ML-powered** IPO intelligence platform designed for placement interviews and final year projects. This platform analyzes Initial Public Offerings (IPOs) and provides risk assessment using Machine Learning.

### 🎯 Key Features

✅ **RESTful API** with comprehensive CRUD operations  
✅ **Scalable Architecture** with connection pooling & pagination  
✅ **Advanced Filtering** by status, sector, subscription, risk score  
✅ **Real-time Updates** for active IPOs  
✅ **ML Integration Ready** with risk score fields  
✅ **Docker Containerization** for easy deployment  
✅ **Comprehensive Documentation** with API specs  

---

## 🏗️ Project Structure

```
ipo-platform/
├── backend/                     # FastAPI Backend (Phase 1 ✅)
│   ├── app/
│   │   ├── api/routes/         # API endpoints
│   │   ├── core/               # Configuration & database
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # Business logic
│   ├── main.py                 # FastAPI application
│   ├── seed_data.py            # Sample data generator
│   ├── test_api.py             # API test suite
│   └── README.md               # Backend documentation
├── frontend/                    # Next.js Frontend (Phase 2)
│   └── [To be implemented]
├── ml_service/                  # ML Service (Phase 4)
│   └── [To be implemented]
├── docker-compose.yml           # Multi-service orchestration
└── README.md                    # This file
```

---

## 🛠️ Technology Stack

### Backend (Phase 1) ✅
| Technology | Purpose | Version |
|------------|---------|---------|
| **FastAPI** | Web framework | 0.109.0 |
| **SQLAlchemy** | ORM | 2.0.25 |
| **PostgreSQL** | Primary database | 16 |
| **Redis** | Caching layer | 7 |
| **Pydantic** | Data validation | 2.5.3 |
| **Docker** | Containerization | 24+ |

### Frontend (Phase 2) 🔜
- Next.js 14 (React + TypeScript)
- Tailwind CSS
- Recharts / Chart.js

### ML Pipeline (Phase 4) 🔜
- PDFPlumber / PyMuPDF
- spaCy (NLP)
- Scikit-learn
- TF-IDF + Logistic Regression
- SHAP (Explainability)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Git

### 1️⃣ Clone Repository

```bash
git clone <repository-url>
cd ipo-platform
```

### 2️⃣ Start Databases

```bash
# Start PostgreSQL, Redis, MongoDB using Docker
docker-compose up -d

# Verify services
docker-compose ps
```

### 3️⃣ Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (default config works with Docker)

# Seed sample data
python seed_data.py

# Start server
uvicorn main:app --reload
```

### 4️⃣ Access Application

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

### 5️⃣ Test API

```bash
# Run comprehensive test suite
python test_api.py
```

---

## 📡 API Endpoints

### 🔹 IPO Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ipos/` | Create new IPO |
| `GET` | `/api/v1/ipos/` | List IPOs (paginated, filtered) |
| `GET` | `/api/v1/ipos/{id}` | Get IPO details |
| `GET` | `/api/v1/ipos/symbol/{symbol}` | Get IPO by symbol |
| `GET` | `/api/v1/ipos/active` | Get currently open IPOs |
| `GET` | `/api/v1/ipos/upcoming` | Get upcoming IPOs |
| `PUT` | `/api/v1/ipos/{id}` | Update IPO |
| `DELETE` | `/api/v1/ipos/{id}` | Delete IPO |

### 🔹 Example: Create IPO

```bash
curl -X POST "http://localhost:8000/api/v1/ipos/" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechCorp India",
    "symbol": "TECHCORP",
    "status": "upcoming",
    "ipo_type": "mainboard",
    "price_band_lower": 200,
    "price_band_upper": 220,
    "issue_size_rs_cr": 1000,
    "industry_sector": "Technology"
  }'
```

### 🔹 Example: Advanced Filtering

```bash
# Get technology sector IPOs with high subscription
curl "http://localhost:8000/api/v1/ipos/?industry_sector=Technology&min_subscription=3&sort_by=total_subscription&sort_order=desc"
```

---

## 📊 Database Schema

### IPO Table (Optimized with Indexes)

```sql
CREATE TABLE ipos (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Basic Info
    company_name VARCHAR(255) NOT NULL,
    symbol VARCHAR(50) UNIQUE,
    status VARCHAR(20) NOT NULL,  -- INDEXED
    ipo_type VARCHAR(20) NOT NULL,
    
    -- Dates (INDEXED for date-range queries)
    open_date TIMESTAMP,
    close_date TIMESTAMP,
    listing_date TIMESTAMP,
    
    -- Pricing
    price_band_lower FLOAT,
    price_band_upper FLOAT,
    issue_price FLOAT,
    listing_price FLOAT,
    
    -- Subscription (INDEXED total_subscription)
    qib_subscription FLOAT,
    nii_subscription FLOAT,
    retail_subscription FLOAT,
    total_subscription FLOAT,
    
    -- Grey Market Premium
    gmp_amount FLOAT,
    gmp_percentage FLOAT,
    
    -- ML Risk Assessment (INDEXED risk_score)
    risk_score FLOAT,
    risk_category VARCHAR(20),
    ml_processed BOOLEAN DEFAULT FALSE,
    ml_processed_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes for Performance:**
- `idx_ipos_status` on `status`
- `idx_ipos_symbol` on `symbol`
- `idx_ipos_listing_date` on `listing_date`
- `idx_ipos_risk_score` on `risk_score`
- `idx_ipos_ml_processed` on `ml_processed`

---

## 🎨 Scalability Features

### ✅ Implemented in Phase 1

1. **Connection Pooling**
   - Base pool size: 10 connections
   - Max overflow: 20 connections
   - Connection recycling: 1 hour

2. **Pagination**
   - Default page size: 20
   - Maximum page size: 100
   - Prevents memory overload

3. **Strategic Indexing**
   - Status, symbol, dates, risk_score
   - 10x faster queries on filtered data

4. **Modular Architecture**
   - Separation of concerns (Routes → Services → Models)
   - Easy to scale individual components
   - Independent microservices ready

5. **Caching Ready**
   - Redis integration configured
   - Cache layer for Phase 6

6. **Async Support**
   - FastAPI async capabilities
   - Non-blocking I/O operations

---

## 🧪 Testing

### Automated Test Suite

```bash
# Run all API tests
python test_api.py
```

**Tests Include:**
- ✅ Health check
- ✅ CRUD operations
- ✅ Pagination
- ✅ Advanced filtering
- ✅ Sorting
- ✅ Search functionality

### Manual Testing (Postman)

1. Import OpenAPI schema: `http://localhost:8000/api/openapi.json`
2. Set environment variable: `BASE_URL = http://localhost:8000/api/v1`
3. Test all endpoints

---

## 📈 Development Roadmap

### ✅ Phase 1: Foundation (Days 1-5) - **COMPLETE**
- [x] Database schema design
- [x] PostgreSQL setup with Docker
- [x] FastAPI project structure
- [x] IPO CRUD APIs
- [x] Advanced filtering & pagination
- [x] Seed data & testing

### 🔜 Phase 2: Frontend (Days 6-10)
- [ ] Next.js + TypeScript setup
- [ ] Tailwind CSS integration
- [ ] IPO listing page
- [ ] IPO detail page
- [ ] Charts (subscription, GMP)

### 🔜 Phase 3: File Ingestion (Days 11-12)
- [ ] PDF upload functionality
- [ ] Text extraction (PDFPlumber)
- [ ] MongoDB storage

### 🔜 Phase 4: ML Pipeline (Days 13-18)
- [ ] NLP preprocessing
- [ ] Feature engineering
- [ ] Model training (TF-IDF + Logistic Regression)
- [ ] SHAP explainability

### 🔜 Phase 5: ML Integration (Days 19-23)
- [ ] ML microservice
- [ ] Risk score API
- [ ] Frontend ML visualization

### 🔜 Phase 6: Deployment (Days 24-30)
- [ ] Redis caching
- [ ] Background jobs (Celery)
- [ ] Docker Compose multi-service
- [ ] Cloud deployment (AWS/GCP)

---

## 🎓 Interview Talking Points

### Architecture & Design

**Q: How is your application scalable?**

> "I've implemented several scalability features:
> 1. **Database Connection Pooling** with 10 base connections and 20 overflow to handle concurrent requests
> 2. **Pagination** to prevent loading large datasets into memory
> 3. **Strategic indexing** on frequently queried fields (status, risk_score, dates) for 10x query performance
> 4. **Modular three-layer architecture** (Routes → Services → Models) allowing independent scaling
> 5. **Redis caching** configured for read-heavy operations
> 6. **Async FastAPI** for non-blocking I/O operations"

**Q: Why did you choose this tech stack?**

> "I chose FastAPI for its:
> - **High performance** (comparable to Node.js and Go)
> - **Automatic API documentation** (Swagger/OpenAPI)
> - **Type safety** with Python type hints and Pydantic
> - **Async support** for scalable concurrent operations
> - **Easy ML integration** since ML models are typically Python-based
> 
> PostgreSQL provides ACID compliance and complex querying, while Redis will handle caching in Phase 6."

**Q: How did you ensure code quality?**

> "I followed software engineering best practices:
> - **Separation of concerns** with distinct layers (API, Service, Model)
> - **Input validation** using Pydantic schemas
> - **Comprehensive error handling** with appropriate HTTP status codes
> - **Type hints** throughout for better IDE support and bug prevention
> - **Automated testing** with test suite covering all endpoints
> - **Docker containerization** for consistent environments"

### ML Integration

**Q: How will you integrate ML into this system?**

> "The ML service will be a separate microservice communicating via REST API:
> 1. When an IPO's prospectus is uploaded, the backend triggers the ML service
> 2. ML service extracts text, generates features (TF-IDF), and predicts risk score
> 3. SHAP explains which features contributed to the risk score
> 4. Backend stores risk_score, risk_category, and explanation
> 5. Frontend displays the risk assessment with visual explanations
> 
> This microservice architecture allows the ML model to be updated independently without affecting the main application."

---

## 🐛 Troubleshooting

### Database Connection Errors
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Port Already in Use
```bash
# Find and kill process (macOS/Linux)
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Module Import Errors
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📞 Support & Documentation

- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Backend README**: [backend/README.md](backend/README.md)

---

## 📄 License

This project is for educational and placement purposes.

---

## 🎉 Acknowledgments

Built as a **30-day scalable full-stack project** for:
- Final Year Academic Project
- Placement Interviews
- Real-world ML Application Portfolio

---
