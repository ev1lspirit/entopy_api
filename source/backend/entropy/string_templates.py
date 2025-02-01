from enum import StrEnum


class PhrasesWhileProcessing(StrEnum):
    PROCESSING = "🔊 <b>Обрабатываем сигнал....</b>"
    CALCULATION = "🎧 <b>Считаем энтропию...</b>"
    CORRELATION = "〰 <b>Выявляем зависимости...</b>"
    PREPARING_ANSWER = "🤖 <b>Готовим ответ...</b>"

    @classmethod
    def yield_phrase(cls):
        while True:
            yield from (phrase.value for phrase in cls)
