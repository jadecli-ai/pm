# Environment Setup Guide

**Security**: API keys are now stored in `.env` file (NOT in version control)

---

## Quick Setup

### 1. Copy Example File
```bash
cp .env.example .env
```

### 2. Edit `.env` File
```bash
# Open in your editor
nano .env  # or vim, code, etc.
```

Add your actual API keys:
```env
GEMINI_API_KEY=AIzaSyDdPIAHciJa1zVcnu6rF_J4s1U7Bka5UMI
KIMI_API_KEY_v3=sk-kimi-0FTLazX3dtiF8djNaf5rWdFUqwyTBbbi708ODrAd1MBRDcmKclNlEjmbQR3SqrVm
```

### 3. Install Dependencies
```bash
pip install python-dotenv
# or
pip install -r requirements.txt
```

### 4. Verify Setup
```bash
python3 src/env_get.py
```

Expected output:
```
Environment Status:
============================================================
✓ dotenv_available: True
✓ env_file_loaded: True
✓ gemini_api_key_set: True
✓ kimi_api_key_set: True

Testing API key retrieval:
------------------------------------------------------------
✓ Gemini API Key: AIzaSyDdPIAHciJa1zVc...
✓ Kimi API Key: sk-kimi-0FTLazX3dtiF...
```

---

## Getting API Keys

### Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)
4. Add to `.env` as `GEMINI_API_KEY=your_key_here`

### Kimi API Key
1. Go to https://platform.moonshot.ai/
2. Sign up / Log in
3. Navigate to API Keys section
4. Create new key (starts with `sk-kimi-...`)
5. Add to `.env` as `KIMI_API_KEY_v3=your_key_here`

---

## Using in Code

### Python Code
```python
from src.env_get import get_gemini_api_key, get_kimi_api_key

# Get keys
gemini_key = get_gemini_api_key()
kimi_key = get_kimi_api_key()

# Use in your code
from lib.gemini.code_execution import GeminiCodeExecutor

tool = GeminiCodeExecutor()  # Automatically loads key from .env
result = tool.execute_code("print('Hello')")
```

### Command Line
```bash
# Keys are automatically loaded from .env
python3 experiments/test_setup.py

# No need to export manually!
```

---

## Security Features

### ✅ What's Protected
- `.env` file is in `.gitignore` (NOT committed to git)
- API keys loaded at runtime (not in code)
- Example file (`.env.example`) shows format without real keys
- Safe error messages if keys missing

### ❌ What NOT to Do
- ❌ Don't commit `.env` file to git
- ❌ Don't put keys directly in code
- ❌ Don't share `.env` file publicly
- ❌ Don't put keys in environment variables (use .env instead)

### ✅ What TO Do
- ✅ Keep `.env` file local only
- ✅ Use `.env.example` as template
- ✅ Add `.env` to `.gitignore`
- ✅ Rotate keys if exposed

---

## Troubleshooting

### Error: "GEMINI_API_KEY not set"
**Solution**:
1. Check `.env` file exists
2. Check key is on line: `GEMINI_API_KEY=your_key`
3. No spaces around `=`
4. Run `python3 src/env_get.py` to verify

### Error: "No module named 'dotenv'"
**Solution**:
```bash
pip install python-dotenv
```

### Keys Not Loading
**Debug**:
```python
python3 -c "from src.env_get import check_env_status; print(check_env_status())"
```

Shows which keys are set/missing.

---

## Advanced Configuration

### Optional Settings

Add to `.env` for additional features:

```env
# MLflow tracking (for performance monitoring)
MLFLOW_TRACKING_URI=http://localhost:5000

# Redis (for agent coordination)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Custom .env Location

```python
from src.env_get import load_env_file
from pathlib import Path

# Load from custom location
load_env_file(Path("/path/to/custom/.env"))
```

---

## CI/CD Integration

### GitHub Actions

Add secrets to GitHub repository:
1. Go to Settings → Secrets → Actions
2. Add `GEMINI_API_KEY`
3. Add `KIMI_API_KEY_v3`

In workflow file:
```yaml
- name: Run tests
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    KIMI_API_KEY_v3: ${{ secrets.KIMI_API_KEY_v3 }}
  run: python3 experiments/test_all.py
```

### Docker

In `docker-compose.yml`:
```yaml
services:
  app:
    env_file:
      - .env  # Load from .env file
```

Or pass explicitly:
```yaml
services:
  app:
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - KIMI_API_KEY_v3=${KIMI_API_KEY_v3}
```

---

## Migration from Environment Variables

If you previously used `export GEMINI_API_KEY=...`:

### Before (old way)
```bash
export GEMINI_API_KEY="your_key"
export KIMI_API_KEY_v3="your_key"
python3 experiments/test_setup.py
```

### After (new way)
```bash
# 1. Create .env file
echo "GEMINI_API_KEY=your_key" > .env
echo "KIMI_API_KEY_v3=your_key" >> .env

# 2. Run directly (keys auto-loaded)
python3 experiments/test_setup.py
```

**Benefits**:
- No need to export every time
- Keys persist across sessions
- Not in shell history
- Not exposed to child processes

---

## Summary

✅ **Setup Complete When:**
- `.env` file exists with your keys
- `python-dotenv` installed
- `python3 src/env_get.py` shows all keys loaded

✅ **Security Verified When:**
- `.env` in `.gitignore`
- `.env` NOT committed to git
- `git status` doesn't show `.env`

🚀 **Ready to Use!**
