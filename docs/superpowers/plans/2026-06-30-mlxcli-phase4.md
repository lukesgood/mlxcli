# MLX-CLI Phase 4 (v1.1) Implementation Plan - Production Hardening

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden MLX-CLI for production use with performance optimization, security hardening, stability improvements, and enterprise features.

**Architecture:** Build on Phase 1-3 foundation. Enhance: (1) Performance optimization (model caching, async operations), (2) Security hardening (input validation, sandboxing), (3) Stability (error recovery, retry logic), (4) Enterprise features (user profiles, audit logging, monitoring).

**Tech Stack:** Python 3.10+, existing Phase 1-3 deps + redis (optional caching), prometheus (metrics), structlog (structured logging).

## Global Constraints

- Python >= 3.10
- Backward compatible with Phase 1-3 (all 870+ tests must still pass)
- Production-ready code quality (no breaking changes)
- Security best practices (OWASP)
- Performance target: <1s model load (cached), <3s first token generation
- Uptime target: 99.9% availability for long-running sessions
- No external API keys in logs/config files
- TDD approach for all new code

---

## File Structure

### New Core Modules

```
mlxcli/
├── performance/
│   ├── __init__.py
│   ├── cache_manager.py        # Model/response caching
│   ├── async_executor.py       # Async operation support
│   └── profiler.py             # Performance monitoring
├── security/
│   ├── __init__.py
│   ├── input_validator.py      # Input sanitization
│   ├── audit_logger.py         # Audit trail
│   └── rate_limiter.py         # Rate limiting
├── stability/
│   ├── __init__.py
│   ├── retry_policy.py         # Retry with exponential backoff
│   ├── health_check.py         # System health monitoring
│   └── state_manager.py        # Session recovery
├── enterprise/
│   ├── __init__.py
│   ├── user_profile.py         # User settings & preferences
│   ├── config_manager.py       # Advanced configuration
│   └── metrics.py              # Prometheus metrics
```

### Test Files

```
tests/
├── test_cache_manager.py
├── test_input_validator.py
├── test_audit_logger.py
├── test_retry_policy.py
├── test_health_check.py
├── test_async_executor.py
├── test_rate_limiter.py
├── test_user_profile.py
├── test_metrics.py
├── test_phase4_integration.py
└── test_performance_benchmarks.py
```

---

## Task Sequence

### Task 1: Performance Optimization - Model Caching

**Files:**
- Create: `mlxcli/performance/cache_manager.py`
- Create: `tests/test_cache_manager.py`
- Modify: `mlxcli/backends/base.py` (add cache hooks)

**Interfaces:**
- Produces: `CacheManager` class with:
  - `cache_get(key)` - Retrieve cached model or response
  - `cache_set(key, value, ttl)` - Store in cache
  - `cache_clear()` - Clear cache
  - `get_cache_stats()` - Cache hit/miss ratio
- Cache backends: Memory (default), SQLite (persistent), Redis (optional)

### Task 2: Security - Input Validation & Sanitization

**Files:**
- Create: `mlxcli/security/input_validator.py`
- Create: `tests/test_input_validator.py`
- Modify: `mlxcli/cli.py` (add validation hooks)

**Interfaces:**
- Produces: `InputValidator` class with:
  - `validate_prompt(text)` - Check length, encoding, injection attempts
  - `sanitize_input(text)` - Remove dangerous patterns
  - `validate_file_path(path)` - Prevent directory traversal
- Max prompt length: 4096 chars
- Blocked patterns: null bytes, control chars, path traversal

### Task 3: Security - Audit Logging

**Files:**
- Create: `mlxcli/security/audit_logger.py`
- Create: `tests/test_audit_logger.py`
- Modify: `mlxcli/session.py` (log all actions)

**Interfaces:**
- Produces: `AuditLogger` class with:
  - `log_action(action, user, resource, result)` - Log user action
  - `get_audit_trail(session_id)` - Retrieve session audit log
  - `export_audit_log(format)` - Export as JSON/CSV
- Logged events: model load, inference, file access, tool execution
- No sensitive data in logs (API keys, model outputs truncated)

### Task 4: Stability - Retry Logic & Exponential Backoff

**Files:**
- Create: `mlxcli/stability/retry_policy.py`
- Create: `tests/test_retry_policy.py`
- Modify: `mlxcli/backends/base.py` (wrap inference)

**Interfaces:**
- Produces: `RetryPolicy` class with:
  - `execute_with_retry(func, max_retries=5, backoff=exponential)` - Retry failed operations
  - `calculate_backoff(attempt)` - Exponential backoff: 1s, 2s, 4s, 8s, 16s
- Retriable errors: Network timeouts, temporary HF API errors
- Non-retriable: Auth errors, invalid models, permission denied

### Task 5: Stability - Health Checks & Recovery

**Files:**
- Create: `mlxcli/stability/health_check.py`
- Create: `mlxcli/stability/state_manager.py`
- Create: `tests/test_health_check.py`

