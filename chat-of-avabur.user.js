// ==UserScript==
// @name         Chat of Avabur
// @namespace    https://github.com/derekporcelli/
// @version      1.2.0
// @description  Two way Discord Chat integration!
// @author       illecrop <illecrop@proton.me>
// @match        https://*.avabur.com/game*
// @icon         https://github.com/derekporcelli/chat-of-avabur/blob/8c5c2be0d79460032631fc23c186051a09ac3d96/img/tampermonkey-script-icon.png?raw=true
// @grant        none
// @updateURL    https://raw.githubusercontent.com/derekporcelli/chat-of-avabur/main/chat-of-avabur.user.js
// @downloadURL  https://raw.githubusercontent.com/derekporcelli/chat-of-avabur/main/chat-of-avabur.user.js
// @run-at       document-start
// ==/UserScript==

'use strict';

const SETTINGS_KEY = 'CoASettings';

const SETTINGS_DIALOG_HTML = `
<div id="CoASettings" style="display: none; margin: 10px;">
    <div id="CoASettingsContentWrapper">
        <!-- Navigation Bar for Submenus -->
        <div style="margin-bottom: 10px; border-bottom: 1px solid var(--border-color);">
            <button id="hostingTab" onclick="showSubmenu('hosting')" style="background-color: var(--button-background-color); color: var(--button-text-color); margin-right: 5px; border: none; padding: 5px;">
                Hosting
            </button>
            <button id="integrationsTab" onclick="showSubmenu('integrations')" style="background-color: var(--button-background-color); color: var(--button-text-color); border: none; padding: 5px;">
                Integrations
            </button>
        </div>

        <!-- Hosting Section -->
        <div id="hosting" style="display: block;">
            <h4 class="nobg" style="margin: 0; padding: 0;">Hosting</h4>
            <div class="row" style="margin: 0; padding: 0;">
                <div class="col-xs-3" style="display: inline-block; float: none; margin: 0;">
                    <label>
                        <input id="selfHostingBoolean" type="checkbox" v-model="userSettings.selfHostingBoolean" style="margin-right: 10px;"> Self hosting
                    </label>
                </div>
                <div class="col-xs-3" style="display: inline-block; float: none; margin: 0;">
                    <label>WebSocket Server URL</label>
                    <input id="pythonWebSocketUrl" type="text" v-model="userSettings.pythonWebSocketUrl" value="ws://localhost:8765" style="margin-right: 10px; border: 1px solid var(--border-color); background-color: var(--input-background-color); color: #fff;">
                </div>
            </div>
        </div>

        <!-- Integrations Section -->
        <div id="integrations" style="display: none;">
            <h4 class="nobg" style="margin: 0; padding: 0;">Integrations</h4>
            <div class="row" style="margin: 0; padding: 0;">
                <div class="col-xs-3" style="display: inline-block; float: none; margin: 0;">
                    <label>Integration Key</label>
                    <input id="integrationKey" type="text" v-model="userSettings.integrationKey" placeholder="Enter your key" style="margin-right: 10px; border: 1px solid var(--border-color); background-color: var(--input-background-color); color: #fff;">
                </div>
            </div>
        </div>
    </div>

    <!-- Saved Label -->
    <div class="row" style="display: none; margin-top: 10px;" id="CoASettingsSavedLabel">
        <strong class="col-xs-12">
            Settings have been saved
        </strong>
    </div>
</div>
`;

const SETTINGS_BUTTON_HTML = `
<a id="coaPreferences"><button class="btn btn-primary" style="margin: 5px; padding: 5px;">CoA</button></a>
`;

const DEFAULT_USER_SETTINGS = {
    selfHostingBoolean: false,
    pythonWebSocketUrl: 'wss://derekporcelli.com',
    integrationKey: '',
};

const util = {
    log: (message) => console.log(`[${GM_info.script.name} (${GM_info.script.version})] ${message}`),
    error: (message) => console.error(`[${GM_info.script.name} (${GM_info.script.version})] ${message}`),
    sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
};

const initPythonWebSocket = (uri) => {
    util.log(`Initializing Python WebSocket: ${uri}`);
    const ws = new WebSocket(uri);
    ws.addEventListener('open', () => util.log('WebSocket connection established'));
    ws.addEventListener('close', () => util.log('WebSocket connection closed'));
    ws.addEventListener('error', (error) => util.error(`WebSocket error: ${error}`));
    return ws;
}

