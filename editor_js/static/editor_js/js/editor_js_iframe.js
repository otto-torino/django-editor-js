/**
 * Django EditorJS Iframe Library
 * * Manages the Editor.js instance inside the iframe, its configuration,
 * and sending updated data to the parent page.
 * * @version 0.1.1
 * @author Otto
 */
(function(window, document) {
    'use strict';

    // --- Main Namespace ---
    const DjangoEditorJSIframe = {};

    // --- Private Variables (Library State) ---
    let _editorInstance = null;
    let _debounceTimer = null;
    let _bulkListControl = null;
    let _selectedBlockIndexes = [];
    let _pendingBlockIndexes = [];
    let _selectionObserver = null;
    let _selectionUpdateFrame = null;
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
        const activeToolsConfig = useOverride ? { ...toolsOverride } : _config.toolsConfig;

        // Bundled inline tools (link, marker, font size) are used everywhere,
        // including field-specific overrides — unless the override addresses
        // the tool itself (e.g. sets it to null to restore native behavior).
        if (useOverride) {
            for (const name in _config.toolsConfig) {
                if (name in toolsOverride) continue;
                const info = _config.toolsConfig[name];
                const toolClass = info && window[info.class];
                if (toolClass && toolClass.isInline) {
                    activeToolsConfig[name] = info;
                }
            }
        }
        
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

                // Tool-level Editor.js settings (siblings of `class`, not part of
                // the tool's own `config`): forward them if declared.
                // The inline toolbar is on by default; a tool config can opt out
                // with `inlineToolbar: False` (or restrict it with an array).
                const toolSettings = { class: toolClass };
                toolSettings.inlineToolbar = toolInfo.inlineToolbar !== undefined
                    ? toolInfo.inlineToolbar
                    : true;
                ['shortcut', 'toolbox'].forEach(function (key) {
                    if (toolInfo[key] !== undefined) {
                        toolSettings[key] = toolInfo[key];
                    }
                });
                if (Object.keys(finalConfig).length > 0) {
                    toolSettings.config = finalConfig;
                }
                tools[name] = toolSettings;
            } else {
                console.warn(`[DjangoEditorJSIframe] Tool class '${toolInfo.class}' was not found.`);
            }
        }
        
        console.log('[DEBUG] 6. Final tools object for EditorJS:', tools);
        return tools;
    }

    /**
     * Returns a consecutive selection that can be converted. Multiple
     * paragraphs or one-or-more list blocks are supported.
     */
    function _getSelectedConvertibleBlocks() {
        const holder = document.getElementById('editor-js-holder');
        if (!holder) return null;

        const blocks = Array.from(holder.querySelectorAll('.ce-block'));
        let selected = blocks.filter((block) => block.classList.contains('ce-block--selected'));

        if (selected.length === 0) {
            const selection = window.getSelection();
            if (selection && !selection.isCollapsed && selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                selected = blocks.filter((block) => {
                    try {
                        return range.intersectsNode(block);
                    } catch (error) {
                        return false;
                    }
                });
            }
        }

        const indexes = selected
            .map((block) => blocks.indexOf(block))
            .filter((index) => index >= 0);
        const isConsecutive = indexes.every(
            (index, position) => position === 0 || index === indexes[position - 1] + 1
        );
        if (!isConsecutive || indexes.length === 0) return null;

        const allParagraphs = selected.every((block) => block.querySelector('.ce-paragraph'));
        const allLists = selected.every((block) => block.querySelector('.cdx-list'));

        if (allParagraphs && indexes.length >= 2) {
            return { indexes: indexes, kind: 'paragraph' };
        }
        if (allLists) {
            return { indexes: indexes, kind: 'list' };
        }
        return null;
    }

    function _scheduleBulkListControlUpdate() {
        if (_selectionUpdateFrame !== null) return;
        _selectionUpdateFrame = window.requestAnimationFrame(() => {
            _selectionUpdateFrame = null;
            _updateBulkListControl();
        });
    }

    function _updateBulkListControl() {
        if (!_bulkListControl) return;

        const selectionInfo = _getSelectedConvertibleBlocks();
        _selectedBlockIndexes = selectionInfo ? selectionInfo.indexes : [];
        if (!selectionInfo) {
            _bulkListControl.style.display = 'none';
            return;
        }

        _bulkListControl.querySelector('[data-action="paragraph"]').hidden =
            selectionInfo.kind !== 'list';

        const blocks = document.querySelectorAll('#editor-js-holder .ce-block');
        const firstRect = blocks[selectionInfo.indexes[0]].getBoundingClientRect();
        const lastRect = blocks[
            selectionInfo.indexes[selectionInfo.indexes.length - 1]
        ].getBoundingClientRect();

        _bulkListControl.style.display = 'flex';
        const width = _bulkListControl.offsetWidth;
        const height = _bulkListControl.offsetHeight;
        const left = Math.min(
            window.innerWidth - width - 8,
            Math.max(8, lastRect.right - width)
        );
        const preferredTop = firstRect.top - height - 8;
        const top = preferredTop >= 8 ? preferredTop : lastRect.bottom + 8;

        _bulkListControl.style.left = left + 'px';
        _bulkListControl.style.top = top + 'px';
    }

    function _listItemsToParagraphs(items) {
        const paragraphs = [];
        (items || []).forEach((item) => {
            if (typeof item === 'object' && item !== null) {
                paragraphs.push({
                    type: 'paragraph',
                    data: { text: item.content || '' }
                });
                paragraphs.push(..._listItemsToParagraphs(item.items));
            } else {
                paragraphs.push({
                    type: 'paragraph',
                    data: { text: String(item || '') }
                });
            }
        });
        return paragraphs;
    }

    function _listBlockFromParagraphs(blocks, style) {
        return {
            type: 'list',
            data: {
                style: style,
                meta: style === 'ordered' ? { counterType: 'numeric' } : {},
                items: blocks.map((block) => ({
                    content: block.data.text || '',
                    meta: {},
                    items: []
                }))
            }
        };
    }

    async function _convertSelectedBlocks(indexes, targetType) {
        if (!_editorInstance || indexes.length === 0) return;

        const actionButtons = _bulkListControl.querySelectorAll(
            '.editor-js-bulk-list-action'
        );
        actionButtons.forEach((button) => { button.disabled = true; });

        try {
            const output = await _editorInstance.save();
            const selectedBlocks = indexes.map((index) => output.blocks[index]);
            const areParagraphs = selectedBlocks.length >= 2 &&
                selectedBlocks.every((block) => block && block.type === 'paragraph');
            const areLists = selectedBlocks.every(
                (block) => block && block.type === 'list'
            );

            if (!areParagraphs && !areLists) return;

            let replacements;
            if (areParagraphs && (targetType === 'unordered' || targetType === 'ordered')) {
                replacements = [_listBlockFromParagraphs(selectedBlocks, targetType)];
            } else if (areLists && targetType === 'paragraph') {
                replacements = selectedBlocks.flatMap(
                    (block) => _listItemsToParagraphs(block.data.items)
                );
                if (replacements.length === 0) {
                    replacements = [{ type: 'paragraph', data: { text: '' } }];
                }
            } else if (areLists && (targetType === 'unordered' || targetType === 'ordered')) {
                replacements = selectedBlocks.map((block) => ({
                    ...block,
                    data: {
                        ...block.data,
                        style: targetType,
                        meta: targetType === 'ordered'
                            ? {
                                ...block.data.meta,
                                counterType: (block.data.meta || {}).counterType || 'numeric'
                            }
                            : {}
                    }
                }));
            } else {
                return;
            }

            const blocks = output.blocks.slice();
            blocks.splice(indexes[0], indexes.length, ...replacements);
            await _editorInstance.render({ blocks: blocks });

            const updatedData = await _editorInstance.save();
            window.parent.postMessage({
                type: 'editor-data-update',
                content: updatedData
            }, _config.trustedOrigin);

            _selectedBlockIndexes = [];
            _pendingBlockIndexes = [];
            _bulkListControl.style.display = 'none';
            if (window.parentIFrame) window.parentIFrame.size();
        } catch (error) {
            console.error('[DjangoEditorJSIframe] Block conversion failed: ', error);
        } finally {
            actionButtons.forEach((button) => { button.disabled = false; });
        }
    }

    function _setupBulkListConversion(enabled) {
        if (!enabled || _bulkListControl) return;

        _bulkListControl = document.createElement('div');
        _bulkListControl.className = 'editor-js-bulk-list-control';
        _bulkListControl.setAttribute('role', 'toolbar');
        _bulkListControl.setAttribute('aria-label', 'Convert selected blocks');
        _bulkListControl.innerHTML =
            '<button type="button" class="editor-js-bulk-list-action" data-action="unordered" title="Convert to bulleted list" aria-label="Convert to bulleted list">' +
                '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M7 5h10M7 10h10M7 15h10M3 5h.01M3 10h.01M3 15h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>' +
                '<span>Bulleted list</span>' +
            '</button>' +
            '<button type="button" class="editor-js-bulk-list-action" data-action="ordered" title="Convert to numbered list" aria-label="Convert to numbered list">' +
                '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M7 5h10M7 10h10M7 15h10M3 4v2M2.5 10h1L2.5 11.5h1M2.5 14.5h1v1h-1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
                '<span>Numbered list</span>' +
            '</button>' +
            '<button type="button" class="editor-js-bulk-list-action" data-action="paragraph" title="Convert list items to paragraphs" aria-label="Convert list items to paragraphs">' +
                '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M5 4h10M5 8h10M5 12h10M5 16h7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>' +
                '<span>Paragraphs</span>' +
            '</button>';

        _bulkListControl.addEventListener('pointerdown', (event) => {
            const action = event.target.closest('.editor-js-bulk-list-action');
            if (!action || action.disabled) return;

            _pendingBlockIndexes = _selectedBlockIndexes.slice();
            event.preventDefault();
            event.stopPropagation();

            // Editor.js clears its selection on pointer down, so conversion
            // must start before waiting for a later click event.
            _convertSelectedBlocks(_pendingBlockIndexes, action.dataset.action);
        });
        document.body.appendChild(_bulkListControl);

        const holder = document.getElementById('editor-js-holder');
        _selectionObserver = new MutationObserver(_scheduleBulkListControlUpdate);
        _selectionObserver.observe(holder, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ['class']
        });

        document.addEventListener('selectionchange', _scheduleBulkListControlUpdate);
        document.addEventListener('mouseup', _scheduleBulkListControlUpdate);
        document.addEventListener('keyup', _scheduleBulkListControlUpdate);
        window.addEventListener('scroll', _scheduleBulkListControlUpdate, { passive: true });
        window.addEventListener('resize', _scheduleBulkListControlUpdate, { passive: true });
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
                _setupBulkListConversion(Boolean(tools.list));
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

        console.log('[DEBUG] 8. Editor.js instance created:', _editorInstance);
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

            // Programmatic content replacement (e.g. Baton AI translation/summary).
            // Re-renders the editor with the given blocks and re-syncs the parent.
            if (event.data.type === 'set-data' && _editorInstance) {
                _editorInstance.render(event.data.content || { blocks: [] })
                    .then(function () {
                        return _editorInstance.save();
                    })
                    .then(function (outputData) {
                        window.parent.postMessage({
                            type: 'editor-data-update',
                            content: outputData
                        }, _config.trustedOrigin);
                        if (window.parentIFrame) window.parentIFrame.size();
                    })
                    .catch(function (error) {
                        console.error('[DjangoEditorJSIframe] set-data failed: ', error);
                    });
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
