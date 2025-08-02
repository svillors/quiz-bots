import logging
import os
import re
import random

from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_questions(path):
    pattern = re.compile(
        r"Вопрос(?::|\s+\d+:)\s*(?P<question>.+?)\s*Ответ:\s*(?P<answer>.+?)(?=\n(?:Комментарий:|Источник:|Автор:|Вопрос:|$))",
        re.DOTALL
    )
    questions = {}
    count = 1
    for dirpath, _, filenames in os.walk(path):
        for file in filenames:
            with open(os.path.join(dirpath, file), encoding='KOI8-R') as f:
                matches = pattern.finditer(f.read())
                for match in matches:
                    questions[f'question{count}'] = {
                        'question': match.group('question'),
                        'answer': match.group('answer')
                    }
                    count += 1
    logger.info('messages fetched')
    return questions


def start(update: Update, context: CallbackContext) -> None:
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton('Новый вопрос')],
        [KeyboardButton('Сдаться')],
        [KeyboardButton('Мой счёт')]
    ])
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=keyboard,
    )


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    message = update.message.text
    questions = context.bot_data.get("questions", {})
    if message == 'Новый вопрос':
        question_number = random.randint(1, len(questions))
        update.message.reply_text(
            questions[f'question{question_number}']['question'])
    elif message == 'Сдаться':
        pass
    elif message == 'Мой счёт':
        pass


def main() -> None:
    questions = get_questions('quiz-questions')

    load_dotenv()
    token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(token)

    dispatcher = updater.dispatcher

    dispatcher.bot_data['questions'] = questions

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
