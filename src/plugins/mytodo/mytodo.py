from plugins.base_plugin.base_plugin import BasePlugin
from utils.app_utils import resolve_path
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from utils.image_utils import resize_image
from io import BytesIO
from datetime import datetime
import requests
import logging
import textwrap
import os

logger = logging.getLogger(__name__)

class MyTodoPlugin(BasePlugin):
    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['api_key'] = {
            "required": True,
            "service": "OpenAI",
            "expected_key": "TODOIST_API_TOKEN"
        }
        template_params['style_settings'] = True
        return template_params

    def generate_image(self, settings, device_config):

        prompt_response = MyTodoPlugin.fetch_text_prompt()

        title = settings.get("title")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        image_template_params = {
            "title": title,
            "content": prompt_response,
            "plugin_settings": settings
        }

        image = self.render_image(dimensions, "mytodo.html", "mytodo.css", image_template_params)

        return image

    @staticmethod
    def fetch_text_prompt():
        logger.info(f"Getting random text prompt from input")

        prompt = "Hello Tasks! Here is a random task for you to complete today: "
        logger.info(f"Generated random text prompt: {prompt}")

        return prompt