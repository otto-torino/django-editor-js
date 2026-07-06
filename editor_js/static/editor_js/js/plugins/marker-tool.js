/**
 * Inline highlight tool: wraps the selection in <mark class="cdx-marker">.
 * Faithful port of the official @editorjs/marker tool.
 */
class MarkerTool {
    static get isInline() {
        return true;
    }

    static get title() {
        return 'Highlight';
    }

    static get CSS() {
        return 'cdx-marker';
    }

    // Keep the mark tag when Editor.js sanitizes inline content on save.
    static get sanitize() {
        return {
            mark: {
                class: true
            }
        };
    }

    constructor({ api }) {
        this.api = api;
        this.button = null;
        this.iconClasses = {
            base: this.api.styles.inlineToolButton,
            active: this.api.styles.inlineToolButtonActive
        };
    }

    render() {
        this.button = document.createElement('button');
        this.button.type = 'button';
        this.button.classList.add(this.iconClasses.base);
        this.button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24"><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12.4 6.4L15 3.8a1.98 1.98 0 0 1 2.8 0l2.4 2.4a1.98 1.98 0 0 1 0 2.8l-2.6 2.6M12.4 6.4l-6.8 6.8a2 2 0 0 0-.6 1.4v2.4a1 1 0 0 0 1 1h2.4a2 2 0 0 0 1.4-.6l6.8-6.8M12.4 6.4l5.2 5.2M4 21h9"/></svg>';
        return this.button;
    }

    surround(range) {
        if (!range) {
            return;
        }

        const termWrapper = this.api.selection.findParentTag('MARK', MarkerTool.CSS);

        if (termWrapper) {
            this.unwrap(termWrapper);
        } else {
            this.wrap(range);
        }
    }

    wrap(range) {
        const marker = document.createElement('mark');

        marker.classList.add(MarkerTool.CSS);
        marker.appendChild(range.extractContents());
        range.insertNode(marker);

        this.api.selection.expandToTag(marker);
    }

    unwrap(termWrapper) {
        this.api.selection.expandToTag(termWrapper);

        const selection = window.getSelection();
        const range = selection.getRangeAt(0);
        const unwrappedContent = range.extractContents();

        termWrapper.parentNode.removeChild(termWrapper);
        range.insertNode(unwrappedContent);

        selection.removeAllRanges();
        selection.addRange(range);
    }

    checkState() {
        const termTag = this.api.selection.findParentTag('MARK', MarkerTool.CSS);
        this.button.classList.toggle(this.iconClasses.active, !!termTag);
        return !!termTag;
    }

    get shortcut() {
        return 'CMD+SHIFT+M';
    }
}

window.MarkerTool = MarkerTool;
