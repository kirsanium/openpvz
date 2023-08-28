import requests
import logging


_logger = logging.getLogger(__name__)


def get_timezone(longitude: float, latitude: float) -> str | None:
    try:
        response = requests.get(f"http://timezonefinder.michelfe.it/api/0_{longitude}_{latitude}")
    except requests.exceptions.RequestException:
        _logger.exception("Request get_last_videos_created threw exception")
        return None
    result = response.json()
    if result['status_code'] != 200:
        return None
    return result['tz_name']
