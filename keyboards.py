from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню (reply-кнопки)
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск по username")],
        [KeyboardButton(text="📧 Поиск по email")],
        [KeyboardButton(text="📱 Поиск по номеру телефона")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

# Инлайн-меню после поиска
def get_result_actions(username: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Новый поиск", callback_data="new_search")],
            [InlineKeyboardButton(text="📊 Сохранить отчёт", callback_data=f"save_report_{username}")]
        ]
    )
