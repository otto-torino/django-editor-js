import json
import html

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

    def render_paragraph(self, data):
        text = data.get("text", "") 
        return f"<p>{text}</p>"

    def render_header(self, data):
        level = data.get("level", 2)
        text = self.escape(data.get("text", ""))
        return f"<h{level}>{text}</h{level}>"

    def render_list(self, data):
        def render_items(items):
            html_items = ""
            for item in items:
                if isinstance(item, dict) and "items" in item:
                    # Nested list
                    nested_tag = "ul" if item.get("style") == "unordered" else "ol"
                    html_items += f"<li>{self.escape(item.get('content', ''))}{render_items(item['items'])}</li>"
                else:
                    html_items += f"<li>{self.escape(item)}</li>"
            return f"<{tag}>{html_items}</{tag}>"

        tag = "ul" if data.get("style") == "unordered" else "ol"
        items = data.get("items", [])
        return render_items(items)

    def render_quote(self, data):
        text = self.escape(data.get("text", ""))
        caption = self.escape(data.get("caption", ""))
        alignment = data.get("alignment", "left")
        return f'<blockquote style="text-align: {alignment};"><p>{text}</p><footer>{caption}</footer></blockquote>'

    def render_code(self, data):
        code = html.escape(data.get("code", ""))
        return f"<pre><code>{code}</code></pre>"
    
    def render_image(self, data):
        url = data.get("file", {}).get("url", "")
        caption = self.escape(data.get("caption", ""))
        return f'<figure><img src="{self.escape(url)}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'
    
    def render_table(self, data):
        rows = data.get("content", [])
        has_headings = data.get("withHeadings", False)

        if not rows:
            return "<table></table>"
        
        if has_headings and rows:
            headings = rows[0]
            rows = rows[1:]
            html_headings = "".join(f"<th>{self.escape(cell)}</th>" for cell in headings)
            html_rows = [f"<tr>{html_headings}</tr>"]
        else:
            html_rows = []

        for row in rows:
            html_cells = "".join(f"<td>{self.escape(cell)}</td>" for cell in row)
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
        caption = self.escape(data.get("caption", ""))

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


    def render_unknown(self, data):
        return f"<!-- Unsupported block type -->"
