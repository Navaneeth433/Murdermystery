from app import app
from models import Content
import json

with app.app_context():
    c = Content.query.get(1)
    data = json.loads(c.panels_json)
    panels = data.get("panels", [])
    all_ok = True
    for i, url in enumerate(panels):
        has_backslash = "\\" in url
        starts_http = url.startswith("http")
        print(f"Panel {i+1}: starts_http={starts_http} has_backslash={has_backslash} url={url}")
        if not starts_http or has_backslash:
            all_ok = False
    print(f"\nAll URLs clean: {all_ok}")
