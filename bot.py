import logging
import os
import re
import random

import redis
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
    db = context.bot_data.get('db')
    if message == 'Новый вопрос':
        question_number = random.randint(1, len(questions))
        question = questions[f'question{question_number}']
        db.set(update.effective_user.id, question['answer'])
        update.message.reply_text(question['question'])
    elif message == 'Сдаться':
        pass
    elif message == 'Мой счёт':
        pass
    else:
        answer = db.get(update.effective_user.id).decode('utf-8')
        if message.lower() == re.sub(r'\s*\([^)]*\)|[.]+$', '', answer).lower():
            update.message.reply_text('Правильно! Поздравляю! Для ' \
                                      'следующего вопроса нажми «Новый вопрос')
        else:
            update.message.reply_text('Неправильно… Попробуешь ещё раз?')


def main() -> None:
    questions = get_questions('quiz-questions')

    db = redis.Redis(host='localhost', port=6379, db=0)

    load_dotenv()
    token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(token)

    dispatcher = updater.dispatcher

    dispatcher.bot_data['questions'] = questions
    dispatcher.bot_data['db'] = db

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
