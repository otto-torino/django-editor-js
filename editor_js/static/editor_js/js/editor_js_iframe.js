/**
 * Django EditorJS Iframe Library
 * * Manages the Editor.js instance inside the iframe, its configuration,
 * and sending updated data to the parent page.
 * * @version 0.1.0
 * @author Otto
 */
(function(window, document) {
    'use strict';

    // --- Main Namespace ---
    const DjangoEditorJSIframe = {};

    // --- Private Variables (Library State) ---
    let _editorInstance = null;
    let _debounceTimer = null;
    let _config = {
        trustedOrigin: '',
        uploadImageUrl: '',
        csrfToken: '',
        toolsConfig: {}
    };

    // --- Private Methods ---

    /**
     * Reads the configuration passed via data-* attributes on the body.
     */
    function _loadConfig() {
        const body = document.body;
        _config.trustedOrigin = body.dataset.trustedOrigin || '';
        _config.uploadImageUrl = body.dataset.uploadImageUrl || '';
        _config.csrfToken = body.dataset.csrfToken || '';
        _config.toolsConfig = body.dataset.toolsJson ? JSON.parse(body.dataset.toolsJson) : {};

        if (!_config.trustedOrigin) {
            console.error('[DjangoEditorJSIframe] Trusted origin not specified. Communication will not work.');
        }
    }
    
    /**
     * Prepares the configuration object for EditorJS tools.
     * @returns {object} The 'tools' object for EditorJS.
     */
    function _buildTools() {
        const tools = {};
        for (const name in _config.toolsConfig) {
            const toolInfo = _config.toolsConfig[name];
            const toolClass = window[toolInfo.class];

            if (toolClass) {
                if (name === 'image') {
                    tools[name] = {
                        class: toolClass,
                        config: {
                            endpoints: { byFile: _config.uploadImageUrl },
                            additionalRequestHeaders: { 'X-CSRFToken': _config.csrfToken }
                        }
                    };
                } else if (toolInfo.config) {
                    tools[name] = { class: toolClass, ...toolInfo.config };
                } else {
                    tools[name] = toolClass;
                }
            } else {
                console.warn(`[DjangoEditorJSIframe] Tool class '${toolInfo.class}' was not found.`);
            }
        }
        return tools;
    }

    /**
     * Creates and initializes the EditorJS instance.
     * @param {object} initialData - The initial data to populate the editor.
     */
    function _createEditor(initialData) {
        if (_editorInstance) {
            console.warn('[DjangoEditorJSIframe] Attempt to re-initialize an already existing editor.');
            return;
        }

        const tools = _buildTools();
        _editorInstance = new EditorJS({
            holder: 'editor-js-holder',
            tools: tools,
            data: initialData,
            placeholder: 'Write something...',

            onReady: () => {
                if (window.parentIFrame) window.parentIFrame.size();
            },

            onChange: (api, event) => {
                clearTimeout(_debounceTimer);
                _debounceTimer = setTimeout(() => {
                    api.saver.save().then((outputData) => {
                        window.parent.postMessage({
                            type: 'editor-data-update',
                            content: outputData
                        }, _config.trustedOrigin);
                    }).catch((error) => {
                        console.error('[DjangoEditorJSIframe] Save failed: ', error);
                    });

                    if (window.parentIFrame) window.parentIFrame.size();
                }, 250);
            }
        });
    }

    /**
     * Sets up the listener to receive the initialization message from the parent page.
     */
    function _setupMessageListener() {
        window.addEventListener('message', function (event) {
            if (event.origin !== _config.trustedOrigin) return;

            if (event.data.type === 'init') {
                _createEditor(event.data.initialData);
            }
        });
    }

    // --- Public API ---

    /**
     * Initializes the iframe library.
     * Loads the configuration and listens for the initialization command.
     */
    DjangoEditorJSIframe.init = function() {
        _loadConfig();
        _setupMessageListener();
    };

    /**
     * Returns the active EditorJS instance.
     * @returns {EditorJS|null} The editor instance or null if not initialized.
     */
    DjangoEditorJSIframe.getEditorInstance = function() {
        return _editorInstance;
    };

    // --- Global Exposure ---
    window.DjangoEditorJSIframe = DjangoEditorJSIframe;

})(window, document);