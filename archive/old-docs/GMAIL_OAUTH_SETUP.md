# 🔧 GMAIL OAUTH SETUP - IMPORTANT!

## ⚠️ Current Issue: Redirect URI Mismatch

You're getting "Error 400: redirect_uri_mismatch" because Google Cloud Console needs to be updated.

---

## ✅ Solution: Add Port 8002 to Google Console

### **Step 1: Go to Google Cloud Console**
Open: https://console.cloud.google.com/apis/credentials

### **Step 2: Find Your OAuth Client**
Look for the client ID starting with: `218670851183-dm7ca0hr9e2sr5s35gdvuko1an2k87eo`

### **Step 3: Edit the OAuth Client**
1. Click the **pencil icon** (Edit)
2. Scroll to **"Authorized redirect URIs"**
3. You should see existing URIs like:
   - `http://localhost:8000/auth/callback`
   
### **Step 4: Add the New URI**
Click **"ADD URI"** and add:
```
http://localhost:8002/auth/callback
```

### **Step 5: Save**
Click **SAVE** at the bottom

---

## 🔄 After Updating Google Console

1. **Close the current backend terminal** (the one with the error)
2. **Close the frontend terminal** too
3. **Restart the app:**
   ```
   Double-click: start_unified.bat
   ```
4. **Go to:** http://localhost:3001
5. **Click "Email Triage"**
6. **Click "Sign in with Google"**
7. **Should work now!** ✅

---

## 📝 What We Changed

- Backend now runs on **port 8002** (was 8001, originally 8000)
- Updated `.env` file
- Updated `start_unified.bat`
- Updated `next.config.js`

---

## 🆘 If You Can't Access Google Console

If you don't have access to Google Cloud Console right now, you have two options:

### Option A: Ask Someone Who Has Access
Share this URI with whoever manages your Google Cloud project:
```
http://localhost:8002/auth/callback
```

### Option B: Create New OAuth Credentials
1. Go to https://console.cloud.google.com/apis/credentials
2. Create new OAuth 2.0 Client ID
3. Add redirect URI: `http://localhost:8002/auth/callback`
4. Update the `.env` file with new Client ID and Secret

---

## ✅ After It Works

Once Gmail authentication works, you'll be able to:
- ✅ See your emails in the triage tab
- ✅ Use AI analysis on emails
- ✅ Extract action items
- ✅ Add tasks to your todo list
- ✅ Get daily digests

The **Delegations** tab already works without Gmail! 🌶️

---

**Need help?** Let me know what you see!
