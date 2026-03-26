import random
import string
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from states.family import FamilyState
from utils.i18n import get_text
from keyboards.menu import main_menu

router = Router()
db = Database("finance.db")

def generate_join_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@router.message(F.text.in_(["👥 Oila balansi", "👥 Семейный баланс", "👥 Family Wallet"]))
async def show_family_menu(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    family = db.get_user_family(user_id)
    
    if not family:
        kb = [
            [types.InlineKeyboardButton(text=get_text('btn_create_family', lang), callback_data="family_create")],
            [types.InlineKeyboardButton(text=get_text('btn_join_family', lang), callback_data="family_join")]
        ]
        await message.answer(
            get_text('family_welcome', lang) + "\n\n" + get_text('family_no_group', lang),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode="HTML"
        )
    else:
        f_id, name, creator_id, code, role = family
        members = db.get_family_members(f_id)
        stats_data = db.get_family_stats(f_id)
        
        members_text = ""
        for m_id, m_name, m_role in members:
            role_icon = "👑" if m_role == 'admin' else "👤"
            members_text += f"{role_icon} {m_name}\n"
            
        stats_text = ""
        if not stats_data:
            stats_text = get_text('no_data', lang)
        else:
            for m_name, amount, t_type in stats_data:
                type_icon = "📥" if t_type == 'income' else "📤"
                stats_text += f"{m_name}: {type_icon} {amount:,.0f} so'm\n"
        
        kb = [[types.InlineKeyboardButton(text=get_text('btn_leave_family', lang), callback_data="family_leave")]]
        
        await message.answer(
            get_text('family_info', lang, name=name, code=code, members=members_text, stats=stats_text),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "family_create")
async def create_family_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await state.set_state(FamilyState.name)
    await callback.message.edit_text(get_text('enter_family_name', lang))

@router.message(FamilyState.name)
async def process_family_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    name = message.text
    code = generate_join_code()
    
    db.create_family(user_id, name, code)
    await state.clear()
    
    await message.answer(
        get_text('family_created', lang, name=name, code=code),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "family_join")
async def join_family_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await state.set_state(FamilyState.join_code)
    await callback.message.edit_text(get_text('enter_join_code', lang))

@router.message(FamilyState.join_code)
async def process_join_code(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    code = message.text.upper()
    
    success = db.join_family(user_id, code)
    if success:
        await state.clear()
        await message.answer(get_text('join_success', lang))
    else:
        await message.answer(get_text('join_fail', lang))

@router.callback_query(F.data == "family_leave")
async def leave_family(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    db.leave_family(user_id)
    await callback.answer(get_text('action_cancelled', lang)) # Reuse or add join_success
    await callback.message.edit_text(get_text('family_welcome', lang))
