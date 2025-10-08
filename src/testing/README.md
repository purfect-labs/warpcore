# WARPCORE Full UI System Testing

Comprehensive end-to-end testing suite for the complete WARPCORE system with System Orchestrator.

## 🎯 What This Tests

### System Orchestrator Integration
- **Data Layer** → Configuration, discovery, feature gates
- **Web Layer** → Templates, static assets, routing via controllers
- **API Layer** → Controllers, orchestrators, providers, middleware, executors

### Provider-Abstraction-Pattern (PAP) Architecture
- Direct FastAPI routes (no route abstractions)
- Controller → Orchestrator → Provider flow
- Complete request lifecycle validation
- Error handling and performance

### UI Components & User Flows
- WARPCORE branding validation (no APEX references)
- License management UI workflow
- Dashboard and agent cards interaction
- Real user scenarios with native events

## 🚀 Quick Start

### 1. Start WARPCORE Server
```bash
# From project root
python3 warpcore.py --web

# Or use the start script
bash start-warpcore.sh
```

Wait for the system orchestrator to complete initialization:
```
🌊 WARPCORE Provider-Abstraction-Pattern System Orchestrator
📊 Data Layer: ✅ INITIALIZED
🌐 Web Layer: ✅ INITIALIZED  
⚡ API Layer: ✅ INITIALIZED
✅ SYSTEM READY - Provider-Abstraction-Pattern Architecture Active
```

### 2. Run Tests

#### Using the test runner (recommended):
```bash
cd src/testing

# Run all tests
./run_warpcore_ui_tests.sh

# Run with browser visible
./run_warpcore_ui_tests.sh headed

# Interactive debugging
./run_warpcore_ui_tests.sh debug

# Test specific components
./run_warpcore_ui_tests.sh system      # System orchestrator tests
./run_warpcore_ui_tests.sh pap         # PAP architecture tests
./run_warpcore_ui_tests.sh license     # License UI flow tests
```

#### Using npm scripts:
```bash
cd src/testing

npm run test:warpcore                   # All tests
npm run test:warpcore:headed           # With browser visible
npm run test:warpcore:debug            # Interactive debugging
npm run test:warpcore:system           # System orchestrator only
npm run test:warpcore:pap              # PAP architecture only
```

#### Using Playwright directly:
```bash
cd src/testing

npx playwright test e2e/warpcore_full_ui_system.spec.js
npx playwright test e2e/warpcore_full_ui_system.spec.js --headed
npx playwright test e2e/warpcore_full_ui_system.spec.js --debug
```

## 📋 Test Categories

### 1. System Orchestrator Tests
- ✅ All three layers initialization
- ✅ PAP architecture integrity
- ✅ Component discovery (4 controllers, 5 orchestrators, 11 providers)
- ✅ Documentation and architecture endpoints

### 2. UI Component Tests  
- ✅ WARPCORE branding validation
- ✅ Static asset loading
- ✅ JavaScript error monitoring
- ✅ Responsive layout testing

### 3. License Management Flow
- ✅ License modal/interface access
- ✅ Form input validation
- ✅ PAP flow submission (Controller → Orchestrator → Provider)
- ✅ API endpoint integration

### 4. Dashboard & Agent Cards
- ✅ Dashboard layout validation
- ✅ Agent card interactions
- ✅ Hover and click behaviors
- ✅ Responsive design testing

### 5. API Integration Tests
- ✅ Core status endpoints (`/api/status`, `/api/license/status`)
- ✅ Authentication flow through PAP architecture
- ✅ License validation through PAP layers
- ✅ Documentation system validation

### 6. End-to-End User Flows
- ✅ Complete user landing workflow
- ✅ Navigation through interface
- ✅ System status checking
- ✅ Provider operations (GCP)
- ✅ Performance validation

### 7. Error Handling & Edge Cases
- ✅ Invalid API endpoint handling
- ✅ Invalid license operations
- ✅ Network delay tolerance  
- ✅ Large payload handling

### 8. Performance Tests
- ✅ System orchestrator startup timing
- ✅ PAP flow performance validation
- ✅ Multi-layer response times

## 🔧 Configuration

### Playwright Configuration
- **Base URL**: `http://127.0.0.1:8000`
- **Timeout**: 30 seconds (system orchestrator needs time)
- **Browser**: Chrome (system Chrome if available)
- **Viewport**: 1280x720 (responsive testing)
- **Screenshots**: On failure only
- **Video**: Retained on failure

### Test Expectations
- **System orchestrator startup**: < 15 seconds
- **PAP flow operations**: < 5 seconds
- **Multi-endpoint requests**: < 3 seconds
- **JavaScript errors**: < 5 (licensing system may have expected demo errors)

## 🐛 Troubleshooting

### Server Not Running
```
❌ WARPCORE server is not running!

To start the server, run:
  cd /path/to/warpcore
  python3 warpcore.py --web
```

### System Orchestrator Not Ready
Wait for all layers to initialize before running tests:
```
🌊 WARPCORE Provider-Abstraction-Pattern System Orchestrator
📊 Data Layer: ✅ INITIALIZED
🌐 Web Layer: ✅ INITIALIZED  
⚡ API Layer: ✅ INITIALIZED
```

### Test Failures
1. **System orchestrator timing**: Increase timeout or wait longer for initialization
2. **UI component selectors**: Update selectors in test if UI changed
3. **Network timeouts**: Check server performance and network connectivity

### Debug Mode
Use interactive debugging to step through tests:
```bash
./run_warpcore_ui_tests.sh debug
```

## 📁 Test Files

- **`e2e/warpcore_full_ui_system.spec.js`** - Main comprehensive test suite
- **`run_warpcore_ui_tests.sh`** - Test runner script with server validation
- **`playwright.config.js`** - Playwright configuration
- **`package.json`** - Dependencies and npm scripts

## 🎉 Expected Results

When all tests pass:
```
🎉 All WARPCORE UI tests passed!

✅ System Orchestrator: Data → Web → API layers tested
✅ Provider-Abstraction-Pattern: UI flow validated  
✅ License Management: UI components tested
✅ User Workflows: End-to-end flows verified
✅ Performance: System responsiveness validated

🌊 WARPCORE Full UI System: Ready for production! 🚀
```

## 🔄 Integration with CI/CD

The test suite follows WARPCORE patterns for automated testing:

1. **Multi-layer validation** as specified in rules
2. **Real user flows** with native events
3. **Performance validation** with timing expectations
4. **Doubt-driven testing** with multiple validation layers

Perfect for integration into your deployment pipeline!