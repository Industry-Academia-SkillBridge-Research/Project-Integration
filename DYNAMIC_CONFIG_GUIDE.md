# Dynamic Configuration System - Implementation Guide

## Overview

The SkillScope project now uses a **dynamic configuration system** that eliminates hardcoded port dependencies. The frontend automatically discovers backend service URLs at runtime through a configuration server.

### Key Benefits
- **No more port conflicts** - Change ports in one place
- **No frontend rebuilds needed** - Configuration fetched at runtime
- **Environment agnostic** - Works in dev, staging, and production
- **Graceful fallbacks** - Uses `.env` values if config server unavailable

---

## Architecture

### 1. Config Server (Backend)
- **File**: `config_server.py`
- **Port**: 8099 (configurable)
- **Purpose**: Serves service URLs to frontend
- **Endpoints**:
  - `GET /config` - Returns all service URLs
  - `GET /config/{service_name}` - Returns specific service URL
  - `GET /health` - Health check

### 2. Launcher (Backend) 
- **File**: `main.py` (updated)
- **Change**: Now launches config server as first service
- **Startup order**: Config Server → 5 other backends

### 3. Frontend Configuration Service
- **Files**: 
  - `configService.ts` - Fetches and caches config  
  - `useConfig.ts` - React hook for components
  - `dynamicEndpoints.ts` - Helper utilities
  - `api.ts` - Updated to use dynamic config

---

## How It Works

### Workflow

```
1. App starts → main.tsx
2. initializeConfig() called
3. configService fetches from http://localhost:8099/config
4. Config cached in memory
5. Components use getConfig() or useConfig hook
6. Requests routed to correct backend URL
```

### Fallback Mechanism

```
Try to fetch from config server
  ↓
[Success] → Use returned config
[Failure] → Use .env.local values
                ↓
         [No .env] → Use hardcoded defaults
```

---

## Usage in Components

### Option 1: Using the Hook (Recommended for React Components)

```typescript
import { useConfig } from '@/hooks/useConfig';

function MyComponent() {
  const { config, loading, error } = useConfig();
  
  if (loading) return <div>Loading...</div>;
  if (error) console.warn('Config error:', error);
  
  // Use config.AUTH_API, config.AGENT_API, etc.
  const authUrl = config?.AUTH_API;
  
  return <div>Auth API: {authUrl}</div>;
}
```

### Option 2: Using configService Directly

```typescript
import { getConfig, getServiceUrl } from '@/services/configService';

async function fetchData() {
  const authUrl = await getServiceUrl('AUTH_API');
  const response = await fetch(`${authUrl}/auth/me`);
  // ...
}
```

### Option 3: Using Dynamic Endpoint Builder

```typescript
import { buildEndpoint } from '@/utils/dynamicEndpoints';

async function uploadCV() {
  const endpoint = await buildEndpoint('/agent/run-from-pdf', 'agent');
  const response = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  });
}
```

---

## File Structure

```
NewFrontend/
├── .env.local (updated)
│   └── VITE_CONFIG_SERVER_URL=http://localhost:8099
│   └── VITE_*_API (fallback values)
├── src/
│   ├── main.tsx (updated - initializes config)
│   ├── services/
│   │   ├── configService.ts (NEW - fetches config)
│   │   ├── agentService.ts (use dynamicEndpoints)
│   │   ├── nilmaniService.ts (use dynamicEndpoints)
│   │   └── ... (other services)
│   ├── hooks/
│   │   └── useConfig.ts (NEW - React hook)
│   ├── utils/
│   │   └── dynamicEndpoints.ts (NEW - helpers)
│   ├── config/
│   │   └── api.ts (updated)
│   └── ... (other files)

Project-Integration/
├── main.py (updated - launches config server)
├── config_server.py (NEW - serves config)
├── login/ (backend)
├── Agent-Runtime/ (backend)
├── Nipuni_backend/ (backend)
├── Nilmani-backend/ (backend)
└── Advanced-Recommendation-System/ (backend)
```

---

## Modifying Service URLs

### Option A: Edit `config_server.py`

```python
SERVICES_CONFIG = ServiceConfig(
    AUTH_API="http://localhost:8182",         # Change here
    AGENT_API="http://localhost:8002",         # And here
    SKILL_API="http://localhost:8000",
    INTERVIEW_API="http://localhost:8188",
    RECOMMENDATION_API="http://localhost:8001",
)
```

