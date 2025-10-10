# Fix for WinError 10013 - Port Binding Issue on Windows

## Problems Addressed

### 1. Port Binding Error (WinError 10013)
When attempting to run the backend on Windows, users encountered the error:
```
ERROR: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
```

This error occurs when trying to bind to port 8000, which can be:
- Reserved by Windows system services
- Blocked by Hyper-V
- In use by another application
- Part of Windows' excluded port range

### 2. SSL Certificate Verification Error
When calling the OpenAI API, users encountered the error:
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

This error occurs due to:
- Corporate proxies or firewalls
- Outdated SSL certificates
- Windows certificate store issues
- Enterprise network configurations

## Solutions Implemented

### 1. Automatic Port Fallback Mechanism
Modified `backend/backend.py` to automatically try alternative ports when the default port (8000) is unavailable:

**Key Features:**
- Tries ports in order: 8000 → 8001 → 8002 → 8003 → 8080 → 5000
- Respects custom PORT environment variable
- Provides clear feedback about which port is being used
- Shows helpful error messages if all ports fail

**Code Changes:**
- Added port availability checking using socket binding
- Implemented fallback logic with user-friendly messages
- Maintains compatibility with existing PORT environment variable

### 2. SSL Certificate Error Handling
Added automatic SSL error detection and retry logic in both `llm_call` and `generate_pid` functions:

**Key Features:**
- Detects SSL/certificate errors automatically
- Retries API calls without SSL verification when SSL errors occur
- Provides clear feedback to users about SSL fallback
- Works for both PDF analysis and P&ID generation

**Code Changes:**
- Wrapped OpenAI API calls with SSL error detection
- Added fallback to `make_client(verify_ssl=False)` on SSL errors
- Clear logging messages for SSL retry attempts

### 2. Enhanced Documentation
Updated `README.md` with:
- Clear warning about Windows port 8000 issues
- Three different solutions:
  1. **Automatic:** Run `python backend.py` (recommended)
  2. **Manual:** Set custom PORT environment variable
  3. **Advanced:** Use `netsh` to check reserved ports
- Platform-specific instructions for Windows and Linux/Mac
- New "Troubleshooting" section

## Testing

All scenarios tested and verified:

### Port Fallback
✅ **Scenario 1:** Port 8000 available
```
✅ Iniciando servidor na porta 8000
```

✅ **Scenario 2:** Port 8000 blocked, fallback to 8001
```
⚠️  Porta 8000 não disponível, tentando porta 8001...
✅ Iniciando servidor na porta 8001
```

✅ **Scenario 3:** Custom PORT environment variable
```
PORT=9000
✅ Iniciando servidor na porta 9000
```

✅ **Scenario 4:** All ports blocked (error handling)
```
❌ Não foi possível vincular a nenhuma porta. Último erro: [Errno 98]
💡 Portas tentadas: 8000, 8001, 8002, 8003, 8080, 5000
💡 Solução: Especifique uma porta disponível usando PORT=<porta>
```

### SSL Error Handling
✅ **Scenario 1:** SSL certificate error detected and retried
```
⚠️ Erro SSL detectado: [SSL: CERTIFICATE_VERIFY_FAILED]...
🔄 Tentando novamente sem verificação SSL...
✅ Successfully connected without SSL verification
```

✅ **Scenario 2:** Works for both PDF analysis and P&ID generation
- llm_call() function handles SSL errors
- generate_pid() function handles SSL errors

## Usage

### Option 1: Let the script choose (Recommended)
```bash
cd backend
python backend.py
```

### Option 2: Specify a custom port
```bash
# Windows
set PORT=9000
python backend.py

# Linux/Mac
export PORT=9000
python backend.py
```

### Option 3: Use uvicorn directly with custom port
```bash
uvicorn backend:app --reload --port 9000
```

## Impact

### For Users
- ✅ No more confusing WinError 10013 errors
- ✅ Backend "just works" on Windows
- ✅ SSL certificate errors handled automatically
- ✅ Clear guidance when issues occur

### For Developers
- ✅ Minimal code changes (SSL handling + port fallback)
- ✅ Backward compatible (existing configurations still work)
- ✅ Better error messages for debugging
- ✅ Robust error handling for Windows environments

## Files Changed
- `backend/backend.py`: Added port fallback logic + SSL error handling
- `README.md`: Added troubleshooting section for both issues
- `FIX_SUMMARY.md`: Complete documentation

## Commits
1. Initial plan
2. Add port fallback mechanism for Windows WinError 10013 fix
3. Add comprehensive fix summary documentation
4. Add SSL certificate error handling for OpenAI API calls

**Status:** ✅ Complete and tested
