// ==UserScript==
// @name         Chat of Avabur
// @namespace    https://github.com/derekporcelli/
// @version      1.1.0
// @description  Two way Discord Chat integration!
// @author       illecrop <illecrop@proton.me>
// @match        https://*.avabur.com/game*
// @icon         https://github.com/derekporcelli/chat-of-avabur/blob/8c5c2be0d79460032631fc23c186051a09ac3d96/img/tampermonkey-script-icon.png?raw=true
// @grant        GM_addStyle
// @updateURL    https://raw.githubusercontent.com/derekporcelli/chat-of-avabur/main/chat-of-avabur.user.js
// @downloadURL  https://raw.githubusercontent.com/derekporcelli/chat-of-avabur/main/chat-of-avabur.user.js
// @run-at       document-end
// ==/UserScript==

'use strict';

const SETTINGS_KEY = 'CoASettings';

const COA_STYLES = `
.row.text-center > div {
display: inline-block;
float: none;
}
#CoASettings input {
margin-right: 10px;
}
#CoASettings textarea {
width: 50%;
height: 80px;
}
#CoASettings hr {
margin-top: 10px;
margin-bottom: 10px;
}
#notificationLogItems {
margin-top: 10px;
}
input[type=time] {
border: 1px solid var(--border-color);
background-color: var(--input-background-color);
color: #fff;
}
`;

const SETTINGS_DIALOG_HTML = `
<div id="CoASettings" style="display: none; margin: 10px;">
<div id="CoASettingsContentWrapper">
    <div>
        <h4 class="nobg">Hosting</h4>
        <div class="row">
            <div class="col-xs-3">
                <label>
                    <input id="selfHostingBoolean" type="checkbox" v-model="userSettings.selfHostingBoolean"> Self hosting
                </label>
            </div>
            <div class="col-xs-3">
                <label>WebSocket Server URL</label>
                <input id="pythonWebSocketUrl" type="text" v-model="userSettings.pythonWebSocketUrl" value="ws://localhost:8765">
            </div>
        </div>
    </div>
</div>
<div class="row" style="display: none;" id="CoASettingsSavedLabel">
    <strong class="col-xs-12">
        Settings have been saved
    </strong>
</div>
</div>
`;

const SETTINGS_BUTTON_HTML = `
<a id="coaPreferences"><button class="btn btn-primary">CoA</button></a>
`;

const DEFAULT_USER_SETTINGS = {
    selfHostingBoolean: false,
    pythonWebSocketUrl: 'wss://derekporcelli.com/chat-of-avabur',
};

const util = {
    log: (message) => console.log(`[${GM_info.script.name} (${GM_info.script.version})] ${message}`),
    error: (message) => console.error(`[${GM_info.script.name} (${GM_info.script.version})] ${message}`),
};

const initPythonWebSocket = (uri, browserSocket) => {
    const ws = new WebSocket(uri);
    ws.addEventListener('open', () => util.log('WebSocket connection established'));
    ws.addEventListener('close', () => util.log('WebSocket connection closed'));
    ws.addEventListener('error', (error) => util.error(`WebSocket error: ${error}`));
    ws.addEventListener('onmessage', (event) => {
        browserSocket.send(event.data);
    });
    return ws;
}

const hijackWebSocket = (pythonSocket) => {
    const OriginalWebSocket = window.WebSocket;
    let browserSocket = null;

    window.WebSocket = function(url, protocols) {
        util.log("Intercepting WebSocket connection:", url);

        const socket = new OriginalWebSocket(url, protocols);
        browserSocket = socket;

        const originalSend = socket.send;
        socket.send = function(data) {
            pythonSocket.send(data);
            return originalSend.call(socket, data);
        };
        socket.addEventListener("message", (event) => {pythonSocket.send(event.data);});

        return socket;
    };

    window.WebSocket.prototype = OriginalWebSocket.prototype;
}

const loadUserSettings = () => {
    try {
        const storedSettings = localStorage.getItem(SETTINGS_KEY);
        if (storedSettings) {
            const parsedSettings = JSON.parse(storedSettings);
            util.log(JSON.stringify(parsedSettings));
            return parsedSettings;
        }
    } catch (error) {
        util.log(`Error loading settings: ${error.message}`);
    }

    util.log(JSON.stringify(DEFAULT_USER_SETTINGS)); // Log default settings if none exist or error occurs
    return DEFAULT_USER_SETTINGS;
};

const saveUserSettings = (settings) => {
    if (typeof settings !== 'object') {
        util.log("Error: Settings must be an object.");
        return;
    }
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
};


const initHTML = ($, userSettings) => {
    GM_addStyle(COA_STYLES);

    var accountSettingsWrapper = $('#accountSettingsWrapper');
    var settingsLinksWrapper = $('#settingsLinksWrapper');
    var coaSettingsPage = $(SETTINGS_DIALOG_HTML);
    var coaSettingsButton = $(SETTINGS_BUTTON_HTML);

    accountSettingsWrapper.append(coaSettingsPage);
    settingsLinksWrapper.append(coaSettingsButton);

    coaSettingsButton.on('click', function() {
        util.log('Opening CoA settings');
        coaSettingsPage.css('display', 'block').siblings().css('display', 'none');
        settingsLinksWrapper.css('display', 'block');
    });

    var selfHostingBoolean = $('#selfHostingBoolean');
    var pythonWebSocketUrl = $('#pythonWebSocketUrl');
    var coaSettingsSavedLabel = $('#CoASettingsSavedLabel');

    selfHostingBoolean.on('change', function() {
        pythonWebSocketUrl.prop('disabled', !this.checked);
        userSettings.selfHostingBoolean = this.checked;
        if (this.checked) {
            userSettings.pythonWebSocketUrl = pythonWebSocketUrl.val();
        } else {
            userSettings.pythonWebSocketUrl = DEFAULT_USER_SETTINGS.pythonWebSocketUrl;
        }
        saveUserSettings(userSettings);
        coaSettingsSavedLabel.css('display', 'block').fadeOut(2000);
    });

    pythonWebSocketUrl.on('input', function() {
        userSettings.pythonWebSocketUrl = this.value;
        selfHostingBoolean.prop('checked', true);
        saveUserSettings(userSettings);
        coaSettingsSavedLabel.css('display', 'block').fadeOut(2000);
        util.log('WebSocket URL:', this.value);
    });

    if (userSettings.selfHostingBoolean) {
        selfHostingBoolean.prop('checked', true);
        pythonWebSocketUrl.prop('disabled', false);
        pythonWebSocketUrl.val(userSettings.pythonWebSocketUrl);
    } else {
        selfHostingBoolean.prop('checked', false);
        pythonWebSocketUrl.prop('disabled', true);
    }
}

const main = () => {
    var userSettings = loadUserSettings();
    saveUserSettings(userSettings);
    //const pythonSocket = initPythonWebSocket(userSettings.pythonWebSocketUrl, window.WebSocket);
    //hijackWebSocket(pythonSocket);
    initHTML(jQuery, userSettings);
};

main();