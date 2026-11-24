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
    let _toolClassNames = {};
    let _config = {
        trustedOrigin: '',
        uploadImageUrl: '',
        csrfToken: '',
        toolsConfig: {},
        // the translations of editor_js/i18n.py
        i18n: { messages: {}, toolMessages: {}, iframe: {} }
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
        if (body.dataset.i18nJson) {
            _config.i18n = JSON.parse(body.dataset.i18nJson);
        }

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
                // a minified class has lost its name: keep the configured one
                _toolClassNames[name] = toolInfo.class;
            } else {
                console.warn(`[DjangoEditorJSIframe] Tool class '${toolInfo.class}' was not found.`);
            }
        }
        
        console.log('[DEBUG] 6. Final tools object for EditorJS:', tools);
        return tools;
    }

    /**
     * The i18n messages of Editor.js: Editor.js looks up the texts of a tool
     * under the name it is registered with, so the texts of each tool, kept
     * by its class, are filed under its name.
     * @param {object} tools - The 'tools' object for EditorJS.
     * @returns {object} The `i18n.messages` of Editor.js.
     */
    function _buildMessages(tools) {
        const messages = JSON.parse(JSON.stringify(_config.i18n.messages || {}));
        messages.tools = messages.tools || {};
        const toolMessages = _config.i18n.toolMessages || {};
        for (const name in tools) {
            const texts = toolMessages[_toolClassNames[name]];
            if (texts) messages.tools[name] = texts;
        }
        return messages;
    }

    /**
     * Makes room in the iframe for an open menu of Editor.js. The iframe is as
     * tall as the body, and a menu is out of its flow: without the room, a
     * menu longer than the blocks under it is cut by the iframe, which then
     * scrolls inside the page.
     */
    function _fitOpenPopover() {
        let bottom = 0;
        document.querySelectorAll('.ce-popover--opened .ce-popover__container').forEach((menu) => {
            bottom = Math.max(bottom, menu.getBoundingClientRect().bottom + window.scrollY);
        });
        const minHeight = bottom ? Math.ceil(bottom) + 16 + 'px' : '';
        if (document.body.style.minHeight === minHeight) return;
        document.body.style.minHeight = minHeight;
        if (window.parentIFrame) window.parentIFrame.size();
    }

    function _setupPopoverFitting() {
        let frame = null;
        const schedule = () => {
            if (frame !== null) return;
            frame = window.requestAnimationFrame(() => {
                frame = null;
                _fitOpenPopover();
            });
        };
        // a menu opens by a class, and changes size with its content; the
        // style of the body, changed here, is not observed
        new MutationObserver(schedule).observe(document.body, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ['class']
        });
        // a menu opens with an animation that scales it
        document.addEventListener('animationend', schedule, true);
    }

    /**
     * A text of the iframe around the editor, in the language of the page.
     */
    function _t(text) {
        return (_config.i18n.iframe || {})[text] || text;
    }

    function _escapeHtml(text) {
        const element = document.createElement('span');
        element.textContent = text;
        return element.innerHTML.replace(/"/g, '&quot;');
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
        _bulkListControl.setAttribute('aria-label', _t('Convert selected blocks'));
        const action = (name, hint, label, icon) => {
            const title = _escapeHtml(_t(hint));
            return '<button type="button" class="editor-js-bulk-list-action" data-action="' + name +
                '" title="' + title + '" aria-label="' + title + '">' + icon +
                '<span>' + _escapeHtml(_t(label)) + '</span></button>';
        };
        _bulkListControl.innerHTML =
            action('unordered', 'Convert to bulleted list', 'Bulleted list',
                '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M7 5h10M7 10h10M7 15h10M3 5h.01M3 10h.01M3 15h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>') +
            action('ordered', 'Convert to numbered list', 'Numbered list',
                '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M7 5h10M7 10h10M7 15h10M3 4v2M2.5 10h1L2.5 11.5h1M2.5 14.5h1v1h-1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>') +
            action('paragraph', 'Convert list items to paragraphs', 'Paragraphs',
                '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M5 4h10M5 8h10M5 12h10M5 16h7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>');

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
            i18n: { messages: _buildMessages(tools) },

            onReady: () => {
                console.log('[DEBUG] 7. Editor.js is ready.');
                _setupBulkListConversion(Boolean(tools.list));
                _setupPopoverFitting();
                // the blocks move by dragging their ⋮⋮ handle (editorjs-drag-drop)
                if (typeof window.DragDrop === 'function') {
                    new window.DragDrop(_editorInstance);
                }
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

    // --- Auto Initialization ---
    // an inline script calling init() would need the nonce of a Content
    // Security Policy
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', DjangoEditorJSIframe.init);
    } else {
        DjangoEditorJSIframe.init();
    }

})(window, document);
