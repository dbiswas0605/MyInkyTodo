from typing import Optional, List, Dict

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
        api_key = device_config.load_env_key("OPEN_AI_SECRET")

        prompt_response = MyTodoPlugin.fetch_text_prompt(api_key)

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
    def fetch_text_prompt(api_key: str):
        logger.info(f"Getting random text prompt from input")
        MyTodoPlugin.display_tasks_by_project(api_key)

        prompt = "Hello Tasks! Here is a random task for you to complete today: "
        logger.info(f"Generated random text prompt: {prompt}")

        return prompt

    def _make_request(self, api_token:str, endpoint: str) -> Optional[Dict]:
        """
        Make a GET request to the Todoist API

        Args:
            endpoint (str): API endpoint to call

        Returns:
            Dict: JSON response or None if error
        """

        api_token = api_token
        base_url = "https://api.todoist.com/rest/v2"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        url = f"{base_url}/{endpoint}"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {endpoint}: {e}")
            return None

    def get_projects(self, api_token) -> Optional[List[Dict]]:
        """
        Get all projects from Todoist account

        Returns:
            List[Dict]: List of projects or None if error
        """
        return self._make_request(api_token, "projects")

    def get_tasks(self, project_id: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Get tasks from Todoist account

        Args:
            project_id (str, optional): Filter tasks by project ID

        Returns:
            List[Dict]: List of tasks or None if error
        """
        endpoint = "tasks"
        if project_id:
            endpoint += f"?project_id={project_id}"

        return self._make_request(endpoint)

    def display_tasks_by_project(self, api_token: str) -> str:
        """Print a summary of all projects"""
        projects = self.get_projects(api_token)
        if not projects:
            print("No projects found or error occurred")
            return

        print("-" * 50)

        _output = ''
        for project in projects:
            if project['name'] == 'Inbox':
                continue
            tasks = self.get_tasks(project['id'])

            if not tasks:
                print(f"No tasks found for {project['name']}")
            else:
                print(f"{project['name']}")
                for task in tasks:
                    priority_map = {1: "🔸", 2: "🔸", 3: "🔶", 4: "🔴"}
                    priority_icon = priority_map.get(task.get('priority', 1), "🔸")

                    print(f"{priority_icon} {task['content']}")
                    _output += f"{priority_icon} {task['content']}\n"

                    if task.get('description'):
                        print(f"   📝 {task['description']}")
                    if task.get('due'):
                        print(f"   📅 Due: {task['due']['string']}")
                    print()

        return _output
