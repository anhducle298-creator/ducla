class AlertService:
    def format_alert(self, title, lines):
        body = "\n".join(lines)
        return f"* {title}\n\n{body}"
