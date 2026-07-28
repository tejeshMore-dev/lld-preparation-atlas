from datetime import datetime

from observers.observer import Observer

class LoggerObserver(Observer):
    def update(self, event: str, data: dict) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[LOG] {timestamp} | {event} | {data}")
