# 🚀 Quick Start: Connecting ML Model to Laravel

## What We've Created

✅ **Flask API** (`ml_api.py`) - Serves your ML model via HTTP  
✅ **Laravel Service** - Pre-built PHP code to consume the API  
✅ **Test Scripts** - PowerShell scripts to verify everything works  
✅ **Test Page** - HTML page to test the API before Laravel integration  
✅ **Complete Documentation** - Step-by-step integration guide

---

## ⚡ 3-Minute Setup

### Step 1: Start the ML API (2 minutes)

Open PowerShell in this directory and run:

```powershell
# Install dependencies (first time only)
pip install -r requirements.txt

# Start the API
.\start_api.ps1
```

**Expected output:**
```
✓ Flask API running on http://127.0.0.1:5000
```

### Step 2: Test the API (30 seconds)

Open another PowerShell window and run:

```powershell
.\test_api.ps1
```

**Expected output:**
```
✅ Health Check: PASSED
✅ Options: PASSED
✅ Prediction: PASSED
```

### Step 3: Visual Test (30 seconds)

Open `test_page.html` in your browser:
- You should see "API Connected" with a green dot
- Fill the form and click "Predict Production"
- You should get a prediction result

**If all three steps work, you're ready for Laravel integration!**

---

## 🔗 Laravel Integration (10 minutes)

### Quick Copy-Paste Method

1. **Add to `config/services.php`:**
```php
'ml_api' => [
    'url' => env('ML_API_URL', 'http://127.0.0.1:5000'),
],
```

2. **Add to `.env`:**
```
ML_API_URL=http://127.0.0.1:5000
```

3. **Create Service:**
```bash
php artisan make:service CropPredictionService
```
Then copy code from `LARAVEL_INTEGRATION_GUIDE.md` Section 2.1

4. **Add Routes to `routes/api.php`:**
Copy the routes from `laravel_api_routes_example.php`

5. **Test from Laravel:**
```bash
php artisan tinker
```
```php
$service = new App\Services\CropPredictionService();
$health = $service->healthCheck();
print_r($health);
```

---

## 📝 Usage Example

### In Your Laravel Controller:

```php
use App\Services\CropPredictionService;

public function predict(Request $request)
{
    $service = new CropPredictionService();
    
    $result = $service->predict([
        'municipality' => $request->municipality,
        'farm_type' => $request->farm_type,
        'year' => $request->year,
        'month' => $request->month,
        'crop' => $request->crop,
        'area_planted' => $request->area_planted,
        'area_harvested' => $request->area_harvested,
        'productivity' => $request->productivity
    ]);
    
    return response()->json($result);
}
```

### From JavaScript/AJAX:

```javascript
fetch('/api/ml/predict', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-TOKEN': csrfToken
    },
    body: JSON.stringify({
        municipality: 'ATOK',
        farm_type: 'IRRIGATED',
        year: 2024,
        month: 1,
        crop: 'CABBAGE',
        area_planted: 10.5,
        area_harvested: 10.0,
        productivity: 15.5
    })
})
.then(res => res.json())
.then(data => {
    console.log('Predicted:', data.prediction.production_mt, 'mt');
});
```

---

## 🎯 API Endpoints You Can Use

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Check if API is running |
| `/api/available-options` | GET | Get dropdowns for form |
| `/api/predict` | POST | Single prediction |
| `/api/batch-predict` | POST | Multiple predictions |
| `/api/model-info` | GET | Model metadata |

---

## 🐛 Troubleshooting

### Problem: "Connection refused"
**Solution:** Make sure Flask API is running
```powershell
.\start_api.ps1
```

### Problem: "Module not found"
**Solution:** Install Python dependencies
```powershell
pip install -r requirements.txt
```

### Problem: "Model file not found"
**Solution:** Make sure model files exist in `model_artifacts/`
- Check that `best_rf_model.pkl` exists
- Re-run the Jupyter notebook if needed

### Problem: Laravel can't connect
**Solution:** Check `.env` file
```
ML_API_URL=http://127.0.0.1:5000  # ✓ Correct
ML_API_URL=http://localhost:5000   # ✗ Try 127.0.0.1 instead
```

---

## 📦 What's in Each File

| File | What It Does |
|------|--------------|
| `ml_api.py` | Flask API server (the main API) |
| `requirements.txt` | Python dependencies list |
| `start_api.ps1` | One-click API startup script |
| `test_api.ps1` | Automated API testing |
| `test_page.html` | Browser-based test interface |
| `LARAVEL_INTEGRATION_GUIDE.md` | Detailed Laravel guide (30+ pages) |
| `laravel_api_routes_example.php` | Ready-to-use API routes |
| `INTEGRATION_README.md` | Full documentation |

---

## 🔄 Typical Workflow

```
┌─────────────────┐
│ 1. Train Model  │ (Jupyter Notebook - DONE ✓)
│    in Notebook  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Export Model │ (model_artifacts/ - DONE ✓)
│    Files        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Start Flask  │ (.\start_api.ps1)
│    API          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Test API     │ (.\test_api.ps1 or test_page.html)
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Integrate    │ (Copy code to Laravel)
│    with Laravel │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. Users Make   │ (Via your Laravel app)
│    Predictions  │
└─────────────────┘
```

---

## 🎓 Learning Resources

- **For ML API**: Read `LARAVEL_INTEGRATION_GUIDE.md`
- **For Model Training**: See `UPDATED ML MODEL.ipynb`
- **For API Routes**: Check `laravel_api_routes_example.php`
- **For Testing**: Use `test_page.html`

---

## 💡 Pro Tips

1. **Keep Flask API Running**: The API must be running for Laravel to work
2. **Use Absolute Paths**: When deploying, use full paths to model files
3. **Add Logging**: Log all predictions for analysis
4. **Cache Options**: Cache available municipalities/crops in Laravel
5. **Queue Batch Jobs**: Use Laravel queues for bulk predictions
6. **Monitor Performance**: Track API response times

---

## 🚀 Production Deployment

For production, don't use Flask's development server. Use Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 ml_api:app
```

Or run as a Windows service (see full guide for details).

---

## ✅ Checklist

Before going live, ensure:

- [ ] Flask API starts without errors
- [ ] All test scripts pass (test_api.ps1)
- [ ] Test page shows predictions
- [ ] Laravel service can connect
- [ ] Routes are added to Laravel
- [ ] Environment variables are set
- [ ] Error handling is in place
- [ ] Predictions are logged
- [ ] API runs as a service (production)

---

## 🆘 Need Help?

1. **Check the logs**: Flask API shows errors in the terminal
2. **Read the docs**: `LARAVEL_INTEGRATION_GUIDE.md` has detailed troubleshooting
3. **Test individually**: Use `test_page.html` to isolate issues
4. **Verify model files**: Ensure all `.pkl` and `.json` files exist

---

## 📊 Model Performance

- **Type**: Random Forest Regressor
- **Accuracy**: 98.88% (CV Score: 0.9888)
- **Features**: 8 inputs (municipality, crop, area, etc.)
- **Output**: Production in metric tons
- **Training Date**: November 2, 2025

---

**You're all set! Start the API and begin integrating with Laravel! 🎉**
