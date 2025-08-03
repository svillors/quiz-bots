import logging
import os
import re
import random
from enum import Enum

import redis
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackContext, ConversationHandler)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class State(Enum):
    NEW_QUESTION = 1
    SOLUTION_ATTEMPT = 2


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
        [KeyboardButton('Сдаться')]
    ])
    update.message.reply_text(
        'Привет! Я бот-викторина. Нажми "Новый вопрос", чтобы начать.',
        reply_markup=keyboard,
    )

    return State.NEW_QUESTION.value


def handle_new_question_request(update, context):
    questions = context.bot_data.get("questions", {})
    db = context.bot_data.get('db')
    question_number = random.randint(1, len(questions))
    question = questions[f'question{question_number}']
    db.set(update.effective_user.id, question['answer'])
    update.message.reply_text(question['question'])

    return State.SOLUTION_ATTEMPT.value


def handle_solution_attempt(update, context):
    db = context.bot_data.get('db')
    answer = db.get(update.effective_user.id).decode('utf-8')
    message = update.message.text
    if message.lower() == re.sub(r'\s*\([^)]*\)|[.]+$', '', answer).lower():
        update.message.reply_text('Правильно! Поздравляю! Для ' \
                                  'следующего вопроса нажми «Новый вопрос')
        return State.NEW_QUESTION.value
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')
        return State.SOLUTION_ATTEMPT.value


def main() -> None:
    questions = get_questions('quiz-questions')

    db = redis.Redis(host='localhost', port=6379, db=0)

    load_dotenv()
    token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(token)

    dispatcher = updater.dispatcher

    dispatcher.bot_data['questions'] = questions
    dispatcher.bot_data['db'] = db

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.NEW_QUESTION.value: [
                MessageHandler(Filters.regex('Новый вопрос'), handle_new_question_request),
            ],
            State.SOLUTION_ATTEMPT.value: [
                MessageHandler(Filters.regex('Новый вопрос'), handle_new_question_request),
                MessageHandler(Filters.text & ~Filters.command, handle_solution_attempt)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
