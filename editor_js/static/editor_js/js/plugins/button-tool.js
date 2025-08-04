class ButtonTool {
    static get toolbox() {
        return {
            title: 'Button',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="8" rx="2"></rect></svg>'
        };
    }

    constructor({ data, api }) {
        this.api = api;
        this.data = {
            text: data.text || 'Click me',
            url: data.url || '',
            btnColor: data.btnColor || 'btn-primary',
            alignment: data.alignment || 'left'
        };

        this.wrapper = null;
        this.preview = null;
    }

    render() {
        this.wrapper = document.createElement('div');
        this.preview = this._createPreview();
        
        this.wrapper.style.textAlign = this.data.alignment;

        this.wrapper.appendChild(this.preview);
        return this.wrapper;
    }

    renderSettings() {
        const settingsContainer = document.createElement('div');
        const iconText = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 6.1H3"/><path d="M21 12.1H3"/><path d="M15.1 18.1H3"/></svg>';
        const iconLink = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.72"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.72-1.72"/></svg>';
        
        const textInput = this._createSettingInput({
            icon: iconText,
            placeholder: 'Click me',
            value: this.data.text,
            onInput: (value) => {
                this.data.text = value;
                this._updatePreview();
            }
        });

        const urlInput = this._createSettingInput({
            icon: iconLink,
            placeholder: 'https://example.com',
            value: this.data.url,
            onInput: (value) => { this.data.url = value; }
        });
        urlInput.style.marginTop = '10px';

        const colorButtonsWrapper = document.createElement('div');
        colorButtonsWrapper.style.display = 'flex';
        colorButtonsWrapper.style.gap = '8px';
        colorButtonsWrapper.style.marginTop = '10px';
        
        const colors = [
            { name: 'Primary', value: 'btn-primary' },
            { name: 'Secondary', value: 'btn-secondary' }
        ];

        colors.forEach(color => {
            const button = this._createStyleButton(color.name, `color-${color.value}`, () => {
                this.data.btnColor = color.value;
                this._updatePreview();
                this._updateActiveButtons(settingsContainer);
            });
            colorButtonsWrapper.appendChild(button);
        });

        const alignButtonsWrapper = document.createElement('div');
        alignButtonsWrapper.style.display = 'flex';
        alignButtonsWrapper.style.gap = '8px';
        alignButtonsWrapper.style.marginTop = '8px';
        
        const alignments = [
            { name: 'left', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="17" y1="14" x2="3" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>' },
            { name: 'center', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="10" x2="6" y2="10"/><line x1="21" y1="6" x2="3"y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="18" y1="18" x2="6" y2="18"/></svg>' },
            { name: 'right', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="10" x2="7" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="7" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>' }
        ];
        
        alignments.forEach(align => {
            const button = this._createStyleButton(align.icon, `align-${align.name}`, () => {
                this.data.alignment = align.name;
                this._updatePreview();
                this._updateActiveButtons(settingsContainer);
            });
            alignButtonsWrapper.appendChild(button);
        });

        settingsContainer.appendChild(textInput);
        settingsContainer.appendChild(urlInput);
        settingsContainer.appendChild(colorButtonsWrapper);
        settingsContainer.appendChild(alignButtonsWrapper);
        
        this._updateActiveButtons(settingsContainer);

        return settingsContainer;
    }
    
    save() {
        return this.data;
    }

    validate(savedData) {
        return savedData.text.trim() && savedData.url.trim();
    }

    _createPreview() {
        const previewElement = document.createElement('div');
        previewElement.innerText = this.data.text;
        previewElement.className = 'btn';
        previewElement.classList.add(this.data.btnColor);
        return previewElement;
    }

    _updatePreview() {
        if (this.preview) {
            this.preview.innerText = this.data.text;
            this.preview.className = 'btn';
            this.preview.classList.add(this.data.btnColor);
            
            this.wrapper.style.textAlign = this.data.alignment;
        }
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
        input.addEventListener('input', () => onInput(input.value));
        wrapper.appendChild(iconElement);
        wrapper.appendChild(input);
        return wrapper;
    }
    
    _createStyleButton(innerHTML, dataValue, onClick) {
        const button = document.createElement('button');
        button.classList.add(this.api.styles.settingsButton);
        button.innerHTML = innerHTML;
        button.dataset.value = dataValue;
        button.addEventListener('click', onClick);
        return button;
    }

    _updateActiveButtons(container) {
        const buttons = container.querySelectorAll('button');
        buttons.forEach(button => {
            const value = button.dataset.value;
            if (value.startsWith('align-')) {
                button.classList.toggle(this.api.styles.settingsButtonActive, value === `align-${this.data.alignment}`);
            } else if (value.startsWith('color-')) {
                button.classList.toggle(this.api.styles.settingsButtonActive, value === `color-${this.data.btnColor}`);
            }
        });
    }
}

window.ButtonTool = ButtonTool;