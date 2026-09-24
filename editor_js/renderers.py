import json
import html
import re
from html.parser import HTMLParser

from django.utils.html import strip_tags


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
    UNSAFE_URL_RE = re.compile(r'^\s*(javascript|data|vbscript):', re.IGNORECASE)

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
            if name == 'href' and self.UNSAFE_URL_RE.match(value):
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
    
    def render_button(self, data):
        text = self.escape(data.get("text", ""))
        url = self.escape(data.get("url", "#"))
        css_class = self.escape(data.get("btnColor", "btn-secondary"))
        alignment = self.escape(data.get("alignment", "left"))

        button_html = f'<a href="{url}" class="btn {css_class}">{text}</a>'

        return f'<div style="text-align: {alignment};">{button_html}</div>'
    
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
