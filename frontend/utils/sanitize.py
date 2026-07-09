import html


def xss_escape(value: str) -> str:
    return html.escape(str(value), quote=True)


def safe_markdown(value: str) -> str:
    return html.escape(str(value), quote=True)
