# Migration Guide: econcell → efdata

## Repository Changes

1. **Delete old repo**: `github.com/TheLustriVA/econcell`
2. **Create new repo**: `github.com/TheLustriVA/efdata`
3. **Update git remote**:
   ```bash
   git remote set-url origin git@github.com:TheLustriVA/efdata.git
   ```

## Local Directory Rename (Optional but Recommended)

```bash
cd ..
mv econcell efdata
cd efdata
```

## Fix Hardcoded Paths

Several files have hardcoded paths that need updating:

### Files with hardcoded paths:
- `src/econdata/parse_f_series.py`
- `src/econdata/econdata/spiders/upload_codes.py`
- `src/econdata/econdata/settings.py`
- `src/econdata/validation/*.py`
- `frontend/data/definitions.py`
- `frontend/api.py`

### Solution:
Use the new `src/config.py` module:

```python
# Instead of:
load_dotenv('/home/websinthe/code/econcell/.env')

# Use:
from src.config import PROJECT_ROOT, load_dotenv
load_dotenv()  # Already loaded in config.py

# Instead of:
download_dir = '/home/websinthe/code/econcell/src/econdata/downloads'

# Use:
from src.config import DOWNLOADS_DIR
download_dir = str(DOWNLOADS_DIR)
```

## Docker Updates

All docker services now use `efdata` prefix:
- `efdata-db` (was ausflow-db)
- `efdata-app` (was ausflow-app)
- `efdata-api` (was ausflow-api)

## Database Name

Default database name is now `efdata` (was `ausflow`)

## Python Package

- Package name: `efdata` (was `econcell`)
- Install with: `pip install -e .`

## GitHub Pages

After pushing to new repo:
1. Go to Settings → Pages
2. Source: Deploy from branch
3. Branch: main, folder: /docs
4. Site will be at: `https://thelustriya.github.io/efdata/`