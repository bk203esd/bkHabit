import bleach
import markdown as md


ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "blockquote",
    "code",
    "pre",
    "a",
    "hr",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "rel"]}


def render_markdown(text: str) -> str:
    html = md.markdown(
        text or "",
        extensions=["extra", "sane_lists", "nl2br"],
    )
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
