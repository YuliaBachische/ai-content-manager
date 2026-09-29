import os

from dotenv import load_dotenv
from fastapi import FastAPI
from google import genai
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def create_table():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_history (
            id SERIAL PRIMARY KEY,
            input_text TEXT NOT NULL,
            action VARCHAR(50) NOT NULL,
            result TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()

app = FastAPI()
create_table()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


class ContentRequest(BaseModel):
    text: str
    action: str


@app.get("/")
def root():
    return {"message": "AI Content Manager is running"}


@app.post("/generate")
def generate_content(request: ContentRequest):
    prompts = {
        "summarize": """
    Сделай краткое и понятное резюме текста.

    Требования:
    - Сохрани главную мысль и важные факты.
    - Не добавляй информацию от себя.
    - Удали повторы и второстепенные детали.
    - Используй естественный русский язык.
    - Объём — примерно 20–30% от исходного текста.
    """,

        "improve": """
        Перепиши следующий текст, сохранив его исходный смысл и все важные факты.

        Сделай текст заметно более:
        - грамотным;
        - естественным;
        - понятным;
        - связным;
        - профессионально написанным.

        Измени формулировки и структуру предложений там, где это улучшает текст.
        Не добавляй новую информацию и не меняй факты.

        Важно: не просто исправляй ошибки — именно переформулируй текст так, чтобы он звучал лучше.

        Верни только готовую улучшенную версию текста без комментариев и пояснений.

        Текст:
        """,

        "translate": """
    Переведи следующий текст на английский язык.

    Требования:
    - Сохрани смысл и фактическую информацию.
    - Используй естественный современный английский язык.
    - Не переводи названия компаний, продуктов и технологий, если их принято оставлять без перевода.
    - Не добавляй информацию от себя.
    - Верни только перевод без пояснений.
    """,

        "telegram": """
    Адаптируй следующий текст для публикации в Telegram.

    Требования:
    - Сохрани основную информацию и смысл.
    - Сделай текст компактным и удобным для чтения с телефона.
    - Используй короткие абзацы.
    - Можно использовать эмодзи умеренно, если они уместны.
    - Не добавляй факты, которых нет в исходном тексте.
    - Не используй кликбейт.
    - Не начинай текст с фраз вроде «Всем привет!» или «Сегодня мы расскажем».
    - Верни готовый текст поста без пояснений.
    """,

        "headlines": """
    Придумай 5 вариантов заголовка для следующего текста.

    Требования:
    - Заголовки должны быть разными по формулировке.
    - Они должны отражать содержание исходного текста.
    - Не используй кликбейт.
    - Не преувеличивай информацию.
    - Не добавляй факты, которых нет в тексте.
    - Избегай шаблонных фраз вроде «максимальная продуктивность», «без компромиссов» и «идеальный баланс».
    - Заголовки должны звучать естественно.
    - Каждый заголовок выведи с новой строки.
    - Не используй нумерацию.
    - Не добавляй пояснения.
    """,

        "keywords": """
    Выдели наиболее важные ключевые слова и фразы из текста.

    Требования:
    - Выбери до 10 наиболее значимых ключевых слов или фраз.
    - Они должны действительно отражать содержание текста.
    - Не добавляй слова, которых нет в исходном тексте, если они не являются очевидной формой существующего термина.
    - Не используй слишком общие слова вроде «технологии», «компания» или «работа», если они не являются основной темой.
    - Выведи ключевые слова через запятую.
    - Без пояснений.
    """,

        "seo": """
    Проанализируй следующий текст с точки зрения SEO.

    Выведи результат в следующем формате:

    Основные ключевые слова:
    ключевое слово 1, ключевое слово 2, ключевое слово 3

    Дополнительные ключевые фразы:
    фраза 1, фраза 2, фраза 3

    SEO-заголовки:
    заголовок 1
    заголовок 2
    заголовок 3

    Что можно улучшить:
    - рекомендация 1
    - рекомендация 2
    - рекомендация 3

    Требования:
    - Основывайся только на информации из исходного текста.
    - Не выдумывай факты.
    - Не добавляй несуществующие характеристики или преимущества.
    - Рекомендации должны быть практичными.
    - Не используй SEO-клише и искусственное переспамливание ключевыми словами.
    """
    }

    instruction = prompts.get(request.action)

    if not instruction:
        return {"error": "Неизвестное действие"}

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=f"{instruction}\n\nТекст:\n{request.text}"
        )

        result = response.text

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO content_history (input_text, action, result)
            VALUES (%s, %s, %s)
            """,
            (request.text, request.action, result)
        )

        connection.commit()
        cursor.close()
        connection.close()

        return {
            "result": result
        }

    except Exception as e:
        print("GEMINI ERROR:", repr(e))

        return {
            "error": str(e)
        }

@app.get("/history")
def get_history():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, input_text, action, result, created_at
        FROM content_history
        ORDER BY created_at DESC
        LIMIT 20
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    history = []

    for row in rows:
        history.append({
            "id": row[0],
            "input_text": row[1],
            "action": row[2],
            "result": row[3],
            "created_at": row[4].isoformat()
        })

    return history