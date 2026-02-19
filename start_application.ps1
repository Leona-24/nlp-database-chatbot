Write-Host "Starting NLP Chatbot Application..." -ForegroundColor Cyan

# Check for Backend
Write-Host "Launching Backend (FastAPI)..." -ForegroundColor Green
# Using python directly to start uvicorn with explicit host binding
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory ".\nlp_backend"

# Wait a moment for backend to initialize
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if Backend is up
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -Method Head -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "Backend is responding!" -ForegroundColor Green
    }
}
catch {
    Write-Host "Warning: Backend might not be responding yet." -ForegroundColor Yellow
}

# Start Frontend
Write-Host "Launching Frontend (React/Vite)..." -ForegroundColor Green
# On Windows, using npm.cmd is more reliable with Start-Process
Start-Process -NoNewWindow -FilePath "npm.cmd" -ArgumentList "run dev -- --host 127.0.0.1" -WorkingDirectory ".\nlp_frontend"

Write-Host "Application started!" -ForegroundColor Cyan
Write-Host "------------------------------------"
Write-Host "Backend API:   http://127.0.0.1:8000/docs"
Write-Host "Frontend App:  http://127.0.0.1:3000"
Write-Host "------------------------------------"
Write-Host "If the frontend doesn't load immediately, please wait a few seconds and refresh."

# Keep window open
Read-Host "Press Enter to exit and stop servers..."
