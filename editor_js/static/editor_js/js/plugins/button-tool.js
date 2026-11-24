/**
 * A row of buttons. Its data is `{alignment, distribution, gap, buttons:
 * [{text, url, btnColor}]}`; a block saved before rows existed holds one
 * button in `{text, url, btnColor, alignment}` and is read as a row of one.
 *
 * distribution: "grouped" (side by side, placed by alignment), "spread"
 * (first and last button at the edges) or "fill" (equal widths filling the
 * row). gap: "small", "medium" or "large". The renderer in renderers.py
 * draws the row the same way.
 */
const BUTTON_JUSTIFY = { left: 'flex-start', center: 'center', right: 'flex-end' };
const BUTTON_GAPS = { small: '0.5rem', medium: '1rem', large: '2rem' };
const BUTTON_DISTRIBUTIONS = ['grouped', 'spread', 'fill'];
// Two buttons in a row, between the edges of the row.
const BUTTON_LAYOUT_ICON = (buttons) => '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="24" viewBox="0 0 36 24" fill="none" aria-hidden="true">' +
    '<path d="M2 4v16M34 4v16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity=".45"/>' +
    buttons.map(([x, width]) => `<rect x="${x}" y="8.5" width="${width}" height="7" rx="2" fill="currentColor"/>`).join('') +
    '</svg>';
const BUTTON_LAYOUT_ICONS = {
    'grouped-left': BUTTON_LAYOUT_ICON([[5, 10], [16.5, 10]]),
    'grouped-center': BUTTON_LAYOUT_ICON([[7.25, 10], [18.75, 10]]),
    'grouped-right': BUTTON_LAYOUT_ICON([[9.5, 10], [21, 10]]),
    spread: BUTTON_LAYOUT_ICON([[5, 10], [21, 10]]),
    fill: BUTTON_LAYOUT_ICON([[5, 12.5], [18.5, 12.5]])
};
// Two buttons and the space between them: no edges, unlike the layouts.
const BUTTON_GAP_ICON = (buttons) => '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="24" viewBox="0 0 36 24" fill="none" aria-hidden="true">' +
    buttons.map(([x, width]) => `<rect x="${x}" y="8.5" width="${width}" height="7" rx="2" fill="currentColor"/>`).join('') +
    '</svg>';
const BUTTON_GAP_ICONS = {
    small: BUTTON_GAP_ICON([[9.25, 8], [18.75, 8]]),
    medium: BUTTON_GAP_ICON([[7, 8], [21, 8]]),
    large: BUTTON_GAP_ICON([[3, 8], [25, 8]])
};
// A bin, to remove a button from the row.
const BUTTON_REMOVE_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6"/></svg>';
// The style of each button of a row, as BUTTON_STYLES in renderers.py.
const BUTTON_STYLES = {
    grouped: {},
    fill: { flex: '1 1 0', minWidth: 'fit-content' },
    spread: { flex: '0 1 calc((36rem - 100%) * 999)', minWidth: 'fit-content' }
};

class ButtonTool {
    static get toolbox() {
        return {
            title: 'Button',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="8" rx="2"></rect></svg>'
        };
    }

    constructor({ data, api, block }) {
        this.api = api;
        this.block = block;

        const buttons = Array.isArray(data.buttons) ? data.buttons : [data];
        this.data = {
            alignment: ButtonTool._pick(data.alignment, Object.keys(BUTTON_JUSTIFY), 'left'),
            distribution: ButtonTool._pick(data.distribution, BUTTON_DISTRIBUTIONS, 'grouped'),
            gap: ButtonTool._pick(data.gap, Object.keys(BUTTON_GAPS), 'small'),
            buttons: buttons.map((button) => this._newButton(button))
        };
        if (!this.data.buttons.length) {
            this.data.buttons.push(this._newButton());
        }

        this.wrapper = null;
        this.row = null;
        this.missingUrlHint = null;
        this.settingsContainer = null;
        this.urlInputs = [];
    }

    static _pick(value, allowed, fallback) {
        return allowed.includes(value) ? value : fallback;
    }

    // A text of the tool in the language of the editor (editor_js/i18n.py).
    _t(text) {
        return this.api.i18n.t(text);
    }

    // The same, ready for innerHTML.
    _html(text) {
        const element = document.createElement('span');
        element.textContent = this._t(text);
        return element.innerHTML;
    }

    _newButton(button = {}) {
        return {
            text: button.text || this._t('Click me'),
            url: button.url || '',
            btnColor: button.btnColor || 'btn-primary'
        };
    }

    static _isComplete(button) {
        return Boolean(button.text.trim() && button.url.trim());
    }

