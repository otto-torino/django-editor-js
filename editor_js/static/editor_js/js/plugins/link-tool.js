/**
 * Faithful port of the native Editor.js inline link tool (same icons, CSS
 * classes and save mechanism), with one addition: an "Open in new tab"
 * checkbox that saves target="_blank" + rel="noopener noreferrer".
 */
class LinkWithTargetTool {
    static get isInline() {
        return true;
    }

    static get title() {
        return 'Link';
    }

    // Keep target/rel when Editor.js sanitizes inline content on save.
    static get sanitize() {
        return {
            a: {
                href: true,
                target: true,
                rel: true
            }
        };
    }

    static get ICON_LINK() {
        return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24"><path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="M7.69998 12.6L7.67896 12.62C6.53993 13.7048 6.52012 15.5155 7.63516 16.625V16.625C8.72293 17.7073 10.4799 17.7102 11.5712 16.6314L13.0263 15.193C14.0703 14.1609 14.2141 12.525 13.3662 11.3266L13.22 11.12"/><path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="M16.22 11.12L16.3564 10.9805C17.2895 10.0265 17.3478 8.5207 16.4914 7.49733V7.49733C15.5691 6.39509 13.9269 6.25143 12.8271 7.17675L11.3901 8.38588C10.0935 9.47674 9.95706 11.4241 11.0888 12.6852L11.12 12.72"/></svg>';
    }

    static get ICON_UNLINK() {
        return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24"><path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="M15.7795 11.5C15.7795 11.5 16.053 11.1962 16.5497 10.6722C17.4442 9.72856 17.4701 8.2475 16.5781 7.30145V7.30145C15.6482 6.31522 14.0873 6.29227 13.1288 7.25073L11.8796 8.49999"/><path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="M8.24517 12.3883C8.24517 12.3883 7.97171 12.6922 7.47504 13.2161C6.58051 14.1598 6.55467 15.6408 7.44666 16.5869V16.5869C8.37653 17.5731 9.93744 17.5961 10.8959 16.6376L12.1452 15.3883"/><path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="M17.7802 15.1032L16.597 14.9422C16.0109 14.8624 15.4841 15.3059 15.4627 15.8969L15.4199 17.0818"/><path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="M6.39064 9.03238L7.58432 9.06668C8.17551 9.08366 8.6522 8.58665 8.61056 7.99669L8.5271 6.81397"/><line x1="12.1142" x2="11.7" y1="12.2" y2="11.7858" stroke="currentColor" stroke-linecap="round" stroke-width="2"/></svg>';
    }

    constructor({ api }) {
        this.commandLink = 'createLink';
        this.commandUnlink = 'unlink';
        this.ENTER_KEY = 13;
        this.CSS = {
            button: 'ce-inline-tool',
            buttonActive: 'ce-inline-tool--active',
            buttonModifier: 'ce-inline-tool--link',
            buttonUnlink: 'ce-inline-tool--unlink',
            input: 'ce-inline-tool-input',
            inputShowed: 'ce-inline-tool-input--showed'
        };
        this.nodes = {
            button: null,
            wrapper: null,
            input: null,
            checkboxRow: null,
            checkbox: null
        };
        this.inputOpened = false;
        this.fakeBackgroundEnabled = false;
        this.toolbar = api.toolbar;
        this.inlineToolbar = api.inlineToolbar;
        this.notifier = api.notifier;
        this.i18n = api.i18n;
        this.selection = api.selection;
    }

    render() {
        this.nodes.button = document.createElement('button');
        this.nodes.button.type = 'button';
        this.nodes.button.classList.add(this.CSS.button, this.CSS.buttonModifier);
        this.nodes.button.innerHTML = LinkWithTargetTool.ICON_LINK;
        return this.nodes.button;
    }

    renderActions() {
        this.nodes.wrapper = document.createElement('div');

        this.nodes.input = document.createElement('input');
        this.nodes.input.placeholder = this.i18n.t('Add a link');
        this.nodes.input.enterKeyHint = 'done';
        this.nodes.input.classList.add(this.CSS.input);
        this.nodes.input.addEventListener('keydown', (event) => {
            if (event.keyCode === this.ENTER_KEY) {
                this.enterPressed(event);
            }
        });

        this.nodes.checkboxRow = document.createElement('div');
        this.nodes.checkboxRow.style.display = 'none';
        this.nodes.checkboxRow.style.alignItems = 'center';
        this.nodes.checkboxRow.style.gap = '6px';
        this.nodes.checkboxRow.style.padding = '4px 8px 8px';
        this.nodes.checkboxRow.style.fontSize = '13px';

        const checkboxLabel = document.createElement('label');
        checkboxLabel.style.display = 'flex';
        checkboxLabel.style.alignItems = 'center';
        checkboxLabel.style.gap = '6px';
        checkboxLabel.style.cursor = 'pointer';

        this.nodes.checkbox = document.createElement('input');
        this.nodes.checkbox.type = 'checkbox';
        this.nodes.checkbox.addEventListener('keydown', (event) => {
            if (event.keyCode === this.ENTER_KEY) {
                this.enterPressed(event);
            }
        });

        checkboxLabel.appendChild(this.nodes.checkbox);
        checkboxLabel.appendChild(
            document.createTextNode(this.i18n.t('Open in new tab'))
        );

        this.nodes.checkboxRow.appendChild(checkboxLabel);

        this.nodes.wrapper.appendChild(this.nodes.input);
        this.nodes.wrapper.appendChild(this.nodes.checkboxRow);

        return this.nodes.wrapper;
    }

