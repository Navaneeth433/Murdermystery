from app import app
from models import Content, db
import json

with app.app_context():
    contents = Content.query.all()
    for c in contents:
        if not c.panels_json:
            continue
        try:
            data = json.loads(c.panels_json)
        except Exception:
            print(f"Ch {c.chapter_number}: Cannot parse JSON, skipping.")
            continue
        panels = data.get("panels", [])
        # Strip any trailing backslashes, quotes, or whitespace from each URL
        cleaned = [url.rstrip('\\/\'" \t') for url in panels]
        cleaned = [url for url in cleaned if url.startswith("http")]
        if cleaned != panels:
            c.panels_json = json.dumps({"panels": cleaned})
            print(f"Ch {c.chapter_number}: Fixed {len(panels)} panels:")
            for url in cleaned:
                print(f"  {url}")
        else:
            print(f"Ch {c.chapter_number}: Already clean, {len(panels)} panels")
    db.session.commit()
    print("Done.")
