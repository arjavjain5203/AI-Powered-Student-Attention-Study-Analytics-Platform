"""List or download explicitly shared local false-alarm clips for review."""
import argparse
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

from dotenv import load_dotenv

backend = Path(__file__).resolve().parents[1]
root = backend.parent
load_dotenv(backend / ".env")
token = os.getenv("REVIEW_ADMIN_TOKEN", "")
if len(token) < 32:
    raise SystemExit("REVIEW_ADMIN_TOKEN must be configured in backend/.env")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--download", metavar="REPORT_ID", help="Download one explicitly shared clip")
args = parser.parse_args()
api = os.getenv("REVIEW_API_URL", "http://127.0.0.1:8000").rstrip("/")
path = "/api/admin/false-alarms"
if args.download:
    if not re.fullmatch(r"[0-9a-f]{24}", args.download):
        raise SystemExit("Invalid report ID")
    path += f"/{args.download}/clip"
request = Request(api + path, headers={"X-Review-Token": token})
with urlopen(request, timeout=10) as response:
    data = response.read()
if args.download:
    destination = root / ".local" / "review-clips" / f"{args.download}.webm"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    print(f"Saved student-shared clip to {destination} (delete it when review ends)")
else:
    for report in json.loads(data):
        print(f"{report['id']}  {report['category']}  {report['submitted_at']}  clip={report['clip_shared']}")
