from models.notification import Notification


class NotificationService:
    def __init__(self) -> None:
        self.sent_notifications: list[Notification] = []

    def send(self, notification: Notification) -> None:
        self.sent_notifications.append(notification)
        print(
            f"[Notification] To: {notification.member.name} | "
            f"Message: {notification.message}"
        )
