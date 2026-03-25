# Service Files - Dynamic Config Update Guide

## Status: In Progress

With the new dynamic configuration system, all service files automatically benefit from the config server by using the ENDPOINTS object from `api.ts`.

### Automatic Benefits
✅ **All services using `ENDPOINTS`** automatically get fallback config  
✅ **authService/AuthContext** - Uses configService directly  
✅ **agentService** - Uses ENDPOINTS  
✅ **nilmaniService** - Uses configService directly  

### Services Already Updated

#### 1. AuthContext (src/contexts/AuthContext.tsx)
- ✅ Uses `AUTH_API` constant
- ✅ Fetches from configService
- Routes: `/auth/me`, `/auth/login/google`, `/candidate/me`

#### 2. nilmaniService (src/services/nilmaniService.ts)
- ✅ Uses `VITE_NILMANI_API_URL` env
- ✅ Falls back to port 8188
- Routes: `/api/upload-jd`, `/api/start-interview`

#### 3. agentService (src/services/agentService.ts)
- ✅ Uses ENDPOINTS from api.ts
- ✅ Falls back to port 8002
- Routes: `/agent/run`, `/agent/run-from-pdf`, `/runtime/skill-explain`

### Services Needing Updates (Minor)

#### nipuniService.ts
```typescript
// Current
const NIPUNI_API_BASE = import.meta.env.VITE_NIPUNI_API_URL || 'http://localhost:8000';

// Already works with dynamic config!
// - If env var set, uses it
// - Falls back to 8000
// - Can be overridden by config server via .env
```

#### profileService.ts
```typescript
// Currently uses
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8182';

// OK for now - uses fallback mechanism
```

### Services Already Using getConfig()

None yet - but can be added if needed.

---

## Why Current Setup Works

### Configuration Resolution Order
```
1. Config Server (/config endpoint)
   ↓ (if available, used by getConfig())
2. Environment Variables (.env.local)
   ↓ (used by service files)
3. Hardcoded Defaults
   ↓ (in service files as fallback)
```

### Example Flow: User uploads CV and runs analysis

```
1. User clicks "Run Analysis"
2. frontend → agentService.runAgentPipelineFromPDF()
3. agentService uses ENDPOINTS.AGENT.RUN_FROM_PDF
4. ENDPOINTS resolved from api.ts
5. api.ts uses API_CONFIG.AGENT_RUNTIME_API
6. API_CONFIG_FALLBACK = env var from .env.local
7. .env.local has VITE_AGENT_API=http://localhost:8002
8. Request sent to http://localhost:8002/agent/run-from-pdf ✅
```

### If Port Changes (e.g., 8002 → 9002)

**Scenario 1: Using Config Server**
```
1. Edit config_server.py → AGENT_API="http://localhost:9002"
2. Restart main.py
3. Frontend automatically uses new port (on next request)
4. No rebuild needed ✅
```

**Scenario 2: Config Server Down**
```
1. Edit .env.local → VITE_AGENT_API=http://localhost:9002
2. Reload page
3. Uses new port from environment ✅
```

**Scenario 3: Neither Available**
```
1. Falls back to hardcoded port in service files
2. Works but requires code change ❌
```

---

## Future Service Updates (Optional)

### For Fully Dynamic Runtime Configuration

**Example: Update agentService to use getServiceUrl()**

```typescript
// src/services/agentService.ts

import { getServiceUrl } from '@/services/configService';

export async function runAgentPipelineFromPDF(
  file: File,
  roleKey: string,
  topK: number = 25,
  includeXai: boolean = true
): Promise<AgentRunResponse> {
  
  // Get endpoint dynamically
  const agentApi = await getServiceUrl('AGENT_API');
  const params = new URLSearchParams({
    role_key: roleKey,
    top_k: topK.toString(),
    include_xai: includeXai.toString(),
  });
  
  const url = `${agentApi}/agent/run-from-pdf?${params.toString()}`;
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('role_key', roleKey);
  
  const response = await fetch(url, {
    method: 'POST',
    headers: REQUEST_HEADERS.MULTIPART,
    body: formData,
  });
  
  // ... rest of code
}
```

**Advantages:**
- ✅ Real-time config changes (no page reload)
- ✅ No build step needed
- ⚠️ Adds async/await complexity
- ⚠️ Slight performance overhead (but cached)

**Disadvantages:**
- ❌ All functions become async
- ❌ More code changes needed

---

## Verification Checklist

Run these to verify everything works:

### 1. Config Server Responding
```bash
curl http://localhost:8099/config
# Should see: {"AUTH_API":"http://localhost:8182",...}
```

### 2. Frontend Can Fetch Config
```javascript
// In browser console at http://localhost:8080
import { getConfig } from '/src/services/configService.ts';
const cfg = await getConfig();
console.log(cfg);
```

### 3. Services Working with Fallback
- Open http://localhost:8080/modules
- Click on any module (should work with fallback ports)
- Check Network tab - requests to correct ports

### 4. Test Each Module
- [ ] Landing page loads
- [ ] Login with Google OAuth
- [ ] Upload CV in Analysis
- [ ] Run analysis pipeline
- [ ] Change role selection
- [ ] Upload JD for interview
- [ ] Start interview session
- [ ] Skill gap analysis workflow

---

## Troubleshooting Service Issues

### Issue: "Failed to fetch from localhost:8000"
- Check: Skill Backend running on 8000?
- Fix: `python main.py` from Project-Integration folder

### Issue: "Auth API not responding"
- Check: Login Backend running on 8182?
- Fix: Verify port in `main.py` matches 8182

### Issue: "GeminiAPI error" on interview start
- Check: Nilmani backend has GEMINI_API_KEY set
- Fix: Verify env var in Nilmani-backend/.env

### Issue: "Neo4j connection failed"
- Check: NEO4J_URI set correctly
- Fix: Verify credentials in backend .env files

---

## Next Steps

1. ✅ Core dynamic config system implemented
2. ✅ All backends launch from one main.py
3. ✅ Config server running on port 8099
4. ✅ Frontend can fetch config at startup
5. ⏳ Test all workflows end-to-end
6. ⏳ Optional: Update services for real-time config
7. ⏳ Optional: Add admin UI for config management

---

**Last Updated**: March 25, 2026  
**System Status**: Ready for comprehensive testing
