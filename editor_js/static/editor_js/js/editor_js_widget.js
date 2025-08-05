/**
 * Django EditorJS Widget Library
 * * Manages the widget iframe, fullscreen mode, and communication
 * between the main page and the editor iframe.
 * * @version 0.1.1
 * @author Otto
 */
(function(window, document) {
    'use strict';

    // --- Main Namespace ---
    const DjangoEditorJSWidget = {};

    // --- Private Methods ---

    /**
     * Initializes a single instance of the widget.
     * @param {HTMLElement} wrapper - The widget's container element.
     */
    function _initializeInstance(wrapper) {
        if (!wrapper || wrapper.dataset.initialized === 'true') {
            return;
        }

        const widgetName = wrapper.dataset.widgetName;
        
        const iframe = wrapper.querySelector(`#id_${widgetName}_iframe`);
        const hiddenTextarea = wrapper.querySelector(`#id_${widgetName}`);
        const fullscreenBtn = wrapper.querySelector(`#id_${widgetName}_fullscreen_btn`);

        if (!iframe || !hiddenTextarea || !fullscreenBtn) {
            console.error(`[DjangoEditorJSWidget] Core elements not found for widget: ${widgetName}. Please check template structure.`);
            return;
        }

        const configJsonString = wrapper.dataset.configJson || '{}';
        const editorConfig = JSON.parse(configJsonString);
        
        const initialData = hiddenTextarea.value ? JSON.parse(hiddenTextarea.value) : {};
        const iframeOrigin = new URL(iframe.src).origin;

        _setupFullscreen(wrapper, fullscreenBtn);
        _setupMessageListener(iframe, hiddenTextarea, iframeOrigin);

        if (typeof window.iFrameResize === 'function') {
            window.iFrameResize({ log: false, checkOrigin: false }, iframe);
        }

        iframe.onload = function () {
            iframe.contentWindow.postMessage({
                type: 'init',
                config: editorConfig,
                initialData: initialData
            }, iframeOrigin);
        };

        wrapper.dataset.initialized = 'true';
    }

    /**
     * Sets up the logic for fullscreen mode.
     * @param {HTMLElement} wrapper - The element to display in fullscreen.
     * @param {HTMLElement} fullscreenBtn - The button that toggles fullscreen mode.
     */
    function _setupFullscreen(wrapper, fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            if (!document.fullscreenElement) {
                wrapper.requestFullscreen().catch(err => {
                    console.error(`[DjangoEditorJSWidget] Error enabling fullscreen mode: ${err.message}`);
                });
            } else {
                document.exitFullscreen();
            }
        });

        document.addEventListener('fullscreenchange', function() {
            fullscreenBtn.style.display = (document.fullscreenElement === wrapper) ? 'none' : 'block';
        });
    }

    /**
     * Sets up the listener to receive updated data from the editor iframe.
     * @param {HTMLIFrameElement} iframe - The editor's iframe.
     * @param {HTMLTextAreaElement} hiddenTextarea - The hidden textarea where data is saved.
     * @param {string} iframeOrigin - The expected origin for messages.
     */
    function _setupMessageListener(iframe, hiddenTextarea, iframeOrigin) {
        window.addEventListener('message', function (event) {
            if (event.origin !== iframeOrigin) {
                return;
            }

            if (event.source === iframe.contentWindow && event.data.type === 'editor-data-update') {
                hiddenTextarea.value = JSON.stringify(event.data.content);
            }
        });
    }

    // --- Public API ---

    /**
     * Initializes all widgets on the page and sets up a listener for dynamically
     * added ones using Django's `formset:added` event.
     * @param {string} selector - The CSS selector for the widget wrappers.
     */
    DjangoEditorJSWidget.init = function(selector) {
        document.querySelectorAll(selector).forEach(_initializeInstance);

        if (window.django && window.django.jQuery) {
            const $ = window.django.jQuery;
            $(document).on('formset:added', function(event, $row, formsetName) {
                if ($row && typeof $row.find === 'function') {
                    const $widgetWrapper = $row.find(selector);
                    if ($widgetWrapper.length) {
                        _initializeInstance($widgetWrapper[0]);
                    }
                }
            });
        }
    };

    // --- Global Exposure ---
    window.DjangoEditorJSWidget = DjangoEditorJSWidget;

})(window, document);
