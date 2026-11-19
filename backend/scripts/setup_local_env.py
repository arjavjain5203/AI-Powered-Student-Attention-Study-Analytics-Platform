"""Create a local .env once. Deployment uses the same variable names."""
from pathlib import Path
import secrets

backend = Path(__file__).resolve().parents[1]
target = backend / ".env"
if target.exists():
    content = target.read_text(encoding="utf-8")
    if "REVIEW_ADMIN_TOKEN=" not in content:
        with target.open("a", encoding="utf-8") as output:
            output.write(f"\nREVIEW_ADMIN_TOKEN={secrets.token_urlsafe(48)}\n")
        print("Added local false-alarm review credential to backend/.env")
    else:
        print("Existing backend/.env left unchanged")
else:
    example = (backend / ".env.example").read_text(encoding="utf-8")
    example = example.replace("replace-with-a-long-random-secret", secrets.token_urlsafe(48))
    example = example.replace("replace-with-a-long-random-review-token", secrets.token_urlsafe(48))
    target.write_text(example, encoding="utf-8")
    print("Created backend/.env with a random JWT secret")
