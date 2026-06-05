/**
 * Django EditorJS <-> Django Baton AI adapter
 *
 * Registers an editor adapter on Baton.AI so that Baton's AI features
 * (translation, summarization, correction) work on django-editor-js fields,
 * coexisting with CKEditor and native inputs on the same form.
 *
 * Baton AI works with flat text/HTML per field, while Editor.js stores a JSON
 * block structure inside an iframe-hosted editor. This adapter bridges the two:
 *   - reading  -> parse the hidden textarea JSON and render text-bearing blocks to HTML
 *   - writing  -> parse the AI HTML back into Editor.js blocks and re-render the editor
 *
 * Include this script in admin/base_site.html AFTER baton.min.js and
 * editor_js_widget.js, and BEFORE init_baton.js.
 *
 * @version 0.1.0
 * @author Otto
 */
(function (window, document) {
    'use strict';

    // --- Editor.js blocks -> HTML (mirrors editor_js/renderers.py) ---------

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text == null ? '' : String(text);
        return div.innerHTML;
    }

    function renderList(data) {
        const tag = data.style === 'ordered' ? 'ol' : 'ul';
        const items = (data.items || []).map(function (item) {
            if (item && typeof item === 'object') {
                const content = item.content != null ? item.content : '';
                const nested = item.items && item.items.length
                    ? renderList({ style: item.style, items: item.items })
                    : '';
                return '<li>' + content + nested + '</li>';
            }
            return '<li>' + item + '</li>';
        }).join('');
        return '<' + tag + '>' + items + '</' + tag + '>';
    }

    function blocksToHtml(content) {
        if (!content || !content.blocks) return '';
        return content.blocks.map(function (block) {
            const d = block.data || {};
            switch (block.type) {
                case 'paragraph':
                    return '<p>' + (d.text || '') + '</p>';
                case 'header': {
                    const lvl = d.level || 2;
                    return '<h' + lvl + '>' + (d.text || '') + '</h' + lvl + '>';
                }
                case 'list':
                    return renderList(d);
                case 'quote':
                    return '<blockquote><p>' + (d.text || '') + '</p>' +
                        '<footer>' + (d.caption || '') + '</footer></blockquote>';
                case 'code':
                    return '<pre><code>' + escapeHtml(d.code || '') + '</code></pre>';
                default:
                    // Non text-bearing blocks (image, table, embed, button,
                    // divider, raw...) are intentionally skipped: they carry no
                    // translatable prose and are preserved by setData only when
                    // the round-trip can rebuild them (see htmlToBlocks).
                    return '';
            }
        }).join('');
    }

    // --- HTML (AI output) -> Editor.js blocks ------------------------------

    function liToItems(listEl) {
        return Array.prototype.map.call(listEl.children, function (li) {
            return li.tagName && li.tagName.toLowerCase() === 'li' ? li.innerHTML.trim() : '';
        }).filter(function (s) { return s !== ''; });
    }

    function htmlToBlocks(htmlString) {
        const container = document.createElement('div');
        container.innerHTML = htmlString || '';
        const blocks = [];

        Array.prototype.forEach.call(container.childNodes, function (node) {
            // Bare text node -> paragraph
            if (node.nodeType !== 1) {
                const text = (node.textContent || '').trim();
                if (text) blocks.push({ type: 'paragraph', data: { text: text } });
                return;
            }

            const tag = node.tagName.toLowerCase();
            const headerMatch = /^h([1-6])$/.exec(tag);

            if (headerMatch) {
                blocks.push({ type: 'header', data: { text: node.innerHTML.trim(), level: parseInt(headerMatch[1], 10) } });
            } else if (tag === 'ul' || tag === 'ol') {
                blocks.push({ type: 'list', data: { style: tag === 'ol' ? 'ordered' : 'unordered', items: liToItems(node) } });
            } else if (tag === 'blockquote') {
                const p = node.querySelector('p');
                const footer = node.querySelector('footer');
                blocks.push({ type: 'quote', data: {
                    text: (p ? p.innerHTML : node.innerHTML).trim(),
                    caption: footer ? footer.innerHTML.trim() : ''
                } });
            } else if (tag === 'pre') {
                const code = node.querySelector('code');
                blocks.push({ type: 'code', data: { code: (code ? code.textContent : node.textContent) || '' } });
            } else if (tag === 'hr') {
                blocks.push({ type: 'divider', data: {} });
            } else {
                const inner = node.innerHTML.trim();
                if (inner) blocks.push({ type: 'paragraph', data: { text: inner } });
            }
        });

        if (!blocks.length) {
            blocks.push({ type: 'paragraph', data: { text: '' } });
        }
        return { blocks: blocks };
    }

    // --- Field id <-> widget name helpers ----------------------------------

    // Baton works with DOM field ids; django-editor-js textareas are `id_<name>`.
    function fieldIdToName(fieldId) {
        return fieldId.indexOf('id_') === 0 ? fieldId.slice(3) : fieldId;
    }

    function isEditorJsField(fieldId) {
        const name = fieldIdToName(fieldId);
        const names = window.DjangoEditorJSWidget.getNames();
        return names.indexOf(name) !== -1;
    }

    // --- The Baton AI adapter ----------------------------------------------

    const EditorJsBatonAdapter = {
        name: 'django-editor-js',

        getFields: function () {
            return window.DjangoEditorJSWidget.getNames().map(function (name) {
                return 'id_' + name;
            });
        },

        getValue: function (fieldId) {
            if (!isEditorJsField(fieldId)) return undefined;
            const data = window.DjangoEditorJSWidget.getData(fieldIdToName(fieldId));
            return blocksToHtml(data);
        },

        setValue: function (fieldId, value) {
            if (!isEditorJsField(fieldId)) return false;
            return window.DjangoEditorJSWidget.setData(fieldIdToName(fieldId), htmlToBlocks(value));
        },

        setCorrect: function (fieldId, icon) {
            if (!isEditorJsField(fieldId)) return false;
            const wrapper = document.getElementById(fieldId + '_wrapper');
            if (!wrapper) return false;
            wrapper.parentNode.insertBefore(icon, wrapper.nextSibling);
            return true;
        }
    };

    // --- Registration ------------------------------------------------------

    function register() {
        if (window.Baton && window.Baton.AI && typeof window.Baton.AI.registerEditorAdapter === 'function') {
            window.Baton.AI.registerEditorAdapter(EditorJsBatonAdapter);
            return true;
        }
        return false;
    }

    // Baton must be loaded first. Register now if available, otherwise retry on
    // DOMContentLoaded (covers script ordering differences). When Baton is not
    // installed at all we stay silent: this script ships with django-editor-js
    // and is harmless on projects that don't use Baton.
    if (!register()) {
        document.addEventListener('DOMContentLoaded', function () {
            if (register()) return;
            // Only warn if Baton is present but lacks the adapter API (too old).
            if (window.Baton && window.Baton.AI) {
                console.warn('[editor-js] Baton.AI is present but does not support ' +
                    'registerEditorAdapter (upgrade django-baton to >= 5.2). ' +
                    'AI features for Editor.js are disabled.');
            }
        });
    }

    // Expose helpers for testing / advanced reuse
    window.DjangoEditorJSBatonAdapter = {
        adapter: EditorJsBatonAdapter,
        blocksToHtml: blocksToHtml,
        htmlToBlocks: htmlToBlocks
    };

})(window, document);
