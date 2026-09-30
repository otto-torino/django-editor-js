/**
 * Content Security Policy support for the page of the editor iframe.
 *
 * Editor.js and its tools inject their styles at runtime, and only a few of
 * them read a nonce. Loaded first, with the nonce of the page, this script
 * gives it to every <style> created afterwards: this page only runs the
 * editor, so no other code is involved. Without a nonce it does nothing.
 */
(function (document) {
    'use strict';

    const script = document.currentScript;
    const nonce = script && script.nonce;
    if (!nonce) {
        return;
    }

    const createElement = document.createElement;
    document.createElement = function (tagName, options) {
        const element = createElement.call(document, tagName, options);
        if (String(tagName).toLowerCase() === 'style') {
            element.nonce = nonce;
        }
        return element;
    };
})(document);
