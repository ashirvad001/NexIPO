# 🚀 Complete Application Setup & Run Guide

## Step-by-Step Instructions

### Step 1: Open Two PowerShell/Terminal Windows

**Window 1: Backend**
**Window 2: Frontend**

---

## 🔧 Window 1: Backend Setup & Run

```powershell
# Navigate to backend directory
cd "C:\Users\singh\Desktop\Project\Main 2\ipo-intelligence-platform\backend"

# Install dependencies (first time only)
pip install -r requirements.txt

# Create environment file (first time only)
copy .env.example .env

# Seed database with sample data (first time only)
python scripts/seed_data.py

# Start the backend server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for this message:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test backend:** Open http://localhost:8000/health in browser

---

## 🎨 Window 2: Frontend Setup & Run

```powershell
# Navigate to frontend directory
cd "C:\Users\singh\Desktop\Project\Main 2\ipo-intelligence-platform\frontend"

# Install dependencies (first time only - takes 2-3 minutes)
npm install

# Create environment file (first time only)
copy .env.example .env.local

# Start the frontend server
npm run dev
```

**Wait for this message:**
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

**Test frontend:** Open http://localhost:3000 in browser

---

## ✅ Verification Checklist

- [ ] Backend running: http://localhost:8000/health
- [ ] API docs accessible: http://localhost:8000/api/docs
- [ ] Frontend running: http://localhost:3000
- [ ] Dashboard loads with data

---

## 🐛 Troubleshooting

### Backend Issues

**Error: Module not found**
```powershell
cd backend
pip install -r requirements.txt
```

**Error: Database connection failed**
```powershell
# Check .env file exists
# Default uses SQLite, no setup needed
```

**Error: Port 8000 already in use**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend Issues

**Error: Cannot find module**
```powershell
cd frontend
rm -r node_modules
rm package-lock.json
npm install
```

**Error: Port 3000 already in use**
```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Error: Failed to fetch IPO data**
- Ensure backend is running on port 8000
- Check http://localhost:8000/health works
- Verify .env.local has: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`

---

## 🎯 Quick Commands (Copy & Paste)

### Backend (PowerShell Window 1)
```powershell
cd "C:\Users\singh\Desktop\Project\Main 2\ipo-intelligence-platform\backend"
python -m uvicorn main:app --reload
```

### Frontend (PowerShell Window 2)
```powershell
cd "C:\Users\singh\Desktop\Project\Main 2\ipo-intelligence-platform\frontend"
npm run dev
```

---

## 🌐 Access URLs

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/api/docs |
| Health Check | http://localhost:8000/health |

---

## 🛑 Stopping the Application

Press `Ctrl + C` in each PowerShell window to stop the servers.

---

## 📊 Test the Application

1. Open http://localhost:3000
2. You should see the dashboard
3. Click "Active IPOs" to see sample data
4. Click on an IPO card to view details
5. Try filters on "All IPOs" page

---

## 💡 Tips

- Keep both terminal windows open while using the app
- Backend must start before frontend for data to load
- First `npm install` takes 2-3 minutes
- Subsequent starts are much faster

---

**Ready? Open two PowerShell windows and follow the steps above!** 🚀
