import tinycss2
from bs4 import BeautifulSoup
from tinycss2.ast import (
    AtKeywordToken,
    AtRule,
    HashToken,
    IdentToken,
    QualifiedRule,
)


def reply_subject(subject: str) -> str:
    """
    Generate a subject for a reply email.
    """
    lower = subject.lower()
    if lower.startswith("re:") or lower.startswith("re "):
        return subject
    return "Re: " + subject


FULL_HTML = """
<html>
<head>
</head>
<body>
    {}
</body>
</html>
"""


def _rename_body_to_blockquote(
    css: str, quoted_email_div_id: str = "quoted_email"
) -> str:
    """
    Modify CSS of email so that rules that applied to the body now apply to the
    quoted email div element.
    """
    try:
        rules = tinycss2.parse_stylesheet(css, skip_comments=True)
    except TypeError:
        return css

    for rule in rules:
        # this doesn't do nested at-rules.
        # this doesn't do all at-rules that may have rules inside.
        if (
            isinstance(rule, AtRule)
            and rule.lower_at_keyword in {"media", "supports"}
            and not any(
                isinstance(s, AtKeywordToken) for s in (rule.content or [])
            )
        ):
            old_terms = rule.content
        elif isinstance(rule, QualifiedRule):
            old_terms = rule.prelude
        else:
            continue
        if not old_terms:
            continue
        new_terms = []
        i = 0
        while i < len(old_terms):
            # doesn't do *
            # if it was body[id="foo"], the [id="foo"] will stay
            s = old_terms[i]
            if isinstance(s, IdentToken) and s.lower_value == "body":
                new_terms += [
                    IdentToken(line=0, column=0, value="div"),
                    HashToken(
                        line=0,
                        column=0,
                        value=quoted_email_div_id,
                        is_identifier=True,
                    ),
                ]
                if i + 1 < len(old_terms) and isinstance(
                    old_terms[i + 1], HashToken
                ):
                    i += 1
            else:
                new_terms += [s]
            i += 1
        if isinstance(rule, AtRule):
            rule.content = new_terms
        else:
            rule.prelude = new_terms
    try:
        return tinycss2.serialize(rules)
    except TypeError:
        return css


def quote_html(
    received: str, added: str, quoted_email_div_id: str = "quoted_email"
) -> str:
    """
    Build HTML for an email message that quotes a previous email and adds
    content above it. The style of the new content should not be affected by the
    style of the quoted email.

    @param received: complete HTML of the email to quote
    @param added: HTML body snippet to add above the quoted email
    @param quoted_email_div_id: ID of the div element that will contain the
        quoted email
    """
    # handles html(head, body), html(body), body, and raw element
    soup = BeautifulSoup(received, features="html.parser")
    # if it's <body>... or <html>...<body>... then soup.body is not None
    if soup.body is None:
        soup = BeautifulSoup(FULL_HTML.format(received), features="html.parser")
    assert soup.body is not None

    if soup.head:
        style_tags = soup.head.find_all("style")
        styles_content = "\n".join(style.string or "" for style in style_tags)
        for style in style_tags:
            style.decompose()

        new_style = soup.new_tag("style")
        new_style.string = _rename_body_to_blockquote(
            styles_content, quoted_email_div_id=quoted_email_div_id
        )
        soup.head.append(new_style)

    body = soup.body
    body_style = body.get("style")
    body_class = body.get("class")
    body.attrs = {
        k: v for k, v in body.attrs.items() if k not in {"style", "class", "id"}
    }

    body_text = body.encode_contents().decode()
    body.clear()

    bq = soup.new_tag("div", id=quoted_email_div_id)
    if body_style:
        bq["style"] = body_style
    if body_class:
        bq["class"] = body_class
    body_soup = BeautifulSoup(body_text, features="html.parser")
    for content in list(body_soup.contents):
        bq.append(content)

    body.append(bq)

    raw = BeautifulSoup(added, features="html.parser")
    body.insert(0, raw)

    return soup.prettify(formatter="html")


def quote_plain(received: str, added: str) -> str:
    """
    Build a plain-text email message that quotes a previous email and adds
    content above it.
    """
    return "\n".join(
        [added + "\n\n"] + ["> " + ln for ln in received.split("\n")]
    )
