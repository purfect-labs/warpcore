# Git Repository File Analysis

## Summary
**Total tracked files: 284** (too many!)

## Breakdown by Directory:

### 🔥 Major Contributors (should be reduced):
- **src/**: 211 files
  - `src/web/`: 72 files (38 static assets, 16 testing files)
  - `src/agency/`: 53 files (32 web files - duplicates?)
  - `src/api/`: 47 files
  - `src/license_server/`: 13 files
  - `src/testing/`: 11 files
  - `src/data/`: 11 files

### 🚨 Suspicious Files to Review:
- **native/**: 23 files (build artifacts, icons, electron files)
- **linux-native/**: 5 files (more build artifacts)
- **electron/**: 4 files (electron specific)

### 📝 Documentation (reasonable):
- **docs/**: 16 files
- **sales/**: 8 files

## 🎯 Recommended .gitignore Additions:

### Static Assets & Build Artifacts:
```
# Static web assets (should be built/generated)
src/web/static/
src/agency/web/

# Native build artifacts  
native/
linux-native/
electron/

# Testing artifacts
src/*/testing/
test_*.py
*.out

# Generated icons and assets
*.icns
*.png (selectively)
create_icon.py
```

### Duplicated Web Assets:
- `src/agency/web/` (32 files) seems to duplicate `src/web/` functionality
- Both contain dashboard, CSS, JS files

## 🧹 Immediate Actions Needed:

1. **Remove build artifacts from tracking**:
   - `native/` directory (23 files)
   - `linux-native/` directory (5 files)
   - `electron/` directory (4 files)

2. **Remove testing artifacts**:
   - `src/web/testing/` (16 files)
   - Individual test files at root

3. **Review duplicated web assets**:
   - `src/agency/web/` vs `src/web/static/`

4. **Remove generated assets**:
   - Icon files, generated images

## Expected Result:
- **From 284 files → ~80-120 files** (60-70% reduction)
- Core Python code: ~40-60 files
- Essential config/docs: ~20-30 files
- Templates/static (essential only): ~20-30 files
