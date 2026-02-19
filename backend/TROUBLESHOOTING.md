# 🔧 Troubleshooting: "Failed to fetch IPO data"

## Quick Fix

### Step 1: Start the Backend Server

```bash
cd backend
start.bat
```

Or manually:
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

### Step 2: Verify Server is Running

Open browser: http://localhost:8000/health

Should see:
```json
{
  "status": "healthy",
  "service": "NexIPO",
  "version": "1.0.0"
}
```

### Step 3: Check API Docs

Open: http://localhost:8000/api/docs

Test the `/api/v1/ipos/` endpoint

### Step 4: Seed Data (if empty)

```bash
cd backend
python seed_data.py
```

---

## Common Issues

### Issue 1: Port 8000 Already in Use

**Solution:**
```bash
# Windows - Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue 2: Database Empty

**Solution:**
```bash
python seed_data.py
```

### Issue 3: CORS Error (Frontend can't connect)

**Check `.env` file has:**
```
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Issue 4: Module Not Found

**Solution:**
```bash
pip install -r requirements.txt
```

---

## Verify Everything Works

Run this command:
```bash
check_status.bat
```

Or manually test:
```bash
curl http://localhost:8000/api/v1/ipos/
```

---

## Frontend Connection

If using frontend, ensure:

1. Backend running on `http://localhost:8000`
2. Frontend API URL points to `http://localhost:8000/api/v1`
3. CORS is configured correctly

---

## Still Having Issues?

1. Check backend logs in terminal
2. Check browser console (F12) for errors
3. Verify `.env` file exists and is configured
4. Ensure Python 3.11+ is installed