const setPythonSocketOnMessage = (pythonSocket, browserSocket) => {
    util.log('Setting Python WebSocket onmessage event');
    pythonSocket.onmessage = (event) => {
        browserSocket.send(event.data);
    };
}

let browserSocket = null;

const hijackWebSocket = (pythonSocket, key) => {
    util.log('Hijacking WebSocket');

    const OriginalWebSocket = window.WebSocket;

    window.WebSocket = function(url, protocols) {
        util.log(`Modifying WebSocket connection at ${url}`);

        const socket = new OriginalWebSocket(url, protocols);
        browserSocket = socket;

        const originalSend = socket.send;
        socket.send = function(data) {
            pythonSocket.send(JSON.stringify({roa_message: data, key: key}));
            return originalSend.call(socket, data);
        };

        socket.addEventListener("message", (event) => {
            pythonSocket.send(JSON.stringify({roa_message: event.data, key: key}));
        });

        return socket;
    };

    window.WebSocket.prototype = OriginalWebSocket.prototype;
}

const loadUserSettings = () => {
    util.log('Loading user settings');
    try {
        const storedSettings = localStorage.getItem(SETTINGS_KEY);
        if (storedSettings) {
            const parsedSettings = JSON.parse(storedSettings);
            return parsedSettings;
        }
    } catch (error) {
        util.error(`Error loading settings: ${error.message}`);
    }
    return DEFAULT_USER_SETTINGS;
};

const saveUserSettings = (settings) => {
    if (typeof settings !== 'object') {
        util.error("Error: Settings must be an object.");
        return;
    }
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
};


const initHTML = ($, userSettings) => {
    util.log('Initializing HTML');

    var accountSettingsWrapper = $('#accountSettingsWrapper');
    var settingsLinksWrapper = $('#settingsLinksWrapper');
    var coaSettingsPage = $(SETTINGS_DIALOG_HTML);
    var coaSettingsButton = $(SETTINGS_BUTTON_HTML);

    accountSettingsWrapper.append(coaSettingsPage);
    settingsLinksWrapper.append(coaSettingsButton);

    coaSettingsButton.on('click', function() {
        coaSettingsPage.css('display', 'block').siblings().css('display', 'none');
        settingsLinksWrapper.css('display', 'block');
    });

    var selfHostingBoolean = $('#selfHostingBoolean');
    var pythonWebSocketUrl = $('#pythonWebSocketUrl');
    var integrationKey = $('#integrationKey');
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
    });

    integrationKey.on('input', function() {
        userSettings.integrationKey = this.value;
        saveUserSettings(userSettings);
        coaSettingsSavedLabel.css('display', 'block').fadeOut(2000);
    });

    if (userSettings.selfHostingBoolean) {
        selfHostingBoolean.prop('checked', true);
        pythonWebSocketUrl.prop('disabled', false);
        pythonWebSocketUrl.val(userSettings.pythonWebSocketUrl);
    } else {
        selfHostingBoolean.prop('checked', false);
        pythonWebSocketUrl.prop('disabled', true);
    }

    window.showSubmenu = function(tab) {
        const hosting = document.getElementById('hosting');
        const integrations = document.getElementById('integrations');

        if (tab === 'hosting') {
            hosting.style.display = 'block';
            integrations.style.display = 'none';
        } else if (tab === 'integrations') {
            hosting.style.display = 'none';
            integrations.style.display = 'block';
        }
    };
}

const main = async () => {
    var userSettings = loadUserSettings();

    let pythonSocket = initPythonWebSocket(userSettings.pythonWebSocketUrl);
    
    hijackWebSocket(pythonSocket, userSettings.integrationKey);

    while (browserSocket === null) {
        await util.sleep(1000);
    }

    setPythonSocketOnMessage(pythonSocket, browserSocket);

    saveUserSettings(userSettings);

    const observerHTML = new MutationObserver((mutations, observer) => {
        if (document.querySelector('#settingsLinksWrapper')) {
            observer.disconnect();
            initHTML(jQuery, userSettings);
        }
    });
    if (document.body) {
        observerHTML.observe(document.body, { childList: true, subtree: true });
    } else {
        util.error('Body not found');
    }

};

await main();