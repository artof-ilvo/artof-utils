from dotenv import load_dotenv
from os import path, getenv

load_dotenv()

ilvo_path = getenv('ILVO_PATH')
if ilvo_path and path.exists(ilvo_path):
    base = path.join(ilvo_path)
    platform_settings = path.join(base, 'settings.json')
    implements = path.join(base, 'implement')
    fields = path.join(base, 'field')
