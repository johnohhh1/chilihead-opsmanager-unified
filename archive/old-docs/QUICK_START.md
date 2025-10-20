# 🚀 QUICK START GUIDE

## Setup Instructions

### Step 1: Run the Setup Script
Double-click `setup.bat` to:
- Copy all files from openinbox-opsmanager
- Create Python virtual environment
- Install all dependencies

**This will take about 5-10 minutes.**

### Step 2: Configure Environment
1. Copy your `.env` file from `openinbox-opsmanager\server` to `chilihead-opsmanager-unified\server`
   - OR create a new one from `.env.example`

### Step 3: Launch the App
Double-click `start_unified.bat` to launch both:
- Backend server on http://localhost:8000
- Frontend on http://localhost:3001

### Step 4: Push to GitHub
When ready, double-click `push_to_github.bat` to:
- Initialize git repo
- Add all files
- Commit changes
- Push to https://github.com/johnohhh1/chilihead-opsmanager-unified

---

## What's Been Done

✅ Created new project structure
✅ Set up README and .gitignore
✅ Created helper scripts for setup, launch, and git
✅ Ready to copy files from both projects

---

## Next Steps

After running `setup.bat`, we'll:

1. **Copy ChiliHead Components** (30 min)
   - Copy delegation components from Auburn_Hills_Unified
   - Convert from .js to .tsx
   - Update imports for Next.js

2. **Add Delegations Backend** (45 min)
   - Create delegations API routes
   - Add delegation state management
   - Connect to existing state system

3. **Wire Up "Delegate This" Button** (30 min)
   - Add button in email triage
   - Pre-fill delegation form from email data
   - Test workflow

4. **Add Navigation Tab** (15 min)
   - Add "Delegations" to header
   - Create delegations pages
   - Set up routing

**Total Time: ~2 hours after setup completes**

---

## Important Files

- `setup.bat` - One-time setup (run first!)
- `start_unified.bat` - Launch the app
- `push_to_github.bat` - Commit and push to GitHub
- `README.md` - Full documentation
- `.gitignore` - Protects sensitive data

---

## Troubleshooting

### Setup fails
- Make sure Python 3.11+ is installed
- Make sure Node.js 18+ is installed
- Check that openinbox-opsmanager folder exists

### Backend won't start
- Check that .env file exists in server folder
- Make sure virtual environment is activated
- Check that all dependencies installed

### Frontend won't start
- Run `npm install` in client folder
- Check that node_modules folder exists

---

## Need Help?

Just ask! I'll walk you through each step.