### Option B: Use Environment Variables (Future)

```python
SERVICES_CONFIG = ServiceConfig(
    AUTH_API=os.getenv('AUTH_API_URL', 'http://localhost:8182'),
    # ... etc
)
```

### Option C: Edit `.env.local` (Fallback Only)

```env
VITE_AUTH_API=http://localhost:8182
VITE_AGENT_API=http://localhost:8002
# ... etc
```

---

## Services Using Dynamic Config

### Services That Need Updates

Service files should be updated to use `getServiceUrl()` or `buildEndpoint()`:

1. **agentService.ts** - Uses AGENT_API
   - Current: `http://localhost:8002` hardcoded
   - Change: Use `getAgentAPI()`

2. **nilmaniService.ts** - Uses INTERVIEW_API
   - Current: `http://localhost:8188` hardcoded  
   - Change: Use `getInterviewAPI()`

3. **nipuniService.ts** - Uses SKILL_API
   - Current: `http://localhost:8000` hardcoded
   - Change: Use `getSkillAPI()`

4. **authService.ts** (if exists) - Uses AUTH_API
   - Uses Auth Context currently

5. **recommendationService.ts** - Uses RECOMMENDATION_API

### Update Template for Service Files

**Before:**
```typescript
const API_BASE = 'http://localhost:8002';

export function getEndpoint(path: string) {
  return `${API_BASE}${path}`;
}
```

**After:**
```typescript
import { getAgentAPI } from '@/utils/dynamicEndpoints';

export async function getEndpoint(path: string) {
  const agentApi = await getAgentAPI();
  return `${agentApi}${path}`;
}
```

---

## Testing the System

### Test 1: Config Server Health

```bash
curl http://localhost:8099/health
# Expected: {"status":"ok","service":"config-server","version":"1.0.0"}
```

### Test 2: Get All Config

```bash
curl http://localhost:8099/config
# Expected: {"AUTH_API":"http://localhost:8182",...}
```

### Test 3: Get Specific Service

```bash
curl http://localhost:8099/config/agent
# Expected: {"service":"agent","url":"http://localhost:8002"}
```

### Test 4: Frontend Console

```javascript
// In browser console
import { getConfig } from '@/services/configService';
const config = await getConfig();
console.log(config);
```

---

## Troubleshooting

### Issue: "ERR_CONNECTION_REFUSED on port 8099"
- **Cause**: Config server not running
- **Solution**: Check `main.py` is running and launched config_server first

### Issue: "Failed to load resource: localhost:8099/config"
- **Cause**: CORS issue
- **Solution**: Config server has CORS enabled, check network tab for actual error

### Issue: "Config always null/undefined"
- **Cause**: configService not initialized
- **Solution**: Ensure `initializeConfig()` called in `main.tsx`

### Issue: Frontend still using hardcoded ports
- **Cause**: Service files haven't been updated
- **Solution**: Update service files to use `getServiceUrl()` functions

---

## Migration Checklist

- [x] Create `config_server.py`
- [x] Update `main.py` to launch config server
- [x] Create `configService.ts`
- [x] Create `useConfig.ts` hook
- [x] Create `dynamicEndpoints.ts` utilities
- [x] Update `api.ts` with dynamic config
- [x] Update `main.tsx` for config initialization
- [x] Update `.env.local` with config server URL
- [ ] Update `agentService.ts` (requires async refact)
- [ ] Update `nilmaniService.ts` (requires async refact)
- [ ] Update `nipuniService.ts` (requires async refact)
- [ ] Update other service files
- [ ] Test all modules end-to-end
- [ ] Update API routes for any hardcoded URLs
- [ ] Performance testing with config caching

---

## Future Enhancements

1. **Database-backed config** - Store in PostgreSQL/MongoDB
2. **Admin UI** - Dashboard to change ports live
3. **Service discovery** - Auto-detect running services
4. **Load balancing** - Multiple instances of same service
5. **Health monitoring** - Auto-check service availability

---

## Contributing

When adding new services or API calls:

1. Use `getServiceUrl()` instead of hardcoded URLs
2. Handle async config fetching
3. Add fallback for connection failures
4. Update this guide with new service info

---

**Defined**: March 25, 2026  
**Status**: Core system ready, services need individual updates
