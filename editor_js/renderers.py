import json
import html
import re
from html.parser import HTMLParser

from django.utils.html import strip_tags


_UNSAFE_URL_RE = re.compile(r'^(javascript|data|vbscript):', re.IGNORECASE)
# Browsers drop tabs and newlines anywhere in a URL, and control characters
# and spaces at its start, before reading its scheme.
_URL_IGNORED_CHARS_RE = re.compile(r'[\t\n\r]')
_URL_LEADING_CHARS_RE = re.compile(r'^[\x00-\x20]+')


def _is_unsafe_url(url):
    """Whether a browser would run the URL as script or inline content."""
    url = _URL_LEADING_CHARS_RE.sub('', _URL_IGNORED_CHARS_RE.sub('', str(url)))
    return bool(_UNSAFE_URL_RE.match(url))


class _InlineHTMLSanitizer(HTMLParser):
    """
    Allowlist sanitizer for the markup produced by the Editor.js inline
    toolbar (bold, italic, links, highlight, font size, ...). Disallowed
    tags are dropped while their text content is kept; attribute values are
    escaped, validated against per-attribute rules (True = any value, or a
    regex the value must match) and unsafe URL schemes are removed.
    """

    CDX_CLASS_RE = re.compile(r'^cdx-[\w-]+( cdx-[\w-]+)*$')
    FONT_SIZE_STYLE_RE = re.compile(
        r'^font-size:\s*\d+(\.\d+)?(em|rem|px|%)\s*;?$', re.IGNORECASE
    )

    ALLOWED_TAGS = {
        'a': {'href': True, 'target': True, 'rel': True},
        'b': {}, 'strong': {}, 'i': {}, 'em': {},
        'u': {}, 's': {}, 'code': {},
        'mark': {'class': CDX_CLASS_RE},
        'span': {'class': CDX_CLASS_RE, 'style': FONT_SIZE_STYLE_RE},
        'sup': {}, 'sub': {}, 'br': {},
    }

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        allowed_attrs = self.ALLOWED_TAGS.get(tag)
        if allowed_attrs is None:
            return
        rendered_attrs = ''
        for name, value in attrs:
            rule = allowed_attrs.get(name)
            if rule is None or value is None:
                continue
            if name == 'href' and _is_unsafe_url(value):
                continue
            if rule is not True and not rule.match(value):
                continue
            rendered_attrs += f' {name}="{html.escape(value)}"'
        self.parts.append(f'<{tag}{rendered_attrs}>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.ALLOWED_TAGS and tag != 'br':
            self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        self.parts.append(html.escape(data, quote=False))

    def handle_entityref(self, name):
        self.parts.append(f'&{name};')

    def handle_charref(self, name):
        self.parts.append(f'&#{name};')

    def result(self):
        return ''.join(self.parts)


class EditorJsRenderer:
    def __init__(self, data, safe=True):
        """
        :param data: JSON string o dict contenente i dati di Editor.js
        :param safe: Se True, esegue escaping per prevenire XSS
        """
        if isinstance(data, dict):
            self.content = data
        elif isinstance(data, str):
            try:
                self.content = json.loads(data)
            except json.JSONDecodeError:
                raise ValueError("EditorJsRenderer: invalid JSON string.")
        else:
            raise ValueError("EditorJsRenderer: data must be a dict or JSON string.")

        self.safe = safe

    def render(self):
        if "blocks" not in self.content:
            return ""
        return "".join(self.render_block(block) for block in self.content["blocks"])

    def render_block(self, block):
        block_type = block.get("type")
        renderer = getattr(self, f"render_{block_type}", self.render_unknown)
        return renderer(block.get("data", {}))

    def escape(self, text):
        return html.escape(text) if self.safe else text

    def clean_inline(self, text):
        """
        Clean text that may carry inline-toolbar markup (bold, italic,
        links, ...): allowed inline tags pass through, everything else is
        dropped. Full escaping here would show the markup as literal text.
        """
        if not self.safe:
            return text
        sanitizer = _InlineHTMLSanitizer()
        sanitizer.feed(str(text))
        sanitizer.close()
        return sanitizer.result()

    def render_paragraph(self, data):
        text = self.clean_inline(data.get("text", ""))
        return f"<p>{text}</p>"

    def render_header(self, data):
        level = data.get("level", 2)
        text = self.clean_inline(data.get("text", ""))
        return f"<h{level}>{text}</h{level}>"

    def render_list(self, data):
        def render_items(items, style):
            tag = "ul" if style == "unordered" else "ol"
            html_items = ""
            for item in items:
                if isinstance(item, dict):
                    content = self.clean_inline(item.get("content", ""))
                    children = item.get("items", [])
                    child_style = item.get("style", style)
                    nested = render_items(children, child_style) if children else ""
                    html_items += f"<li>{content}{nested}</li>"
                else:
                    html_items += f"<li>{self.clean_inline(item)}</li>"
            return f"<{tag}>{html_items}</{tag}>"

        items = data.get("items", [])
        return render_items(items, data.get("style", "unordered"))

    def render_quote(self, data):
        text = self.clean_inline(data.get("text", ""))
        caption = self.clean_inline(data.get("caption", ""))
        alignment = data.get("alignment", "left")
        return f'<blockquote style="text-align: {alignment};"><p>{text}</p><footer>{caption}</footer></blockquote>'

    def render_code(self, data):
        code = html.escape(data.get("code", ""))
        return f"<pre><code>{code}</code></pre>"
    
    def render_image(self, data):
        url = data.get("file", {}).get("url", "")
        caption = data.get("caption", "")
        # The alt attribute must be plain text; the visible caption keeps
        # its inline markup.
        alt = self.escape(strip_tags(caption)) if self.safe else caption
        return f'<figure><img src="{self.escape(url)}" alt="{alt}"><figcaption>{self.clean_inline(caption)}</figcaption></figure>'
    
    def render_table(self, data):
        rows = data.get("content", [])
        has_headings = data.get("withHeadings", False)

        if not rows:
            return "<table></table>"
        
        if has_headings and rows:
            headings = rows[0]
            rows = rows[1:]
            html_headings = "".join(f"<th>{self.clean_inline(cell)}</th>" for cell in headings)
            html_rows = [f"<tr>{html_headings}</tr>"]
        else:
            html_rows = []

        for row in rows:
            html_cells = "".join(f"<td>{self.clean_inline(cell)}</td>" for cell in row)
            html_rows.append(f"<tr>{html_cells}</tr>")
        
        if has_headings:
            return f"""
            <table>
                <thead>{html_rows.pop(0)}</thead>
                <tbody>{"".join(html_rows)}</tbody>
            </table>
            """
        else:
            return f"<table><tbody>{''.join(html_rows)}</tbody></table>"
        
    def render_raw(self, data):
        raw_html = data.get("html", "")
        return raw_html
    
    def render_embed(self, data):
        service = self.escape(data.get("service", ""))
        embed_url = self.escape(data.get("embed", ""))
        caption = self.clean_inline(data.get("caption", ""))

        if not embed_url:
            return ""

        return f"""
            <figure class="embed-figure embed-{service}">
                <div class="embed-responsive-wrapper">
                    <iframe src="{embed_url}" frameborder="0" allowfullscreen></iframe>
                </div>
                <figcaption>{caption}</figcaption>
            </figure>
        """
    
    BUTTON_JUSTIFY = {"left": "flex-start", "center": "center", "right": "flex-end"}
    BUTTON_GAPS = {"small": "0.5rem", "medium": "1rem", "large": "2rem"}
    # The style of each button of a row, by distribution. "fit-content" keeps
    # a button as wide as its text, so a row that does not fit wraps whole
    # buttons rather than their text.
    BUTTON_STYLES = {
        "grouped": "",
        # Equal widths: every button grows from no width at all.
        "fill": "flex: 1 1 0; min-width: fit-content;",
        # Below 36rem of row the basis turns huge and every button takes a
        # line of its own, full width; above it turns 0 and the buttons keep
        # the width of their text, spread by the row.
        "spread": "flex: 0 1 calc((36rem - 100%) * 999); min-width: fit-content;",
    }

    def render_button(self, data):
        # A button block holds a row of buttons in "buttons"; blocks saved
        # before that hold a single button in "text", "url" and "btnColor".
        buttons = data.get("buttons")
        if buttons is None:
            buttons = [data]
        if not buttons:
            return ""

        # The layout values go into a style attribute: only known ones pass.
        alignment = data.get("alignment", "left")
        if alignment not in self.BUTTON_JUSTIFY:
            alignment = "left"
        distribution = data.get("distribution", "grouped")
        if distribution not in self.BUTTON_STYLES:
            distribution = "grouped"
        gap = data.get("gap", "small")
        if gap not in self.BUTTON_GAPS:
            gap = "small"

        if distribution == "spread":
            justify = "space-between"
        else:
            justify = self.BUTTON_JUSTIFY[alignment]
        style = self.BUTTON_STYLES[distribution]
        button_style = f' style="{style}"' if style else ""

        buttons_html = []
        for button in buttons:
            text = self.escape(button.get("text", ""))
            url = button.get("url", "#")
            # As for the links in the text: a button must not run script.
            if self.safe and _is_unsafe_url(url):
                url = "#"
            url = self.escape(url)
            css_class = self.escape(button.get("btnColor", "btn-secondary"))
            buttons_html.append(f'<a href="{url}" class="btn {css_class}"{button_style}>{text}</a>')

        # A row that does not fit wraps onto more lines.
        return (
            f'<div class="editor-js-buttons editor-js-buttons--{distribution}" '
            f'style="display: flex; flex-wrap: wrap; gap: {self.BUTTON_GAPS[gap]}; '
            f'justify-content: {justify};">{"".join(buttons_html)}</div>'
        )
    
    def render_divider(self, data):
        return '<hr>'

    def render_spacer(self, data):
        size = data.get("size", "medium")
        if size not in {"small", "medium", "large"}:
            size = "medium"
        heights = {"small": "1rem", "medium": "2rem", "large": "4rem"}
        return (
            f'<div class="editor-js-spacer editor-js-spacer--{size}" '
            f'style="height: {heights[size]};" aria-hidden="true"></div>'
        )


    def render_unknown(self, data):
        return f"<!-- Unsupported block type -->"
