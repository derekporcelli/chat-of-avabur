# Chat of Avabur

This is an open source project for the game **Relics of Avabur**. The goal of this project is to achieve full duplex chat integration with Discord using a Discord App or Bot. Works nicely with [Notifications of Avabur](https://github.com/davidmcclelland/notifications-of-avabur/).

## Installation
### Normal
I have an AWS server that can host Discord Bots, but if you don't trust me, feel free to follow the instructions to self-host your Bot
#### Discord Bot
Paste this URL in your server and allow everything
```
https://discord.com/oauth2/authorize?client_id=1309797708432932865&permissions=380104682512&integration_type=0&scope=bot
```

#### TamperMonkey Script
If you haven't, install the TamperMonkey Extension ([Chrome](https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo?hl=en)) ([Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/))

Then, [install the script](https://github.com/derekporcelli/chat-of-avabur/raw/main/chat-of-avabur.user.js)

### Self Hosted

First, clone the repository
NOTE: To ensure proper WebSocket connection, start the server _before_ loading **Relics of Avabur**

#### Discord Bot
1. Visit (https://discord.com/developers/applications)[Discord Developer Portal]
2. Click `New Application`
3. Give it a name, agree to Discord ToS, and click `Create`
4. Click `Bot` on the left sidebar
5. Click `Reset Token`, `Yes, do it!`, and verify
6. Click `Copy` and paste your token in a new file called `token.txt` in your project root directory
7. Toggle `Message Content Intent`
8. Click `OAuth2` on the left sidebar
9. Check the following boxes: `bot > Manage Channels, View Channels, Send Messages, Create Public Threads, Create Private Threads, Send Messages in Threads, Manage Messages, Read Message History, Use Slash Commands`
10. Click `Copy` and paste your Generated URL into a private Discord Channel where you have admin permissions
11. Click the URL in the message and allow everything

#### TamperMonkey Script
See instructions in Normal Installation for TamperMonkey Script
NOTE: After installation or updates, you must edit the script to use custom WebSocket sockets
1. Open the script in TamperMonkey
2. Find the comments that start with `[SELF HOSTING]` and follow the instructions provided
3. Save the file
4. Reload **Relics of Avabur**

#### Server
Ensure you have `python3` and `pip` installed
1. Ensure you are in the project root directory
```sh
cd ./chat-of-avabur
```
2. Install the dependencies
```sh
pip install -r requirements.txt
```
3. Open `chat-of-avabur.py` in a text editor
4. Find the comments that start with `[SELF HOSTING]` and follow the instructions provided
5. Save the file
6. Start the server
```sh
python3 ./chat-of-avabur.py
```
