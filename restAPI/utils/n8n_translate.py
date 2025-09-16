import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# You'll need to add this to your settings or .env
N8N_TRANSLATE_WEBHOOK_URL = getattr(settings, 'N8N_TRANSLATE_WEBHOOK_URL', 'https://n8n.nxfs.no/webhook/translate-task')

def send_translation_request(task_id, model_name, fields_to_translate):
    """
    Send translation request to n8n workflow.

    Args:
        task_id: ID of the model instance to update
        model_name: Name of the model (e.g., 'Task', 'Project')
        fields_to_translate: Dict of field names and text to translate

    Returns:
        bool: True if request was sent successfully, False otherwise
    """
    try:
        payload = {
            'task_id': task_id,
            'model_name': model_name,
            'fields': fields_to_translate,
            'api_base_url': getattr(settings, 'API_BASE_URL', 'https://api.nxfs.no'),
            'callback_endpoint': f'/app/{model_name.lower()}s/{task_id}/'  # e.g., /app/tasks/123/
        }

        logger.info(f"Sending translation request to n8n for {model_name} {task_id}: {list(fields_to_translate.keys())}")

        response = requests.post(
            N8N_TRANSLATE_WEBHOOK_URL,
            json=payload,
            timeout=10,  # Don't wait too long
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            logger.info(f"Translation request sent successfully for {model_name} {task_id}")
            return True
        else:
            logger.warning(f"n8n webhook returned status {response.status_code} for {model_name} {task_id}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send translation request to n8n for {model_name} {task_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending translation request for {model_name} {task_id}: {str(e)}")
        return False