# 🚀 NexIPO - Advanced ML-Powered IPO Intelligence Platform

A **production-ready**, **ML-powered** IPO intelligence platform designed for comprehensive analysis, risk assessment, and volatility forecasting of Initial Public Offerings (IPOs) in the Indian stock market. Built as a scalable full-stack application suitable for placement interviews, academic projects, and real-world financial data analysis.

## 🌟 Key Features

✅ **Advanced ML Volatility Forecasting**: Predicts listing-day gains using a combined **BERT + LSTM** architecture analyzing global geopolitical news and historical data.
✅ **Public AI Track Record Page**: Transparently showcases the model's historical prediction accuracy, mean absolute error, and performance across Mainboard and SME IPOs.
✅ **Risk Assessment NLP Pipeline**: Uses TF-IDF and Logistic Regression to analyze Red Herring Prospectuses (RHPs) and generate explainable risk scores (0-100) using SHAP.
✅ **Real-time IPO Data Syncing**: Automated data scraping and enrichment from IPO Central and Moneycontrol.
✅ **Allotment & Probability Calculator**: Calculates the mathematical probability of allotment based on live subscription data (QIB, NII, Retail).
✅ **Comprehensive Dashboard & IPO Discovery**: Filter, sort, and search active, upcoming, and past IPOs (Mainboard & SME).
✅ **RHP Viewer & Downloader**: Integrated in-app PDF viewer for official prospectus documents.
✅ **User Authentication & Profiles**: Secure JWT-based authentication system with user profile management.
✅ **Scalable FastAPI Backend**: Featuring connection pooling, pagination, background tasks, and rate limiting.
✅ **Modern Next.js Frontend**: Responsive, animated, and beautifully designed UI using Tailwind CSS and Recharts.

---

## 🏗️ Project Structure

```
NexIPO/
├── backend/                     # FastAPI Backend & ML Pipelines
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/routes/          # RESTful API endpoints
│   │   ├── core/                # Configuration & security
│   │   ├── db/                  # Database connection pooling
│   │   ├── ml_service/          # NLP, TF-IDF, BERT, LSTM models
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   └── services/            # Business logic (Scraping, Auth, etc.)
│   ├── scripts/                 # Model training & DB seeding scripts
│   ├── tests/                   # Pytest automated test suite
│   └── main.py                  # FastAPI application entry point
├── frontend/                    # Next.js Frontend
│   ├── components/              # Reusable React components (UI, Charts, Modals)
│   ├── contexts/                # React Context (Auth, WebSockets)
│   ├── pages/                   # Next.js file-based routing
│   ├── services/                # Axios API client wrappers
│   └── styles/                  # Tailwind global styles
├── docker-compose.yml           # Multi-service orchestration (Prod)
└── docker-compose.dev.yml       # Multi-service orchestration (Dev)
```

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: Next.js 14 (React + TypeScript)
- **Styling**: Tailwind CSS
- **Data Visualization**: Recharts
- **Icons**: React Icons
- **State Management**: React Context API

### Backend
- **Web Framework**: FastAPI (Async Python)
- **Database ORM**: SQLAlchemy 2.0 with Alembic Migrations
- **Primary Database**: SQLite (Default) / PostgreSQL (Supported)
- **Data Validation**: Pydantic v2
- **Authentication**: JWT (JSON Web Tokens) & Passlib (Bcrypt)

### Machine Learning & Data Processing
- **Volatility Forecasting**: PyTorch, BERT (HuggingFace transformers), LSTM
- **Risk Classification**: Scikit-learn (TF-IDF + Logistic Regression)
- **Explainable AI**: SHAP (SHapley Additive exPlanations)
- **NLP & Text Processing**: NLTK, PyMuPDF (fitz), pdfplumber
- **Data Scraping**: BeautifulSoup4, Requests
- **Data Handling**: Pandas, NumPy

---

## 🚀 Quick Start Guide

### Prerequisites
- Node.js 18+ & npm
- Python 3.11+
- Git

### 1️⃣ Clone the Repository

```bash
git clone <repository-url>
cd NexIPO
```

### 2️⃣ Start the Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your specific API keys (e.g., NEWS_API_KEY) if needed

# Run database migrations
python -m alembic upgrade head

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```
*The backend will be available at `http://localhost:8000`*
*API Documentation (Swagger UI) at `http://localhost:8000/api/docs`*

### 3️⃣ Start the Frontend

Open a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Configure environment variables
cp .env.example .env.local

# Start the Next.js development server
npm run dev
```
*The frontend will be available at `http://localhost:3000`*

---

## 📡 Core API Endpoints

### 🔹 IPO Management & Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/ipos/` | List IPOs (paginated, filtered, sorted) |
| `GET` | `/api/v1/ipos/{id}` | Get detailed IPO information |
| `GET` | `/api/v1/ipos/active` | Get currently open IPOs |
| `GET` | `/api/v1/ipos/upcoming` | Get upcoming IPOs |
| `POST` | `/api/v1/ipos/sync` | Trigger manual web scraping sync |

