# GUI Verification Rules & Troubleshooting

## Problem Analysis (Trial & Error Retrospective)

**Issue**: Recurrent `failures to navigate to URL` and `connection refused` errors when attempting to verify the GUI running on `localhost`.

**Cause Analysis**:
The application `validate_bibtex.py` performs heavy initialization setup before traversing into the main event loop and binding to the port. This includes:

1.  Loading NLP models (`en_core_web_sm`).
2.  Pre-checking API connectivity (ArXiv, Crossref, etc.).
3.  Compiling `FIELD_SCHEMA`.

In previous attempts, the `browser_subagent` was triggered almost immediately (within 2 seconds) of the `run_command` call. The application was still initializing, leading to a race condition where the browser attempted to connect to a closed port. This forced multiple retry loops, wasting resources.

**Key Observation**: The `Uvicorn running on http://0.0.0.0:PORT` message is the only reliable indicator that the server is ready to accept connections.

---

## The Rule: Strict Server Startup Protocol

To ensure 100% success rate in GUI verification, the following protocol must be strictly adhered to:

### 1. START with Log Capture

Always redirect output to a log file so readiness can be programmatically verified.

```python
# CORRECT
run_command(CommandLine="python3 validate_bibtex.py references.bib --gui --port 8080 > server.log 2>&1")

# INCORRECT (Blind wait)
run_command(CommandLine="python3 validate_bibtex.py ...")
```

### 2. VERIFY Readiness

Do not launch the browser until the port binding is confirmed.

```python
# Check logs for success message
run_command(CommandLine="grep 'Uvicorn running on' server.log")
# OR check port explicitly
run_command(CommandLine="netstat -tuln | grep 8080")
```

### 3. LAUNCH Browser

Only after Step 2 confirms readiness, launch the `browser_subagent`.

### 4. CLEANUP

Always kill the background process using the port after verification is complete to prevent port conflicts.

```python
run_command(CommandLine="fuser -k 8080/tcp")
```

## Latency Factors & Delays

When verifying this specific application, expect significant startup delays due to the following architectural decisions:

### 1. Pre-flight Validation (Primary Bottleneck)

The application runs a full validation of the provided bibliography file **before** starting the web server.

- **Impact**: For a file with ~70 entries, this causes a **30-40 second delay** between executing the command and the port becoming active.
- **Mitigation**: Do NOT lower timeout values. Trust the log poll.

### 2. External API Rate Limits

During pre-flight validation, the app queries external APIs (ArXiv, Crossref, DBLP).

- **ArXiv**: Enforces a strict 3-5 second delay between requests.
- **Impact**: If many entries require ArXiv verification, startup time increases linearly despite threading optimizations.

### 3. NLP Model Loading

The application loads `en_core_web_sm` (Spacy) on startup.

- **Impact**: Adds a fixed ~3-5 second overhead to every run, even with empty bibliography files.

## Common Error Reference

| Error                    | Cause                                                   | Fix                                     |
| :----------------------- | :------------------------------------------------------ | :-------------------------------------- |
| `ERR_CONNECTION_REFUSED` | Browser launched before `Uvicorn running` log appeared. | **WAIT** longer. Poll logs.             |
| `Address already in use` | Previous validation process was not killed.             | Run `fuser -k PORT/tcp`.                |
| `429 Too Many Requests`  | Launching multiple validators too quickly.              | Wait between runs; respect rate limits. |
