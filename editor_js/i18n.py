"""
The translations of the editor: the dictionary Editor.js takes as
``i18n.messages``, and the texts of the iframe around it, in the active
language.

Every text goes through Django's gettext, so its translations live in the
.po files of the library, and a project can add a language as it does for
any other app. The keys are the English texts Editor.js and its tools look
up: a text with no translation stays in English.

Every text has an "editor_js" context: Django uses the translation of the
first installed app that has a text, and without a context "Delete" or "Add"
would take the one of the admin.
"""
from django.utils.translation import pgettext


def _core_messages():
    return {
        "ui": {
            "blockTunes": {
                "toggler": {
                    "Click to tune": pgettext("editor_js", "Click to tune"),
                    "or drag to move": pgettext("editor_js", "or drag to move"),
                },
            },
            "inlineToolbar": {"converter": {"Convert to": pgettext("editor_js", "Convert to")}},
            "toolbar": {"toolbox": {"Add": pgettext("editor_js", "Add")}},
            "popover": {
                "Filter": pgettext("editor_js", "Filter"),
                "Nothing found": pgettext("editor_js", "Nothing found"),
                "Convert to": pgettext("editor_js", "Convert to"),
            },
        },
        # The titles of the block and inline tools, in the toolbox, in the
        # inline toolbar and in "Convert to".
        "toolNames": {
            "Text": pgettext("editor_js", "Text"),
            "Heading": pgettext("editor_js block", "Heading"),
            "Unordered List": pgettext("editor_js", "Unordered List"),
            "Ordered List": pgettext("editor_js", "Ordered List"),
            "Checklist": pgettext("editor_js", "Checklist"),
            "Quote": pgettext("editor_js", "Quote"),
            "Table": pgettext("editor_js", "Table"),
            "Raw HTML": pgettext("editor_js", "Raw HTML"),
            "Image": pgettext("editor_js", "Image"),
            "Button": pgettext("editor_js", "Button"),
            "Divider": pgettext("editor_js", "Divider"),
            "Spacer": pgettext("editor_js", "Spacer"),
            "Link": pgettext("editor_js", "Link"),
            "Bold": pgettext("editor_js", "Bold"),
            "Italic": pgettext("editor_js", "Italic"),
            "Highlight": pgettext("editor_js", "Highlight"),
            "Font size": pgettext("editor_js", "Font size"),
        },
        "tools": {
            "stub": {
                "Error": pgettext("editor_js", "Error"),
                "The block can not be displayed correctly.": pgettext(
                    "editor_js", "The block can not be displayed correctly."
                ),
            },
        },
        "blockTunes": {
            "delete": {"Delete": pgettext("editor_js", "Delete"), "Click to delete": pgettext("editor_js", "Click to delete")},
            "moveUp": {"Move up": pgettext("editor_js", "Move up")},
            "moveDown": {"Move down": pgettext("editor_js", "Move down")},
        },
    }


def _header_messages():
    return {
        f"Heading {level}": pgettext("editor_js", "Heading %(level)s") % {"level": level}
        for level in range(1, 7)
    }


def _list_messages():
    return {
        "Unordered": pgettext("editor_js", "Unordered"),
        "Ordered": pgettext("editor_js", "Ordered"),
        "Checklist": pgettext("editor_js", "Checklist"),
        "Counter type": pgettext("editor_js", "Counter type"),
        "Start with": pgettext("editor_js", "Start with"),
        "Numeric": pgettext("editor_js", "Numeric"),
        "Lower Roman": pgettext("editor_js", "Lower Roman"),
        "Upper Roman": pgettext("editor_js", "Upper Roman"),
        "Lower Alpha": pgettext("editor_js", "Lower Alpha"),
        "Upper Alpha": pgettext("editor_js", "Upper Alpha"),
    }


def _quote_messages():
    return {
        "Enter a quote": pgettext("editor_js", "Enter a quote"),
        "Enter a caption": pgettext("editor_js", "Enter a caption"),
        "Align Left": pgettext("editor_js", "Align Left"),
        "Align Center": pgettext("editor_js", "Align Center"),
    }


def _table_messages():
    return {
        "Add column to left": pgettext("editor_js", "Add column to left"),
        "Add column to right": pgettext("editor_js", "Add column to right"),
        "Add row above": pgettext("editor_js", "Add row above"),
        "Add row below": pgettext("editor_js", "Add row below"),
        "Delete column": pgettext("editor_js", "Delete column"),
        "Delete row": pgettext("editor_js", "Delete row"),
        "Heading": pgettext("editor_js table row", "Heading"),
        "With headings": pgettext("editor_js", "With headings"),
        "Without headings": pgettext("editor_js", "Without headings"),
        "Stretch": pgettext("editor_js", "Stretch"),
        "Collapse": pgettext("editor_js", "Collapse"),
    }


