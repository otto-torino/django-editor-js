class SpacerTool {
    static get toolbox() {
        return {
            title: 'Spacer',
            icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 3h12M4 17h12M10 6v8M7.5 8.5 10 6l2.5 2.5M7.5 11.5 10 14l2.5-2.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        };
    }

    static get isReadOnlySupported() {
        return true;
    }

    constructor({ data, api, readOnly }) {
        this.api = api;
        this.readOnly = readOnly;
        this.data = {
            size: ['small', 'medium', 'large'].includes(data.size) ? data.size : 'medium'
        };
        this.wrapper = null;
    }

    render() {
        this.wrapper = document.createElement('div');
        this.wrapper.classList.add('editor-js-spacer');
        this.wrapper.setAttribute('aria-hidden', 'true');
        this._updateSize();
        return this.wrapper;
    }

    renderSettings() {
        return [
            this._sizeSetting('small', 'Small'),
            this._sizeSetting('medium', 'Medium'),
            this._sizeSetting('large', 'Large')
        ];
    }

    save() {
        return this.data;
    }

    _sizeSetting(size, label) {
        return {
            label: label,
            icon: '<svg width="20" height="20" viewBox="0 0 20 20"><path d="M4 5h12M4 15h12M10 7v6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
            isActive: this.data.size === size,
            closeOnActivate: true,
            onActivate: () => {
                this.data.size = size;
                this._updateSize();
                if (this.wrapper) {
                    this.wrapper.dispatchEvent(new CustomEvent('change', { bubbles: true }));
                }
            }
        };
    }

    _updateSize() {
        if (!this.wrapper) return;
        this.wrapper.dataset.size = this.data.size;
    }
}

window.SpacerTool = SpacerTool;
