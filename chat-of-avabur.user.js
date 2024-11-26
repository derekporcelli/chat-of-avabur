// ==UserScript==
// @name         Chat of Avabur
// @namespace    http://tampermonkey.net/
// @version      1.0.0
// @description  Two way Discord Chat integration!
// @author       illecrop
// @match        https://avabur.com/game
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // Replace with your Python WebSocket server URL
    const pythonWebSocketUrl = "wss://derekporcelli.com/chat-of-avabur";

    // Establish WebSocket connection with Python server
    const pythonSocket = new WebSocket(pythonWebSocketUrl);

    pythonSocket.onopen = () => {
        console.log("[Tampermonkey] Connected to Python WebSocket server.");
    };

    pythonSocket.onmessage = (event) => {

        // Forward message to the browser's WebSocket connection
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

    // Intercept browser's WebSocket
    const OriginalWebSocket = window.WebSocket;
    let browserSocket = null;

    window.WebSocket = function(url, protocols) {
        console.log("[Tampermonkey] Intercepting WebSocket connection:", url);

        // Create the original WebSocket connection
        const socket = new OriginalWebSocket(url, protocols);
        browserSocket = socket;

        // Hook the `send` method
        const originalSend = socket.send;
        socket.send = function(data) {
            console.log("[Tampermonkey] Intercepted send:", data);

            // Forward the data to the Python WebSocket server
            if (pythonSocket.readyState === 1) {
                pythonSocket.send(data);
            }
            // Call the original send method
            return originalSend.call(socket, data);
        };

        // Hook the `onmessage` handler
        socket.addEventListener("message", (event) => {

            // Forward the message to the Python WebSocket server
            if (pythonSocket.readyState === 1) {
                pythonSocket.send(event.data);
            } else {
                console.error("[Tampermonkey] Python socket not ready for incoming message:", event.data);
            }
        });

        return socket;
    };

    // Preserve the prototype chain
    window.WebSocket.prototype = OriginalWebSocket.prototype;
})();
