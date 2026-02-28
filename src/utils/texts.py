from datetime import datetime, timedelta

from src.config import settings


def format_message(
    title: str,
    published: datetime,
    summary: str,
    link: str,
    source: str,
) -> str:
    summary = (
        "\n" + summary + "\n"
        if summary and summary != settings.EMPTY_TEXT
        else ""
    )
    return f"""
📌 <i><b>{title}</b></i>
{summary}
📅 <b>{(published + timedelta(hours=settings.TIMEZONE)).strftime("%d.%m.%Y %H:%M")}</b>
🔗 <b><a href="{link}">{source}, читать</a></b>
"""
