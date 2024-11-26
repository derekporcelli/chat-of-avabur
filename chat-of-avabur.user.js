// ==UserScript==
// @name         Chat of Avabur
// @namespace    http://tampermonkey.net/
// @version      1.0.0
// @description  Two way Discord Chat integration!
// @author       illecrop
// @match        https://avabur.com/game
// @icon         https://github.com/derekporcelli/chat-of-avabur/blob/8c5c2be0d79460032631fc23c186051a09ac3d96/img/tampermonkey-script-icon.png?raw=true
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    const pythonWebSocketUrl = "wss://derekporcelli.com/chat-of-avabur";

    const pythonSocket = new WebSocket(pythonWebSocketUrl);

    pythonSocket.onopen = () => {
        console.log("[Tampermonkey] Connected to Python WebSocket server.");
    };

    pythonSocket.onmessage = (event) => {

        if (browserSocket && browserSocket.readyState === 1) {
            browserSocket.send(event.data);
        } else {
            console.error("[Tampermonkey] Browser socket not ready to send:", event.data);
        }
    };

    pythonSocket.onerror = (error) => {
        console.error("[Tampermonkey] WebSocket error:", error);
    };

    pythonSocket.onclose = () => {
        console.log("[Tampermonkey] Disconnected from Python WebSocket server.");
    };

    const OriginalWebSocket = window.WebSocket;
    let browserSocket = null;

    window.WebSocket = function(url, protocols) {
        console.log("[Tampermonkey] Intercepting WebSocket connection:", url);

        const socket = new OriginalWebSocket(url, protocols);
        browserSocket = socket;

        const originalSend = socket.send;
        socket.send = function(data) {
            console.log("[Tampermonkey] Intercepted send:", data);

            if (pythonSocket.readyState === 1) {
                pythonSocket.send(data);
            }

            return originalSend.call(socket, data);
        };

        socket.addEventListener("message", (event) => {

            if (pythonSocket.readyState === 1) {
                pythonSocket.send(event.data);
            } else {
                console.error("[Tampermonkey] Python socket not ready for incoming message:", event.data);
            }
        });

        return socket;
    };

    window.WebSocket.prototype = OriginalWebSocket.prototype;
})();
