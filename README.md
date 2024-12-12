# Chat of Avabur

## About
This is an open source project for the game **Relics of Avabur**. The goal of this project is to achieve full duplex chat integration with Discord using a Discord App or Bot. Works nicely with [Notifications of Avabur](https://github.com/davidmcclelland/notifications-of-avabur/).

## Linking RoA to Discord
**[NOTE]** Do this in a private server or other people will be able to chat on your behalf

1. Enter the following command in the channel you want to be your RoA chat interface and make a note of your key
```
/gen_key
```
2. Click `Account Management > CoA > Integrations`
3. Paste your key in the box and reload the page

## Installation
Regardless of which installation method you choose, you must [Link RoA to Discord](#linking-roa-to-discord)

### Normal
I have an AWS server that can host Discord Bots, but if you don't trust me, feel free to follow the instructions to [self-host](#self-hosted) your Bot

#### Discord Bot
1. Paste this URL in your server and allow everything
```
https://discord.com/oauth2/authorize?client_id=1309797708432932865&permissions=380104682512&integration_type=0&scope=bot
```

#### TamperMonkey Script
1. If you haven't, install the TamperMonkey Extension ([Chrome](https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo?hl=en)) ([Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/))
2. Then, [install the script](https://github.com/derekporcelli/chat-of-avabur/raw/main/chat-of-avabur.user.js)

---

### Self Hosted
**[NOTE]** To ensure proper WebSocket connection, start the server, _then_ load **Relics of Avabur**

#### Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
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
See instructions in [Normal Installation](#normal) for TamperMonkey Script, then come back here
1. Log in to **Relics of Avabur**
2. Click `Account Management > CoA`
3. Check `Self hosting`

#### Server
Ensure you have `python3`, `pip`, and `git` installed
1. Clone the repository
```sh
git clone https://github.com/derekporcelli/chat-of-avabur.git
```
2. Ensure you are in the project root directory
```sh
cd ./chat-of-avabur
```
3. Install the dependencies
```sh
pip install -r requirements.txt
```
4. Start the server
```sh
python3 ./chat-of-avabur.py --self-host
```