**Interfaces:**
- Produces: `HealthCheck` class with:
  - `check_model_loaded()` - Verify model state
  - `check_disk_space()` - Monitor free space
  - `check_memory_usage()` - Monitor RAM
  - `get_health_status()` - Return overall health
- Produces: `StateManager` for session recovery on crash
- Checkpoints: Save session state every 5 minutes
- Recovery: Auto-restore last session on startup

### Task 6: Performance - Async Operations

**Files:**
- Create: `mlxcli/performance/async_executor.py`
- Modify: `mlxcli/backends/base.py` (async generate)
- Create: `tests/test_async_executor.py`

**Interfaces:**
- Produces: `AsyncExecutor` for:
  - `async_generate(prompt, timeout=30)` - Non-blocking inference
  - `async_load_model(name)` - Parallel model loading
- Enable background inference for chat continuations
- Thread pool: 4 workers (configurable)

### Task 7: Security - Rate Limiting

**Files:**
- Create: `mlxcli/security/rate_limiter.py`
- Create: `tests/test_rate_limiter.py`
- Modify: `mlxcli/cli.py` (apply limits)

**Interfaces:**
- Produces: `RateLimiter` with:
  - `check_limit(key)` - Allow/deny request
  - `get_quota(key)` - Current usage
- Limits: 100 requests/min per session, 10 concurrent inferences
- Headers: X-RateLimit-Remaining, X-RateLimit-Reset

### Task 8: Enterprise - User Profiles & Settings

**Files:**
- Create: `mlxcli/enterprise/user_profile.py`
- Create: `mlxcli/enterprise/config_manager.py`
- Create: `tests/test_user_profile.py`

**Interfaces:**
- Produces: `UserProfile` class with:
  - `get_preference(key)` - User settings
  - `set_preference(key, value)` - Save settings
  - `get_default_model()` - User's preferred model
- Settings: theme, auto-save, default model, log level
- Storage: `~/.mlxcli/profiles/{username}.json`

### Task 9: Monitoring & Metrics

**Files:**
- Create: `mlxcli/enterprise/metrics.py`
- Create: `tests/test_metrics.py`
- Modify: `mlxcli/cli.py` (instrument code)

**Interfaces:**
- Produces: `MetricsCollector` for:
  - `record_inference_time(duration)` - Model latency
  - `record_token_count(tokens)` - Throughput
  - `get_metrics_summary()` - Counters/gauges
- Export: Prometheus format (`GET /metrics` endpoint)
- Metrics: inference_time_ms, model_load_time_ms, error_rate, cache_hit_ratio

### Task 10: Integration Testing & Polish

**Files:**
- Create: `tests/test_phase4_integration.py`
- Create: `tests/test_performance_benchmarks.py`
- Update: Documentation (README, CLAUDE.md)
- Code quality: black, ruff, mypy

**Interfaces:**
- Comprehensive end-to-end tests for all Phase 4 features
- All 870+ existing tests still passing
- Performance benchmarks: model load, inference, cache ops
- Documentation: deployment guide, performance tuning, monitoring

---

## Summary

**Phase 4 (v1.1) Completion Goals**

### Features to Deliver

- ✅ Model caching (in-memory + persistent)
- ✅ Input validation & sanitization
- ✅ Audit logging (all user actions)
- ✅ Retry logic with exponential backoff
- ✅ Health checks & session recovery
- ✅ Async/non-blocking operations
- ✅ Rate limiting per session
- ✅ User profiles & preferences
- ✅ Prometheus metrics export
- ✅ Performance benchmarks
- ✅ Comprehensive testing (100+ new tests)
- ✅ Production deployment guide

### Test Coverage Target

- Phase 1: 242 tests
- Phase 2: 232 tests
- Phase 3: 396 tests
- Phase 4: 120+ tests
- **Total: 1000+ tests**

### Success Criteria

- ✅ Model load time <1s (cached)
- ✅ First token <3s (99th percentile)
- ✅ 99.9% uptime for sessions
- ✅ Zero security vulnerabilities (OWASP)
- ✅ All 870+ prior tests passing
- ✅ Production-ready monitoring
- ✅ User profile customization works
- ✅ Audit trail complete & queryable
- ✅ Performance benchmarks documented
- ✅ Deployment guide provided

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|------------|
| Model load (cached) | <1s | 95th percentile |
| First token (room temp) | <3s | 99th percentile |
| Inference (cached response) | <100ms | p99 |
| Memory usage | <2GB | Long-running session |
| Cache hit ratio | >80% | After warm-up |

---

## Security Checklist

- [ ] Input validation on all user inputs
- [ ] No sensitive data in logs
- [ ] Rate limiting enabled
- [ ] Audit trail complete
- [ ] File path traversal prevented
- [ ] Process isolation for code execution
- [ ] Dependencies audited (pip-audit)
- [ ] OWASP Top 10 mitigation verified

---

**Last updated**: 2026-06-30  
**Target Release**: v1.1 (Production Hardened)  
**Effort Estimate**: 2-3 weeks  
**Test Coverage**: 1000+ tests (100% pass rate target)