    surround(range) {
        if (range) {
            if (this.inputOpened) {
                this.selection.restore();
                this.removeFakeBackground();
            } else {
                this.setFakeBackground();
                this.selection.save();
            }

            const parentAnchor = this.selection.findParentTag('A');

            if (parentAnchor) {
                if (this.inputOpened) {
                    this.closeActions(false);
                    this.checkState();
                } else {
                    this.selection.expandToTag(parentAnchor);
                    this.unlink();
                    this.closeActions();
                    this.checkState();
                    this.toolbar.close();
                }
                return;
            }
        }
        this.toggleActions();
    }

    checkState() {
        const anchorTag = this.selection.findParentTag('A');

        if (anchorTag) {
            this.nodes.button.innerHTML = LinkWithTargetTool.ICON_UNLINK;
            this.nodes.button.classList.add(this.CSS.buttonUnlink);
            this.nodes.button.classList.add(this.CSS.buttonActive);
            this.openActions();

            const hrefAttr = anchorTag.getAttribute('href');
            this.nodes.input.defaultValue = hrefAttr !== 'null' ? hrefAttr : '';
            this.nodes.checkbox.checked = anchorTag.target === '_blank';
            this.selection.save();
        } else {
            this.nodes.button.innerHTML = LinkWithTargetTool.ICON_LINK;
            this.nodes.button.classList.remove(this.CSS.buttonUnlink);
            this.nodes.button.classList.remove(this.CSS.buttonActive);
        }

        return !!anchorTag;
    }

    clear() {
        this.closeActions();
    }

    get shortcut() {
        return 'CMD+K';
    }

    toggleActions() {
        if (this.inputOpened) {
            this.closeActions(false);
        } else {
            this.openActions(true);
        }
    }

    openActions(needFocus = false) {
        this.nodes.input.classList.add(this.CSS.inputShowed);
        this.nodes.checkboxRow.style.display = 'flex';
        if (needFocus) {
            this.nodes.input.focus();
        }
        this.inputOpened = true;
    }

    closeActions(clearSavedSelection = true) {
        if (this.fakeBackgroundEnabled) {
            // Preserve the current selection while removing the fake
            // background applied to the saved one (as the native tool does).
            const currentSelection = window.getSelection();
            const currentRange = currentSelection.rangeCount
                ? currentSelection.getRangeAt(0).cloneRange()
                : null;

            this.selection.restore();
            this.removeFakeBackground();

            if (currentRange) {
                currentSelection.removeAllRanges();
                currentSelection.addRange(currentRange);
            }
        }

        this.nodes.input.classList.remove(this.CSS.inputShowed);
        this.nodes.checkboxRow.style.display = 'none';
        this.nodes.input.value = '';
        this.nodes.checkbox.checked = false;
        this.inputOpened = false;
    }

    enterPressed(event) {
        this.saveLink(event);
    }

    saveLink(event) {
        let value = this.nodes.input.value || '';

        if (!value.trim()) {
            this.selection.restore();
            this.unlink();
            event.preventDefault();
            this.closeActions();
            return;
        }

        if (!this.validateURL(value)) {
            this.notifier.show({
                message: 'Pasted link is not valid.',
                style: 'error'
            });
            console.warn('Incorrect Link pasted', value);
            return;
        }

        value = this.prepareLink(value);

        this.selection.restore();
        this.removeFakeBackground();
        this.insertLink(value);

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        this.collapseToEnd();
        this.inlineToolbar.close();
    }

    validateURL(str) {
        return !/\s/.test(str);
    }

    prepareLink(link) {
        link = link.trim();
        link = this.addProtocol(link);
        return link;
    }

    addProtocol(link) {
        if (/^(\w+):(\/\/)?/.test(link)) {
            return link;
        }

        const isInternal = /^\/[^/\s]/.test(link);
        const isAnchor = link.substring(0, 1) === '#';
        const isProtocolRelative = /^\/\/[^/\s]/.test(link);

        if (!isInternal && !isAnchor && !isProtocolRelative) {
            link = 'http://' + link;
        }
        return link;
    }

    insertLink(link) {
        const anchorTag = this.selection.findParentTag('A');
        if (anchorTag) {
            this.selection.expandToTag(anchorTag);
        }
        document.execCommand(this.commandLink, false, link);

        // The only behavioral addition over the native tool: apply the
        // "open in new tab" choice to the created/updated anchor.
        const createdAnchor = this.selection.findParentTag('A');
        if (createdAnchor) {
            this.applyTarget(createdAnchor);
        }
    }

    unlink() {
        document.execCommand(this.commandUnlink);
    }

    applyTarget(anchor) {
        if (this.nodes.checkbox.checked) {
            anchor.setAttribute('target', '_blank');
            anchor.setAttribute('rel', 'noopener noreferrer');
        } else {
            anchor.removeAttribute('target');
            anchor.removeAttribute('rel');
        }
    }

    setFakeBackground() {
        this.selection.setFakeBackground();
        this.fakeBackgroundEnabled = true;
    }

    removeFakeBackground() {
        if (!this.fakeBackgroundEnabled) {
            return;
        }
        this.selection.removeFakeBackground();
        this.fakeBackgroundEnabled = false;
    }

    collapseToEnd() {
        const selection = window.getSelection();
        if (selection && selection.rangeCount) {
            selection.collapseToEnd();
        }
    }
}

window.LinkWithTargetTool = LinkWithTargetTool;
