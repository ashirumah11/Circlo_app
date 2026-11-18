import os
from pathlib import Path

# Set test environment defaults
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('USE_SQLITE', '1')
os.environ.setdefault('USE_LOCAL_CACHE', '1')

# Ensure staticfiles and media directories exist for tests
base_dir = Path(__file__).resolve().parent / 'backend'
(base_dir / 'staticfiles').mkdir(parents=True, exist_ok=True)
(base_dir / 'media').mkdir(parents=True, exist_ok=True)