def _raw_messages():
    return {"Enter HTML code": pgettext("editor_js", "Enter HTML code")}


def _embed_messages():
    return {"Enter a caption": pgettext("editor_js", "Enter a caption")}


def _image_messages():
    return {
        "Caption": pgettext("editor_js", "Caption"),
        "Select an Image": pgettext("editor_js", "Select an Image"),
        "Couldn’t upload image. Please try another.": pgettext(
            "editor_js", "Couldn’t upload image. Please try another."
        ),
        "With border": pgettext("editor_js", "With border"),
        "Stretch image": pgettext("editor_js", "Stretch image"),
        "With background": pgettext("editor_js", "With background"),
        "With caption": pgettext("editor_js", "With caption"),
    }


def _button_messages():
    return {
        "Click me": pgettext("editor_js", "Click me"),
        "Button %(number)s": pgettext("editor_js", "Button %(number)s"),
        "Add a URL to every button in the block settings: a button without one will not be saved.": pgettext(
            "editor_js",
            "Add a URL to every button in the block settings: a button without one will not be saved.",
        ),
        "Primary": pgettext("editor_js", "Primary"),
        "Secondary": pgettext("editor_js", "Secondary"),
        "Remove": pgettext("editor_js", "Remove"),
        "+ Add button": pgettext("editor_js", "+ Add button"),
        "Layout": pgettext("editor_js", "Layout"),
        "Grouped on the left": pgettext("editor_js", "Grouped on the left"),
        "Grouped in the center": pgettext("editor_js", "Grouped in the center"),
        "Grouped on the right": pgettext("editor_js", "Grouped on the right"),
        "Spread": pgettext("editor_js", "Spread"),
        "Fill": pgettext("editor_js", "Fill"),
        "Spacing": pgettext("editor_js", "Spacing"),
        "Small": pgettext("editor_js button spacing", "Small"),
        "Medium": pgettext("editor_js button spacing", "Medium"),
        "Large": pgettext("editor_js button spacing", "Large"),
    }


def _spacer_messages():
    return {
        "Small": pgettext("editor_js spacer size", "Small"),
        "Medium": pgettext("editor_js spacer size", "Medium"),
        "Large": pgettext("editor_js spacer size", "Large"),
    }


def _link_messages():
    return {
        "Add a link": pgettext("editor_js", "Add a link"),
        "Open in new tab": pgettext("editor_js", "Open in new tab"),
        "Save link (Enter)": pgettext("editor_js", "Save link (Enter)"),
        "Pasted link is not valid.": pgettext("editor_js", "Pasted link is not valid."),
    }


def _font_size_messages():
    return {
        "Small": pgettext("editor_js font size", "Small"),
        "Normal": pgettext("editor_js font size", "Normal"),
        "Large": pgettext("editor_js font size", "Large"),
        "Huge": pgettext("editor_js font size", "Huge"),
    }


# The texts of each tool, by its class: Editor.js looks them up under the
# name the tool is registered with, which a project or a field may change,
# so the iframe files them under that name.
TOOL_MESSAGES = {
    "Header": _header_messages,
    "EditorjsList": _list_messages,
    "Quote": _quote_messages,
    "Table": _table_messages,
    "RawTool": _raw_messages,
    "Embed": _embed_messages,
    "ImageTool": _image_messages,
    "ButtonTool": _button_messages,
    "SpacerTool": _spacer_messages,
    "LinkWithTargetTool": _link_messages,
    "FontSizeTool": _font_size_messages,
}


def get_editor_js_i18n():
    """
    The texts of the editor in the active language: ``messages``, the
    ``i18n.messages`` of Editor.js without the texts of the tools;
    ``toolMessages``, the texts of each tool by its class; ``iframe``, the
    texts of the iframe around the editor.
    """
    return {
        "messages": _core_messages(),
        "toolMessages": {name: build() for name, build in TOOL_MESSAGES.items()},
        "iframe": _iframe_messages(),
    }


def _iframe_messages():
    return {
        "Convert selected blocks": pgettext("editor_js", "Convert selected blocks"),
        "Convert to bulleted list": pgettext("editor_js", "Convert to bulleted list"),
        "Bulleted list": pgettext("editor_js", "Bulleted list"),
        "Convert to numbered list": pgettext("editor_js", "Convert to numbered list"),
        "Numbered list": pgettext("editor_js", "Numbered list"),
        "Convert list items to paragraphs": pgettext("editor_js", "Convert list items to paragraphs"),
        "Paragraphs": pgettext("editor_js", "Paragraphs"),
    }
