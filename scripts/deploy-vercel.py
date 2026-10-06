#!/usr/bin/env python3
"""Deploy the FloodSafe Pakistan Next.js frontend to Vercel via the REST API.

Uses the stored custom.vercel credential. Creates the project (if needed),
sets env vars, uploads source files, and creates a production deployment.
"""
import sys, os, json, hashlib, time, urllib.request

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

WEB = "/home/hatch/workspace/flood-risk-dss/web"
HOSTS = ["api.vercel.com"]
PROJECT_NAME = "floodsafe-pakistan"
EXCLUDE_DIRS = {"node_modules", ".next", ".git"}

API_BASE_URL = os.environ.get("API_BASE_URL", "")
SITE_URL = f"https://{PROJECT_NAME}.vercel.app"


def api(method, path, body=None, raw=None, extra_headers=None):
    req = urllib.request.Request(
        "https://api.vercel.com" + path,
        data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None),
        method=method,
    )
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (extra_headers or {}).items():
        req.add_header(k, v)
    add_surrogate_to_request(req, "custom.vercel", allowed_hosts=HOSTS)
    resp = urllib.request.urlopen(req, timeout=120)
    return read_json_response(resp)


def get_project():
    try:
        p = api("GET", f"/v10/projects/{PROJECT_NAME}")
        print("project exists:", p["id"], flush=True)
        return p
    except Exception as e:
        print("project not found, creating...", flush=True)
    p = api("POST", "/v10/projects", body={"name": PROJECT_NAME, "framework": "nextjs"})
    print("project created:", p["id"], flush=True)
    return p


def set_env(project_id, key, value):
    existing = api("GET", f"/v10/projects/{project_id}/env")
    for e in existing.get("envs", []):
        if e["key"] == key and "production" in e.get("target", []):
            api("DELETE", f"/v10/projects/{project_id}/env/{e['id']}")
            print(f"  removed old {key}", flush=True)
    api("POST", f"/v10/projects/{project_id}/env", body={
        "key": key, "value": value, "type": "encrypted", "target": ["production"],
    })
    print(f"  set {key}", flush=True)


def collect_files():
    files = []
    for root, dirs, names in os.walk(WEB):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for n in names:
            full = os.path.join(root, n)
            rel = os.path.relpath(full, WEB)
            data = open(full, "rb").read()
            sha = hashlib.sha1(data).hexdigest()
            files.append((rel, sha, len(data), data))
    return files


def main():
    project = get_project()
    pid = project["id"]

    print("setting env vars", flush=True)
    if API_BASE_URL:
        set_env(pid, "API_BASE_URL", API_BASE_URL)
        set_env(pid, "NEXT_PUBLIC_API_BASE_URL", API_BASE_URL)
    set_env(pid, "NEXT_PUBLIC_SITE_URL", SITE_URL)

    files = collect_files()
    print(f"uploading {len(files)} files", flush=True)
    for i, (rel, sha, size, data) in enumerate(files):
        api("POST", "/v2/files", raw=data, extra_headers={
            "Content-Type": "application/octet-stream", "x-vercel-digest": sha})
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(files)}", flush=True)

    print("creating deployment", flush=True)
    dep = api("POST", "/v13/deployments?skipAutoDetectionConfirmation=1", body={
        "name": PROJECT_NAME,
        "project": pid,
        "target": "production",
        "files": [{"file": rel, "sha": sha, "size": size} for rel, sha, size, _ in files],
    })
    dep_id = dep["id"]
    print("deployment id:", dep_id, flush=True)

    for _ in range(90):
        d = api("GET", f"/v13/deployments/{dep_id}")
        state = d.get("readyState")
        if state == "READY":
            print("READY url:", d.get("url"))
            break
        if state in ("ERROR", "CANCELED"):
            print("FAILED:", state, d.get("errorSummary"))
            sys.exit(1)
        time.sleep(10)
    else:
        print("timed out waiting")
        sys.exit(1)

    print("disabling SSO protection", flush=True)
    api("PATCH", f"/v9/projects/{pid}", body={"ssoProtection": None})
    print("done:", SITE_URL)


if __name__ == "__main__":
    main()
