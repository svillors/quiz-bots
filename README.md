# Quiz Bots
A simple quiz bot for Telegram and VK that reads questions from local files and allows users to answer in a conversational interface.

## Environment
### Requirements
you should install all dependencies using:
```bash
pip install -r requirements.txt
```
### Environment variables
- TG_BOT_TOKEN - your telegram bot's token.
- VK_TOKEN - your group token in vk.

## Usage
Firstly you should unzip archive with questions using:
```bash
unzip quiz-questions.zip -d quiz-questions/
```
### To run bots:

Telegram
```bash
python3 tg_bot.py
```
VK
```bash
python3 vk_bot.py
```
