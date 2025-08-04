from PIL import Image, ImageDraw, ImageFont
from plugins.base_plugin.base_plugin import BasePlugin
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

class MyTodoPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['style_settings'] = True
        return template_params

    def _get_google_service(self, settings):
        creds = None
        # TODO: Implement proper OAuth2 flow and token storage
        if not settings.get('client_id') or not settings.get('client_secret'):
            raise RuntimeError('Google API credentials not configured')

        client_config = {
            "installed": {
                "client_id": settings['client_id'],
                "client_secret": settings['client_secret'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
            }
        }

        flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
        creds = flow.run_local_server(port=0)

        return build('tasks', 'v1', credentials=creds)

    def _fetch_tasks(self, service, settings):
        max_tasks = int(settings.get('max_tasks', 5))
        list_id = settings.get('list_id', '@default')

        try:
            results = service.tasks().list(tasklist=list_id, maxResults=max_tasks).execute()
            return results.get('items', [])
        except Exception as e:
            raise RuntimeError(f'Failed to fetch tasks: {str(e)}')

    def generate_image(self, settings, device_config):
        # Create a new image with white background
        width = device_config.width
        height = device_config.height
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)

        # Load font
        try:
            font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
            font_tasks = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        except OSError:
            # Fallback to default font
            font_title = ImageFont.load_default()
            font_tasks = ImageFont.load_default()

        # Draw title
        draw.text((10, 10), 'My Todo List', font=font_title, fill='black')

        try:
            service = self._get_google_service(settings)
            tasks = self._fetch_tasks(service, settings)

            y_position = 50
            for task in tasks:
                task_title = task.get('title', 'Untitled Task')
                status = '☐' if task.get('status') == 'needsAction' else '☑'
                draw.text((10, y_position), f'{status} {task_title}', font=font_tasks, fill='black')
                y_position += 30

            if not tasks:
                draw.text((10, y_position), 'No tasks found', font=font_tasks, fill='black')

        except Exception as e:
            draw.text((10, height//2), f'Error: {str(e)}', font=font_tasks, fill='black')

        return image
