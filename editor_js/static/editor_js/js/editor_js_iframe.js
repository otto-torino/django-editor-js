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
     * Reads the global configuration passed via data-* attributes on the body.
     */
    function _loadConfig() {
        const body = document.body;
        _config.trustedOrigin = body.dataset.trustedOrigin || '';
        _config.uploadImageUrl = body.dataset.uploadImageUrl || '';
        _config.csrfToken = body.dataset.csrfToken || '';
        _config.toolsConfig = body.dataset.toolsJson ? JSON.parse(body.dataset.toolsJson) : {};

        console.log('[DEBUG] 1. Default config loaded from <body>:', _config.toolsConfig);

        if (!_config.trustedOrigin) {
            console.error('[DjangoEditorJSIframe] Trusted origin not specified. Communication will not work.');
        }
    }
    
    /**
     * Prepares the configuration object for EditorJS tools.
     * @param {object} toolsOverride - A field-specific tools config that overrides the global one.
     * @returns {object} The final 'tools' object for EditorJS.
     */
    function _buildTools(toolsOverride) {
        const tools = {};
        
        console.log('[DEBUG] 4. _buildTools received override:', toolsOverride);

        const useOverride = toolsOverride && Object.keys(toolsOverride).length > 0;
        const activeToolsConfig = useOverride ? toolsOverride : _config.toolsConfig;
        
        console.log(`[DEBUG] 5. Using ${useOverride ? 'specific' : 'default'} tools config:`, activeToolsConfig);

        for (const name in activeToolsConfig) {
            const toolInfo = activeToolsConfig[name];
            if (!toolInfo) continue;

            const toolClass = window[toolInfo.class];

            if (toolClass) {
                let finalConfig = toolInfo.config || {};
                if (name === 'image') {
                    finalConfig = {
                        ...finalConfig,
                        endpoints: { byFile: _config.uploadImageUrl },
                        additionalRequestHeaders: { 'X-CSRFToken': _config.csrfToken }
                    };
                }
                tools[name] = { class: toolClass, config: finalConfig };
                if (Object.keys(finalConfig).length === 0) {
                    tools[name] = toolClass;
                }
            } else {
                console.warn(`[DjangoEditorJSIframe] Tool class '${toolInfo.class}' was not found.`);
            }
        }
        
        console.log('[DEBUG] 6. Final tools object for EditorJS:', tools);
        return tools;
    }

    /**
     * Creates and initializes the EditorJS instance.
     * @param {object} initialData - The initial data to populate the editor.
     * @param {object} fieldConfig - The entire field-specific configuration object from the parent.
     */
    function _createEditor(initialData, fieldConfig) {
        if (_editorInstance) {
            console.warn('[DjangoEditorJSIframe] Attempt to re-initialize an already existing editor.');
            return;
        }

        console.log('[DEBUG] 3. _createEditor called with field config:', fieldConfig);
        const tools = _buildTools(fieldConfig.tools);

        _editorInstance = new EditorJS({
            holder: 'editor-js-holder',
            tools: tools,
            data: initialData,
            placeholder: document.body.dataset.placeholder || 'Write something...',

            onReady: () => {
                console.log('[DEBUG] 7. Editor.js is ready.');
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
                console.log('[DEBUG] 2. Received "init" message from parent:', event.data);
                const fieldConfig = event.data.config || {};
                
                _createEditor(event.data.initialData, fieldConfig);
            }
        });
    }

    // --- Public API ---

    /**
     * Initializes the iframe library.
     */
    DjangoEditorJSIframe.init = function() {
        _loadConfig();
        _setupMessageListener();
    };

    /**
     * Returns the active EditorJS instance.
     */
    DjangoEditorJSIframe.getEditorInstance = function() {
        return _editorInstance;
    };

    window.DjangoEditorJSIframe = DjangoEditorJSIframe;

})(window, document);
