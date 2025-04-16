from datetime import datetime

def log_time():
    return datetime.now().strftime("[%H:%M:%S]")

def log_info(message):
    print(f"{log_time()} INFO: {message}")

def log_warn(message):
    print(f"{log_time()} WARNING: {message}")

def log_fail(message):
    print(f"{log_time()} ERROR: {message}")


log_error = log_fail
