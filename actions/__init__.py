# JARVIS actions package - all action modules
# Each action module provides pure-ish functions for tool dispatch.

from actions.open_app import open_app
from actions.sys_info import sys_info
from actions.weather import get_weather_summary
from actions.calendar import get_calendar_events, add_calendar_event, delete_calendar_event
from actions.reminders import get_reminders, add_reminder
from actions.browser import browser_control
from actions.shell import shell_run
from actions.whatsapp import send_whatsapp_message, save_whatsapp_contact
from actions.media import play_media
from actions.youtube_stats import get_youtube_channel_report
from actions.screen_vision import analyze_screen
from actions.tts import speak_text
from actions.system_doctor import get_system_health, cleanup_temp_files, cleanup_recycle_bin
from actions.process_manager import list_processes, kill_process, set_process_priority, find_process_by_port
from actions.file_guardian import find_large_files, find_duplicate_files, cleanup_folder, get_folder_summary
from actions.network_monitor import get_network_summary, list_connections, ping_host
from actions.system_cron import add_cron_job, list_cron_jobs, remove_cron_job, start_cron_daemon
from actions.service_monitor import list_services, control_service
from actions.health import get_health_data
from actions.location import get_current_location
from actions.disk_predictor import predict_disk_full
from actions.process_timeline import poll_processes
from actions.cron_web_ui import start_cron_web_ui
from actions.windows_utils import open_url, open_uri, copy_to_clipboard
from actions.network_anomaly import scan_network_anomalies, check_ip

__all__ = [
    "open_app",
    "sys_info",
    "get_weather_summary",
    "get_calendar_events", "add_calendar_event", "delete_calendar_event",
    "get_reminders", "add_reminder",
    "browser_control",
    "shell_run",
    "send_whatsapp_message", "save_whatsapp_contact",
    "play_media",
    "get_youtube_channel_report",
    "analyze_screen",
    "speak_text",
    "get_system_health", "cleanup_temp_files", "cleanup_recycle_bin",
    "list_processes", "kill_process", "set_process_priority", "find_process_by_port",
    "find_large_files", "find_duplicate_files", "cleanup_folder", "get_folder_summary",
    "get_network_summary", "list_connections", "ping_host",
    "add_cron_job", "list_cron_jobs", "remove_cron_job", "start_cron_daemon",
    "list_services", "control_service",
    "get_health_data",
    "get_current_location",
    "predict_disk_full",
    "poll_processes",
    "scan_network_anomalies", "check_ip",
    "start_cron_web_ui",
    "open_url", "open_uri", "copy_to_clipboard",
]
