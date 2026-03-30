# Test ML API
# This script tests if the ML API is working correctly

Write-Host "=== Testing ML API ===" -ForegroundColor Green
Write-Host ""

$apiUrl = "http://127.0.0.1:5000"

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$apiUrl/api/health" -Method Get
    Write-Host "  Status: $($response.status)" -ForegroundColor Green
    Write-Host "  Model Type: $($response.model_type)" -ForegroundColor Green
    Write-Host "  Training Date: $($response.training_date)" -ForegroundColor Green
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Make sure the Flask API is running (run start_api.ps1)" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 2: Get Available Options
Write-Host "Test 2: Get Available Options" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$apiUrl/api/available-options" -Method Get
    Write-Host "  Municipalities: $($response.municipalities.Count) available" -ForegroundColor Green
    Write-Host "  Farm Types: $($response.farm_types.Count) available" -ForegroundColor Green
    Write-Host "  Crops: $($response.crops.Count) available" -ForegroundColor Green
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: Make a Prediction
Write-Host "Test 3: Make a Prediction" -ForegroundColor Yellow
$testData = @{
    MUNICIPALITY = "ATOK"
    FARM_TYPE = "IRRIGATED"
    YEAR = 2024
    MONTH = 1
    CROP = "CABBAGE"
    Area_planted_ha = 10.5
    Area_harvested_ha = 10.0
    Productivity_mt_ha = 15.5
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$apiUrl/api/predict" -Method Post -Body $testData -ContentType "application/json"
    Write-Host "  Success: $($response.success)" -ForegroundColor Green
    Write-Host "  Predicted Production: $($response.prediction.production_mt) mt" -ForegroundColor Green
    Write-Host "  Expected from Productivity: $($response.prediction.expected_from_productivity) mt" -ForegroundColor Green
    Write-Host "  Difference: $($response.prediction.difference) mt" -ForegroundColor Green
    Write-Host "  Confidence Score: $($response.prediction.confidence_score)" -ForegroundColor Green
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== All Tests Passed ===" -ForegroundColor Green
Write-Host ""
Write-Host "The ML API is working correctly and ready to integrate with Laravel!" -ForegroundColor Cyan
