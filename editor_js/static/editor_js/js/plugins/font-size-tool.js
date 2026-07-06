/**
 * Inline font size tool: wraps the selection in
 * <span class="cdx-font-size" style="font-size: ..."> using a set of preset
 * sizes. The inline toolbar popover shows renderActions() as a nested panel
 * when the tool button is clicked.
 */
class FontSizeTool {
    static get isInline() {
        return true;
    }

    static get title() {
        return 'Font size';
    }

    static get CSS() {
        return 'cdx-font-size';
    }

    // Keep the span and its attributes when Editor.js sanitizes inline
    // content on save.
    static get sanitize() {
        return {
            span: {
                class: true,
                style: true
            }
        };
    }

    static get SIZES() {
        return [
            { label: 'Small', value: '0.75em' },
            { label: 'Normal', value: null },
            { label: 'Large', value: '1.4em' },
            { label: 'Huge', value: '1.8em' }
        ];
    }

    constructor({ api }) {
        this.api = api;
        this.nodes = {
            button: null,
            actions: null
        };
        this.selection = api.selection;
        this.inlineToolbar = api.inlineToolbar;
        this.i18n = api.i18n;
    }

    render() {
        this.nodes.button = document.createElement('button');
        this.nodes.button.type = 'button';
        this.nodes.button.classList.add(this.api.styles.inlineToolButton);
        this.nodes.button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24"><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 18L9 6l4 12M6.3 14.5h5.4M17 8v8M14.8 13.8L17 16l2.2-2.2M19.2 10.2L17 8l-2.2 2.2"/></svg>';
        return this.nodes.button;
    }

    renderActions() {
        this.nodes.actions = document.createElement('div');
        this.nodes.actions.style.display = 'flex';
        this.nodes.actions.style.alignItems = 'center';
        this.nodes.actions.style.gap = '2px';
        this.nodes.actions.style.padding = '4px';

        FontSizeTool.SIZES.forEach((size) => {
            const sizeButton = document.createElement('button');
            sizeButton.type = 'button';
            sizeButton.classList.add(this.api.styles.inlineToolButton);
            sizeButton.style.width = 'auto';
            sizeButton.style.padding = '0 8px';
            sizeButton.style.fontSize = size.value || '1em';
            sizeButton.textContent = this.i18n.t(size.label);
            sizeButton.addEventListener('click', () => this.apply(size.value));
            this.nodes.actions.appendChild(sizeButton);
        });

        return this.nodes.actions;
    }

    surround() {
        // The nested panel is opened by the popover itself; here we only
        // remember the selection. save()/restore() are pure JS: DOM-mutating
        // helpers (like the link tool's fake background) would fire a
        // selectionchange that makes the editor rebuild the toolbar, closing
        // the nested panel.
        this.selection.save();
    }

    checkState() {
        const span = this.getActiveSpan();
        this.nodes.button.classList.toggle(this.api.styles.inlineToolButtonActive, !!span);
        return !!span;
    }

    /**
     * Returns the sized span the selection lives in, if any. Besides
     * findParentTag (which walks up from the selection's anchor node), it
     * also covers ranges whose container IS the span itself — the state
     * left by expandToTag after a previous apply.
     */
    getActiveSpan() {
        const parentSpan = this.selection.findParentTag('SPAN', FontSizeTool.CSS);
        if (parentSpan) {
            return parentSpan;
        }

        const selection = window.getSelection();
        if (!selection || !selection.rangeCount) {
            return null;
        }

        let node = selection.getRangeAt(0).commonAncestorContainer;
        while (node && node.nodeType !== Node.DOCUMENT_NODE) {
            if (node.nodeType === Node.ELEMENT_NODE && node.classList.contains(FontSizeTool.CSS)) {
                return node;
            }
            node = node.parentNode;
        }
        return null;
    }

    apply(fontSize) {
        this.selection.restore();

        // Selection inside (or coinciding with) an already sized span:
        // update it in place or remove it, never nest a new one.
        const existing = this.getActiveSpan();
        if (existing) {
            if (fontSize) {
                existing.style.fontSize = fontSize;
            } else {
                this.unwrap(existing);
            }
            this.inlineToolbar.close();
            return;
        }

        this.wrap(fontSize);
        this.inlineToolbar.close();
    }

    wrap(fontSize) {
        const selection = window.getSelection();
        if (!selection || !selection.rangeCount) {
            return;
        }

        const range = selection.getRangeAt(0);
        if (range.collapsed) {
            return;
        }

        // Strip any sized span contained in the selection, so sizes never
        // stack (em values would compound) and "Normal" clears them.
        const fragment = range.extractContents();
        fragment.querySelectorAll(`span.${FontSizeTool.CSS}`).forEach((inner) => {
            this.unwrap(inner);
        });

        if (!fontSize) {
            range.insertNode(fragment);
            return;
        }

        const span = document.createElement('span');
        span.classList.add(FontSizeTool.CSS);
        span.style.fontSize = fontSize;
        span.appendChild(fragment);
        range.insertNode(span);

        this.selection.expandToTag(span);
    }

    unwrap(span) {
        const parent = span.parentNode;
        while (span.firstChild) {
            parent.insertBefore(span.firstChild, span);
        }
        parent.removeChild(span);
        parent.normalize();
    }
}

window.FontSizeTool = FontSizeTool;
