/**
 * Django EditorJS Widget Library
 * * Manages the widget iframe, fullscreen mode, and communication
 * between the main page and the editor iframe.
 * * @version 0.1.0
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
        const widgetName = wrapper.dataset.widgetName;
        
        // Find DOM elements specific to this instance
        const iframe = document.getElementById(`id_${widgetName}_iframe`);
        const hiddenTextarea = document.getElementById(`id_${widgetName}`);
        const fullscreenBtn = document.getElementById(`id_${widgetName}_fullscreen_btn`);
        
        if (!iframe || !hiddenTextarea || !fullscreenBtn) {
            console.error(`[DjangoEditorJSWidget] Elements not found for widget: ${widgetName}. Initialization skipped.`);
            return;
        }

        const editorConfig = JSON.parse(wrapper.dataset.configJson);
        const initialData = hiddenTextarea.value ? JSON.parse(hiddenTextarea.value) : {};
        const iframeOrigin = new URL(iframe.src).origin;

        _setupFullscreen(wrapper, fullscreenBtn);
        _setupMessageListener(iframe, hiddenTextarea, iframeOrigin);

        // Initialize iFrameResize if the library is available
        if (typeof window.iFrameResize === 'function') {
            window.iFrameResize({ log: false, checkOrigin: false }, iframe);
        }

        // Send configuration data to the iframe once it has loaded
        iframe.onload = function () {
            iframe.contentWindow.postMessage({
                type: 'init',
                config: editorConfig,
                initialData: initialData
            }, iframeOrigin);
        };
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
                    // Use console.error instead of alert for a better user experience
                    console.error(`[DjangoEditorJSWidget] Error enabling fullscreen mode: ${err.message}`);
                });
            } else {
                document.exitFullscreen();
            }
        });

        document.addEventListener('fullscreenchange', function() {
            // Hide the button only when the wrapper is in fullscreen
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
            // Security check: accept messages only from the trusted origin
            if (event.origin !== iframeOrigin) {
                return;
            }

            // Ensure the message comes from the correct iframe window
            if (event.source === iframe.contentWindow && event.data.type === 'editor-data-update') {
                hiddenTextarea.value = JSON.stringify(event.data.content);
            }
        });
    }

    // --- Public API ---

    /**
     * Initializes all EditorJS widgets present on the page.
     * Searches for elements matching the provided selector and initializes them.
     * @param {string} [selector='[data-widget-name]'] - A CSS selector to find widget containers.
     */
    DjangoEditorJSWidget.init = function(selector) {
        const widgetSelector = selector || '[data-widget-name]';
        const widgetWrappers = document.querySelectorAll(widgetSelector);
        
        if (widgetWrappers.length === 0) {
            console.warn(`[DjangoEditorJSWidget] No widgets found with selector: ${widgetSelector}`);
        }
        
        widgetWrappers.forEach(_initializeInstance);
    };

    // --- Global Exposure ---
    window.DjangoEditorJSWidget = DjangoEditorJSWidget;

})(window, document);