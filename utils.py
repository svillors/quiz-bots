import re
import os


def get_questions(path, logger=None):
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
    if not logger:
        logger.info('messages fetched')
    return questions
