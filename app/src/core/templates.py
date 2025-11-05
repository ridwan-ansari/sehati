from pathlib import Path
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = BASE_DIR / "src" / "templates"

templates = Jinja2Templates(directory=TEMPLATE_DIR)

def get_templates():
    return templates
