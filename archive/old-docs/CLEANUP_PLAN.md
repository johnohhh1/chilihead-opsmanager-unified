# Project Cleanup Plan

## Proposed Structure

```
chilihead-opsmanager-unified/
├── 📄 README.md                    ← KEEP (main docs)
├── 🚀 START_EVERYTHING.bat         ← KEEP (main startup)
├── 🐳 docker-compose.yml           ← KEEP (database)
│
├── 📁 client/                      ← Frontend (keep as-is)
├── 📁 server/                      ← Backend (keep as-is)
├── 📁 docs/                        ← Current project docs
│
├── 📁 scripts/                     ← Active utility scripts
│   ├── start_database.bat
│   ├── stop_database.bat
│   ├── start_unified.bat
│   └── run_migrations.bat
│
└── 📁 archive/                     ← Old stuff (out of sight)
    ├── old-docs/                   ← Historical documentation
    ├── test-scripts/               ← Test/debug scripts
    └── old-scripts/                ← Unused batch files
```

## Files to Keep in Root (Clean View)
- `README.md` - Main documentation
- `START_EVERYTHING.bat` - Quick start script
- `docker-compose.yml` - Database setup
- `.gitignore` - Git config

## Files to Move

### → scripts/ (Active utilities)
- `start_database.bat`
- `stop_database.bat`
- `start_unified.bat`
- `run_migrations.bat`
- `push_to_github.bat`

### → archive/old-docs/
- `DATABASE_SETUP.md`
- `DEBUG_NEEDED.md`
- `GMAIL_OAUTH_SETUP.md`
- `HANDOFF_DOCUMENT.md`
- `MANUAL_FIXES.md`
- `NEXT_SESSION_START_HERE.md`
- `NEXT_STEPS.md`
- `PHASE1_COMPLETE.md`
- `QUICK_START.md`
- `STATUS.md`
- `STEP1_COMPLETE.md`
- `STEP2_COMPLETE.md`
- `URGENT_FIXES.md`

### → archive/test-scripts/
- `test_api.bat`
- `test_backend.bat`
- `test_database.bat`
- `apply_fixes.bat`
- `fix_markdown.bat`

### → archive/old-scripts/
- `setup.bat`
- `setup_alembic.bat`
- `start_backend_8001.bat`
- `EMERGENCY_RESTORE.bat`
- `force_restart_frontend.bat`
- `install_db_deps.bat`
- `exclude.txt`

## After Cleanup - Root Directory Will Show:
```
chilihead-opsmanager-unified/
├── README.md
├── START_EVERYTHING.bat
├── docker-compose.yml
├── .gitignore
├── client/
├── server/
├── docs/
├── scripts/
└── archive/
```

Clean and professional! 🎯

## Note
All files are preserved in `archive/` - nothing deleted, just organized!
