from datetime import datetime


def format_message(
    title: str,
    published: datetime,
    summary: str,
    link: str,
    source: str,
):

    return f"""
📌 <i><b>{title}</b></i>

{summary}

🔗 <b>{source} <a href="{link}">(Перейти к источнику)</a></b>

"""


# 📅 <b>{published.strftime(format="%d.%m.%Y %H:%M")}</b>