### 🔹 Machine Learning & Volatility
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ml/predict/{ipo_id}` | Generate Prospectus NLP Risk Score |
| `POST` | `/api/v1/volatility/predict/{ipo_id}` | Forecast Listing Gain (BERT+LSTM) |
| `GET` | `/api/v1/model-accuracy` | Get historical ML prediction accuracy |
| `GET` | `/api/v1/model-accuracy/summary`| Get aggregate ML performance stats |
| `GET` | `/api/v1/volatility/high-volatility-alert`| Get high-risk IPO alerts |

### 🔹 Users & Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/signup` | Register a new user |
| `POST` | `/api/v1/auth/login/json` | Authenticate and get JWT token |
| `GET` | `/api/v1/auth/me` | Get current logged-in user profile |

### 🔹 Tools & Utilities
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/allotment/calculate/{ipo_id}` | Calculate allotment probability |
| `GET` | `/api/v1/files/rhp/search/{company}` | Search for official RHP documents |

---

## 🤖 Machine Learning Pipelines

NexIPO features two distinct machine learning pipelines designed to evaluate different aspects of an IPO.

### 1. Risk Assessment Pipeline (NLP on Prospectus)
Analyzes the official Red Herring Prospectus (RHP) to identify hidden risks.
- **Text Preprocessing**: Cleans and extracts key risk factors using NLTK (lemmatization, stop words).
- **Feature Extraction**: TF-IDF Vectorization (1000 features) combined with 34 custom metadata features (readability, financial ratios).
- **Classification**: A balanced Logistic Regression model predicts risk into Low (0-33), Medium (34-66), and High (67-100) buckets.
- **Explainability**: SHAP (SHapley Additive exPlanations) is used to extract the exact terms (e.g., "litigation", "debt") that drove the risk score, providing human-readable explanations on the frontend.

### 2. Volatility & Listing Gain Forecaster (BERT + LSTM)
Predicts the expected listing day gain percentage.
- **News Sentiment (BERT)**: Fetches recent global geopolitical and macroeconomic news using a News API, processing headlines through a pre-trained FinBERT model to extract market sentiment.
- **Time-Series Analysis (LSTM)**: Feeds the BERT sentiment embeddings, along with historical GMP (Grey Market Premium), subscription data, and sector performance into an LSTM (Long Short-Term Memory) neural network.
- **Output**: Predicts a continuous value representing the expected listing gain/loss percentage.
- **Track Record Logging**: Every prediction is logged to the `prediction_logs` table, allowing the public `/model-accuracy` page to transparently display the model's historical MAE (Mean Absolute Error) and directional accuracy.

---

## 📊 Database Schema Highlights

- `users`: Authentication and profile data (hashed passwords).
- `ipos`: Core IPO data (dates, pricing, financials, subscription metrics, ML risk scores).
- `gmp_history`: Time-series tracking of Grey Market Premium trends.
- `prediction_logs`: Immutable ledger of all ML volatility predictions for accuracy tracking and auditing.

---

## 🎓 Interview Talking Points

### Architecture & Scalability
- **Connection Pooling**: Uses SQLAlchemy's connection pooling to efficiently manage database connections and prevent bottlenecks during high traffic (e.g., when a popular IPO opens).
- **Async Processing**: The FastAPI backend utilizes Python's `asyncio` for non-blocking I/O operations, ensuring high throughput for web scraping and API requests.
- **CPU-bound Offloading**: ML inference tasks (like BERT sentiment analysis) are explicitly offloaded to thread pools (`run_in_executor`) to prevent blocking the async event loop.
- **Data Persistence Strategy**: Alembic migrations ensure that database schema changes (like adding the `prediction_logs` table) are version-controlled and safely deployed.

### Machine Learning Design Decisions
- **Why TF-IDF + Logistic Regression for Risk?**: While LLMs are popular, TF-IDF + LR is fast, lightweight, and highly interpretable. Using SHAP allows us to explicitly tell the user *why* an IPO is risky, meeting regulatory/financial transparency requirements.
- **Why BERT + LSTM for Volatility?**: Market volatility is driven by both language (news sentiment) and sequential data (GMP trends over time). Combining a transformer (BERT) for text embeddings with an RNN (LSTM) for time-series forecasting is a robust multimodal approach.
- **Model Accountability**: By implementing the public "AI Track Record" page, the application treats ML models as accountable entities, tracking predicted vs. actual outcomes to calculate real-world MAE and directional accuracy.

---

## 🧪 Testing

The backend includes a comprehensive `pytest` suite ensuring API reliability and authentication enforcement.

```bash
cd backend
python -m pytest tests/ -v
```

**Test Coverage Includes:**
- CRUD operations for IPOs.
- Authentication flow (Signup, Login, JWT validation).
- ML prediction endpoint mocking and validation.
- Model Accuracy calculation logic (verifying MAE and directional correctness math).
- Role-based access control (Admin vs. User routes).

---

## 📄 License
This project is for educational, academic research, and placement portfolio purposes.

## 🎉 Acknowledgments
Built as an advanced full-stack machine learning project demonstrating modern web architecture, financial data processing, and applied artificial intelligence.
