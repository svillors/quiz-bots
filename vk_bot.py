import os
import re
import random
import logging

import redis
import vk_api as vk
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from dotenv import load_dotenv

from utils import get_questions


logger = logging.getLogger(__name__)


def handle_message_from_user(event, vk_api, keyboard, questions, db):
    if event.text == 'Новый вопрос':
        question_number = random.randint(1, len(questions))
        question = questions[f'question{question_number}']
        db.set(event.user_id, question['answer'])
        vk_api.messages.send(
            user_id=event.user_id,
            message=question['question'],
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )
    elif event.text == 'Сдаться':
        answer = db.get(event.user_id).decode('utf-8')
        text = f'Вот правильный ответ: {answer}\n' \
               'Нажми "Новый вопрос" для продолжения'
        vk_api.messages.send(
            user_id=event.user_id,
            message=text,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )
    else:
        answer = db.get(event.user_id).decode('utf-8')
        message = event.text
        if message.lower() == re.sub(r'\s*\([^)]*\)|[.]+$', '', answer).lower():
            text = 'Правильно! Поздравляю!' \
                   'Для следующего вопроса нажми «Новый вопрос'
        else:
            text = 'Неправильно… Попробуешь ещё раз?'

        vk_api.messages.send(
            user_id=event.user_id,
            message=text,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    questions = get_questions('quiz-questions', logger)

    db = redis.Redis(host='localhost', port=6379, db=0)

    load_dotenv()
    token = os.getenv('VK_TOKEN')
    vk_session = vk.VkApi(token=token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    keyboard = VkKeyboard()
    keyboard.add_button('Новый вопрос')
    keyboard.add_line()
    keyboard.add_button('Сдаться')

    logger.info('bot started')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            handle_message_from_user(event, vk_api, keyboard, questions, db)


if __name__ == "__main__":
    main()
