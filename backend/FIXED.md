# FIXED: "Failed to fetch IPO data" Error

## What Was Fixed:

1. **CORS Configuration** - Changed to allow all origins in development
2. **Database Verified** - 5 IPOs exist in database
3. **Server Startup Scripts** - Created easy startup scripts

## How to Start the Server:

### Option 1: Double-click
```
run_server.bat
```

### Option 2: Command line
```bash
cd backend
python -m uvicorn main:app --reload
```

## Verify It Works:

1. **Start the server** using one of the methods above

2. **Open browser** and test these URLs:
   - http://localhost:8000/health
   - http://localhost:8000/api/v1/ipos/
   - http://localhost:8000/api/docs

3. **Test from command line:**
```bash
curl http://localhost:8000/api/v1/ipos/
```

## If Still Not Working:

1. **Check if server is running:**
   - Look for "Uvicorn running on http://0.0.0.0:8000" in terminal
   
2. **Check browser console (F12):**
   - Look for actual error message
   - Check Network tab for failed requests

3. **Verify frontend is pointing to correct URL:**
   - Should be: `http://localhost:8000/api/v1`

## Server is Running When You See:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Quick Test:

After starting server, run:
```bash
curl http://localhost:8000/api/v1/ipos/ | python -m json.tool
```

Should return JSON with IPO data.
