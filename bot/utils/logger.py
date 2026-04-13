import os
from datetime import datetime
from pathlib import Path
from enum import Enum

class LogType(str, Enum):
    SYSTEM_STATUS = "system_status"
    MAIN_LOG = "main_log"
    USERBOT_MODULE = "userbot_module"
    MEMBER_LOG = "member_log"

import inspect

def _write_log(level: str, content: str, message_log: LogType):
    """
    Internal function to write logs to a file in the format: 
    Logs/YYYY/MM/DD/message_log.txt
    """
    now = datetime.now()
    
    # Get caller info (file and line)
    # Go back 2 frames: _write_log -> LogInfo/Error -> Actual Caller
    frame = inspect.currentframe().f_back.f_back
    filename = "unknown"
    lineno = 0
    if frame:
        filename = os.path.basename(frame.f_code.co_filename)
        lineno = frame.f_lineno

    # Find the root backend directory
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    # Create directory path: Logs/YYYY/MM/DD
    log_dir = base_dir / "Logs" / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    
    # Ensure directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file name
    file_name = message_log.value
    if not file_name.endswith(".txt"):
        file_name += ".txt"
        
    log_file_path = log_dir / file_name
    
    # Format time for each log line
    time_str = now.strftime("%Y/%m/%d %H:%M:%S")
    log_line = f"[{time_str}] [{level}] [{filename}:{lineno}] {content}\n"
    
    # Write to file in append mode
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_line)
        
    # Print to console for direct monitoring
    print(f"[{time_str}] [{level}] | {filename}:{lineno} | {content}")

def LogInfo(content: str, message_log: LogType = LogType.MAIN_LOG):
    _write_log("INFO", content, message_log)

def LogWarning(content: str, message_log: LogType = LogType.MAIN_LOG):
    _write_log("WARNING", content, message_log)

def LogError(content: str, message_log: LogType = LogType.MAIN_LOG):
    _write_log("ERROR", content, message_log)