    render() {
        this.wrapper = document.createElement('div');

        this.row = document.createElement('div');
        this.row.className = 'button-row';
        this.row.style.display = 'flex';
        this.row.style.flexWrap = 'wrap';

        this.missingUrlHint = document.createElement('div');
        this.missingUrlHint.className = 'button-missing-url-hint';
        this.missingUrlHint.innerText = this._t('Add a URL to every button in the block settings: a button without one will not be saved.');

        this.wrapper.appendChild(this.row);
        this.wrapper.appendChild(this.missingUrlHint);
        this._updatePreview();
        this._updateMissingUrlState();
        return this.wrapper;
    }

    renderSettings() {
        this.settingsContainer = document.createElement('div');
        this._fillSettings();
        return this.settingsContainer;
    }

    save() {
        // A button without text or url is left out, as a block without them
        // was before rows existed.
        return {
            alignment: this.data.alignment,
            distribution: this.data.distribution,
            gap: this.data.gap,
            buttons: this.data.buttons
                .filter((button) => ButtonTool._isComplete(button))
                .map((button) => ({ ...button }))
        };
    }

    validate(savedData) {
        return savedData.buttons.length > 0;
    }

    _fillSettings() {
        const container = this.settingsContainer;
        if (!container) return;
        container.innerHTML = '';
        this.urlInputs = [];

        const iconText = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 6.1H3"/><path d="M21 12.1H3"/><path d="M15.1 18.1H3"/></svg>';
        const iconLink = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.72"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.72-1.72"/></svg>';
        const several = this.data.buttons.length > 1;

        this.data.buttons.forEach((button, index) => {
            const item = document.createElement('div');
            item.className = 'button-settings-item';

            if (several) {
                const title = document.createElement('div');
                title.className = 'button-settings-item-title';
                title.innerText = this._t('Button %(number)s').replace('%(number)s', index + 1);
                item.appendChild(title);
            }

            item.appendChild(this._createSettingInput({
                icon: iconText,
                placeholder: this._t('Click me'),
                value: button.text,
                onInput: (value) => {
                    button.text = value;
                    this._updatePreview();
                }
            }));

            const urlInput = this._createSettingInput({
                icon: iconLink,
                placeholder: 'https://example.com',
                value: button.url,
                onInput: (value) => {
                    button.url = value;
                    this._updateMissingUrlState();
                }
            });
            this.urlInputs.push(urlInput.querySelector('input'));
            item.appendChild(urlInput);

            const actions = document.createElement('div');
            actions.className = 'button-settings-actions';
            const colors = [
                { name: 'Primary', value: 'btn-primary' },
                { name: 'Secondary', value: 'btn-secondary' }
            ];
            const colorButtons = [];
            colors.forEach((color) => {
                const colorButton = this._createStyleButton(this._html(color.name), () => {
                    button.btnColor = color.value;
                    this._updatePreview();
                    this._setActive(colorButtons, colorButton);
                });
                colorButtons.push(colorButton);
                if (button.btnColor === color.value) this._setActive([colorButton], colorButton);
                actions.appendChild(colorButton);
            });

            if (several) {
                const remove = this._createStyleButton(BUTTON_REMOVE_ICON, () => {
                    this.data.buttons.splice(this.data.buttons.indexOf(button), 1);
                    this._buttonsChanged();
                }, 'button-settings-remove');
                // an icon says its name on hover, and to a screen reader
                remove.title = this._t('Remove');
                remove.setAttribute('aria-label', this._t('Remove'));
                actions.appendChild(remove);
            }

            item.appendChild(actions);
            container.appendChild(item);
        });

        const addButton = this._createStyleButton(this._html('+ Add button'), () => {
            this.data.buttons.push(this._newButton());
            this._buttonsChanged();
        }, 'button-settings-add');
        container.appendChild(addButton);

        // one choice for where the buttons go: the alignment places only a
        // grouped row, the other layouts use the whole width
        container.appendChild(this._createSettingsTitle('Layout'));
        container.appendChild(this._createChoiceRow(
            [
                { value: 'grouped-left', label: 'Grouped on the left', icon: BUTTON_LAYOUT_ICONS['grouped-left'] },
                { value: 'grouped-center', label: 'Grouped in the center', icon: BUTTON_LAYOUT_ICONS['grouped-center'] },
                { value: 'grouped-right', label: 'Grouped on the right', icon: BUTTON_LAYOUT_ICONS['grouped-right'] },
                { value: 'spread', label: 'Spread', icon: BUTTON_LAYOUT_ICONS.spread },
                { value: 'fill', label: 'Fill', icon: BUTTON_LAYOUT_ICONS.fill }
            ],
            this.data.distribution === 'grouped' ? `grouped-${this.data.alignment}` : this.data.distribution,
            (value) => {
                const [distribution, alignment] = value.split('-');
                this.data.distribution = distribution;
                if (alignment) this.data.alignment = alignment;
            }
        ));

        container.appendChild(this._createSettingsTitle('Spacing'));
        container.appendChild(this._createChoiceRow(
            [
                { value: 'small', label: 'Small', icon: BUTTON_GAP_ICONS.small },
                { value: 'medium', label: 'Medium', icon: BUTTON_GAP_ICONS.medium },
                { value: 'large', label: 'Large', icon: BUTTON_GAP_ICONS.large }
            ],
            this.data.gap,
            (value) => { this.data.gap = value; }
        ));

        this._updateMissingUrlState();
    }

