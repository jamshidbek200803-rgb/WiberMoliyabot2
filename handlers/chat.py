from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from config import ADMIN_ID
from states.chat import ChatState
from keyboards.menu import main_menu, support_keyboard
from utils.i18n import get_text

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["💬 Chat-AI", "💬 Чат-ИИ", "💬 Chat-AI"]))
async def start_chat(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    await message.answer(
        get_text('chat_welcome', lang),
        reply_markup=support_keyboard(lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("sup_"))
async def handle_support_query(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    action = callback.data.split("_")[1]
    
    if action == "premium":
        await callback.message.edit_text(get_text('chat_premium_info', lang), parse_mode="Markdown", reply_markup=support_keyboard(lang))
    elif action == "payment":
        await callback.message.edit_text(get_text('chat_payment_info', lang), parse_mode="Markdown", reply_markup=support_keyboard(lang))
    elif action == "balance":
        await callback.message.edit_text(get_text('chat_balance_info', lang), parse_mode="Markdown", reply_markup=support_keyboard(lang))
    elif action == "goal":
        await callback.message.edit_text(get_text('chat_goal_info', lang), parse_mode="Markdown", reply_markup=support_keyboard(lang))
    elif action == "admin":
        await state.set_state(ChatState.chatting)
        await state.update_data(lang=lang)
        await callback.message.answer(
            get_text('chat_ask_admin', lang),
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text=get_text('chat_cancel_btn', lang))]],
                resize_keyboard=True
            )
        )
        await callback.answer()

@router.message(ChatState.chatting, F.text.in_(["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]))
async def cancel_admin_chat(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    balance = db.get_real_balance(user_id)
    is_premium = db.is_user_premium(user_id)
    
    await state.clear()
    await message.answer(get_text('chat_canceled', lang), reply_markup=main_menu(lang, balance, is_premium))

@router.message(ChatState.chatting)
async def handle_admin_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    
    admin_text = f"🚨 **YANGI SUPPORT MUROJAATI**\n\n"
    admin_text += f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
    admin_text += f"🆔 ID: `{message.from_user.id}`\n"
    admin_text += f"📝 Xabar: {message.text}\n\n"
    admin_text += "💬 Javob berish uchun ushbu xabarni 'Reply' qiling."
    
    await message.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    
    balance = db.get_real_balance(message.from_user.id)
    is_premium = db.is_user_premium(message.from_user.id)
    
    await state.clear()
    await message.answer(get_text('chat_msg_sent_to_admin', lang), reply_markup=main_menu(lang, balance, is_premium))

@router.message(F.chat.id == int(ADMIN_ID), F.reply_to_message)
async def admin_reply_handler(message: types.Message):
    reply = message.reply_to_message.text
    try:
        if "🆔 ID:" in reply:
            user_id = int(reply.split("🆔 ID:")[1].split("\n")[0].strip().replace("`", ""))
            lang = db.get_user_language(user_id)
            user_text = f"{get_text('admin_reply_header', lang)}\n\n{message.text}"
            await message.bot.send_message(chat_id=user_id, text=user_text, parse_mode="Markdown")
            await message.answer(get_text('admin_reply_sent_to_user', 'uz'))
    except Exception: pass
