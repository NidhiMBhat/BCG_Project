with open("healthcare_backend/main.py", "r") as f:
    content = f.read()

import_line = "from healthcare_backend.api import auth, patients, scans, session, live, analytics, alerts, export, settings"
content = content.replace(import_line, import_line + ", stream")

router_line = "app.include_router(settings.router, prefix=\"/api/settings\", tags=[\"settings\"])"
content = content.replace(router_line, router_line + "\napp.include_router(stream.router, prefix=\"/api/live\", tags=[\"stream\"])")

with open("healthcare_backend/main.py", "w") as f:
    f.write(content)
print("main.py patched")