    _createSettingsTitle(text) {
        const title = document.createElement('div');
        title.className = 'button-settings-item-title button-settings-row-title';
        title.innerText = this._t(text);
        return title;
    }

    // A row of settings buttons of which one is active at a time.
    _createChoiceRow(choices, current, onChoose) {
        const wrapper = document.createElement('div');
        wrapper.className = 'button-settings-actions';
        const buttons = [];
        choices.forEach((choice) => {
            const content = choice.icon || this._html(choice.label);
            const button = this._createStyleButton(content, () => {
                onChoose(choice.value);
                this._updatePreview();
                this._setActive(buttons, button);
            });
            // an icon says its name on hover, and to a screen reader
            if (choice.icon) {
                button.title = this._t(choice.label);
                button.setAttribute('aria-label', this._t(choice.label));
                button.classList.add('button-settings-icon-choice');
            }
            buttons.push(button);
            if (choice.value === current) this._setActive([button], button);
            wrapper.appendChild(button);
        });
        return wrapper;
    }

    // Adding or removing a button rebuilds the settings. It waits for the
    // click to end: a clicked element taken out of the page reads to Editor.js
    // as a click outside of it, which closes the settings.
    _buttonsChanged() {
        this._updatePreview();
        this._updateMissingUrlState();
        this._dispatchChange();
        setTimeout(() => this._fillSettings(), 0);
    }

    _updatePreview() {
        if (!this.row) return;
        const buttonStyle = BUTTON_STYLES[this.data.distribution];
        this.row.style.gap = BUTTON_GAPS[this.data.gap];
        this.row.style.justifyContent = this.data.distribution === 'spread'
            ? 'space-between'
            : BUTTON_JUSTIFY[this.data.alignment];
        this.row.innerHTML = '';
        this.data.buttons.forEach((button) => {
            const preview = document.createElement('div');
            preview.className = 'btn';
            preview.classList.add(button.btnColor);
            preview.innerText = button.text;
            Object.assign(preview.style, buttonStyle);
            this.row.appendChild(preview);
        });
    }

    // save() leaves out a button without url: flag it while editing.
    _updateMissingUrlState() {
        const missing = this.data.buttons.some((button) => !button.url.trim());
        if (this.missingUrlHint) this.missingUrlHint.hidden = !missing;
        this.urlInputs.forEach((input, index) => {
            const button = this.data.buttons[index];
            input.classList.toggle('button-settings-input-invalid', Boolean(button) && !button.url.trim());
        });
    }

    _createSettingInput({ icon, placeholder, value, onInput }) {
        const wrapper = document.createElement('div');
        wrapper.classList.add('button-settings-input-wrapper');
        const iconElement = document.createElement('span');
        iconElement.classList.add('button-settings-input-icon');
        iconElement.innerHTML = icon;
        const input = document.createElement('input');
        input.placeholder = placeholder;
        input.value = value;
        input.className = this.api.styles.input;
        input.addEventListener('input', () => {
            onInput(input.value);
            this._dispatchChange();
        });
        wrapper.appendChild(iconElement);
        wrapper.appendChild(input);
        return wrapper;
    }

    _createStyleButton(innerHTML, onClick, extraClass) {
        const button = document.createElement('button');
        button.type = 'button';
        button.classList.add(this.api.styles.settingsButton);
        if (extraClass) button.classList.add(extraClass);
        button.innerHTML = innerHTML;
        button.onclick = () => {
            onClick();
            this._dispatchChange();
        };
        return button;
    }

    _setActive(buttons, active) {
        buttons.forEach((button) => {
            button.classList.toggle(this.api.styles.settingsButtonActive, button === active);
        });
    }

    // The settings inputs live outside the block, so Editor.js does not see
    // their edits: notify it, or the saved data keeps the old values (and a
    // button saved without url is left out by save()).
    _dispatchChange() {
        if (this.block) this.block.dispatchChange();
    }
}

window.ButtonTool = ButtonTool;
