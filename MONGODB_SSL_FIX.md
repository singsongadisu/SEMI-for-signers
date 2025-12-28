# Quick MongoDB Atlas SSL Fix Guide

## Problem
SSL/TLS handshake error when connecting to MongoDB Atlas from Python

## Solutions (Choose One)

### ✅ Solution 1: Install MongoDB Locally (RECOMMENDED FOR TESTING)

1. Download MongoDB Community Server:
   https://www.mongodb.com/try/download/community

2. Install MongoDB (accept defaults)

3. Update your `.env` file:
   ```
   MONGODB_URI=mongodb://localhost:27017/semi_db
   ```

4. Start MongoDB service:
   ```powershell
   net start MongoDB
   ```

5. Restart your Flask app

---

### ✅ Solution 2: Fix Python SSL Certificates

Run these commands:

```powershell
# Update SSL certificates
pip install --upgrade certifi

# Set certificate path
$env:SSL_CERT_FILE = python -c "import certifi; print(certifi.where())"

# Restart app
python app.py
```

---

### ✅ Solution 3: Use MongoDB Atlas with Fixed Connection String

Your `.env` file should look like this:

```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/semi_db?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true
```

Replace:
- `username` - your MongoDB username
- `password` - your MongoDB password  
- `cluster` - your cluster name

---

### ✅ Solution 4: Disable SSL Verification (Development Only)

Already applied in app.py:
```python
mongoengine.connect(
    db=MONGODB_DB,
    host=MONGODB_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,  # Development only!
    serverSelectionTimeoutMS=5000
)
```

**WARNING**: Only use for development! Never in production!

---

## Current Status

✅ Updated `app.py` with SSL handling
✅ Upgraded `pymongo` and `certifi`
⏳ Need to choose a solution above

## Recommended Next Steps

1. **For Testing Voice Feature**: Use Local MongoDB (Solution 1)
2. **For Production**: Fix Atlas connection properly (Solution 3)
3. **Quick Test**: Try restarting app with current changes

---

## Verify Connection

Once MongoDB is running, verify with:

```powershell
python -c "import pymongo; print(pymongo.MongoClient('mongodb://localhost:27017/').server_info())"
```

---

Last Updated: 2024-12-24
