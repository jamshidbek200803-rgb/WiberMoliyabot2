from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from config import ADMIN_ID
from utils.i18n import get_text
from keyboards.admin_kb import admin_menu_keyboard, admin_user_action_keyboard
from states.admin import AdminState, AdState, AdHistoryState
import asyncio
import csv
import os

def parse_duration_hours(text):
    """Parse duration text like '15 minut', '2 soat', '3 kun', '1 oy' into hours."""
    parts = text.lower().split()
    if len(parts) != 2:
        return None
    try:
        value = float(parts[0])
    except (ValueError, TypeError):
        return None
    unit = parts[1]
    if unit.startswith('minut'):
        return value / 60.0
    elif unit.startswith('soat'):
        return value
    elif unit.startswith('kun'):
        return value * 24.0
    elif unit.startswith('oy'):
        return value * 24.0 * 30.0
    return None

router = Router()
db = Database("finance.db")

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID) or db.is_extra_admin(user_id)

@router.message(Command("admin"))
async def admin_start(message: types.Message):
    if not is_admin(message.from_user.id): return
    
    lang = db.get_user_language(message.from_user.id)
    is_m = db.get_maintenance_mode()
    await message.answer(
        get_text('admin_panel_title', lang),
        reply_markup=admin_menu_keyboard(lang, is_m),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_maintenance")
async def toggle_maintenance(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    lang = db.get_user_language(callback.from_user.id)
    current = db.get_maintenance_mode()
    db.set_maintenance_mode(not current)
    await callback.message.edit_text(get_text('admin_panel_title', lang), reply_markup=admin_menu_keyboard(lang, not current), parse_mode="Markdown")

@router.callback_query(F.data == "admin_export")
async def export_data(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    lang = db.get_user_language(callback.from_user.id)
    filename = f"users_export_{callback.from_user.id}.csv"
    users = db.get_all_users_list()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'User', 'Premium'])
        writer.writerows(users)
    await callback.message.answer_document(types.FSInputFile(filename), caption=get_text('admin_export_done', lang))
    os.remove(filename)

@router.callback_query(F.data == "admin_categories")
async def cats_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    lang = db.get_user_language(callback.from_user.id)
    cats = db.get_all_categories_admin()
    text = "🏷 **Kategoriyalar:**\n\n" + "\n".join([f"`{c[0]}` {c[1]} ({c[2]})" for c in cats])
    kb = [[types.InlineKeyboardButton(text=get_text('btn_add_cat', lang), callback_data="cat_add"),
           types.InlineKeyboardButton(text=get_text('btn_del_cat', lang), callback_data="cat_del")],
          [types.InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_admin")]]
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@router.callback_query(F.data == "cat_add")
async def cat_add_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_cat_name)
    await callback.message.answer("Kategoriya nomini yuboring:")

@router.message(AdminState.add_cat_name)
async def cat_add_name(message: types.Message, state: FSMContext):
    await state.update_data(cname=message.text)
    await state.set_state(AdminState.add_cat_type)
    kb = [[types.KeyboardButton(text="income"), types.KeyboardButton(text="expense")]]
    await message.answer("Turi (income/expense):", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@router.message(AdminState.add_cat_type)
async def cat_add_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.add_category(data['cname'], message.text)
    await state.clear()
    await message.answer("✅ Qo'shildi!", reply_markup=types.ReplyKeyboardRemove())
    await admin_start(message)

@router.callback_query(F.data == "admin_feedback")
async def view_fb(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    lang = db.get_user_language(callback.from_user.id)
    unread = db.get_unread_feedback()
    text = "\n\n".join([f"👤 {f[4]} (`{f[1]}`):\n{f[2]}" for f in unread]) if unread else "Yangi fikrlar yo'q."
    for f in unread: db.mark_feedback_read(f[0])
    kb = [[types.InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_admin")]]
    await callback.message.edit_text(get_text('admin_feedback_info', lang, text=text), reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@router.callback_query(F.data == "admin_admins")
async def admins_menu(callback: types.CallbackQuery):
    if str(callback.from_user.id) != str(ADMIN_ID): return # Only super admin
    lang = db.get_user_language(callback.from_user.id)
    kb = [[types.InlineKeyboardButton(text=get_text('btn_add_admin', lang), callback_data="adm_add"),
           types.InlineKeyboardButton(text=get_text('btn_del_admin', lang), callback_data="adm_del")],
          [types.InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_admin")]]
    await callback.message.edit_text("👑 **Adminlar:**", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@router.callback_query(F.data == "adm_add")
async def adm_add_st(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_admin_id)
    await callback.message.answer("Yangi admin ID-sini yuboring:")

@router.message(AdminState.add_admin_id)
async def adm_add_fn(message: types.Message, state: FSMContext):
    try:
        db.add_extra_admin(int(message.text))
        await message.answer("✅ Admin qo'shildi!")
    except: await message.answer("❌ Xato.")
    await state.clear()
    await admin_start(message)

@router.callback_query(F.data == "back_to_admin")
async def back_adm(callback: types.CallbackQuery):
    await admin_start(callback.message); await callback.message.delete()

# --- Pre-existing feature handlers (Broadcast, Stats, Users, Premium, Ban, Approve/Reject) ---
@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    lang = db.get_user_language(callback.from_user.id)
    total, inc, exp = db.get_admin_stats()
    await callback.message.edit_text(get_text('admin_stats_msg', lang, total=total, income=inc, expense=exp), reply_markup=admin_menu_keyboard(lang, db.get_maintenance_mode()), parse_mode="Markdown")

@router.callback_query(F.data == "admin_broadcast")
async def br_st(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(AdminState.broadcast_msg)
    await callback.message.edit_text(get_text('admin_broadcast_ask', db.get_user_language(callback.from_user.id)))

@router.message(AdminState.broadcast_msg)
async def br_pr(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    lang = db.get_user_language(message.from_user.id)
    text = message.text; await state.clear()
    msg = await message.answer(get_text('admin_broadcast_started', lang))
    uids = db.get_all_user_ids(); ok, fl = 0, 0
    for u in uids:
        try: await message.bot.send_message(u, text); ok += 1; await asyncio.sleep(0.05)
        except: fl += 1
    await msg.edit_text(get_text('admin_broadcast_done', lang, ok=ok, fail=fl))

@router.callback_query(F.data == "admin_users")
async def list_users(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    lang = db.get_user_language(callback.from_user.id)
    users = db.get_all_users_list()[:20]
    text = get_text('admin_users_title', lang) + "\n\n" + "\n".join([f"ID: `{u[0]}` | {u[1]} @{u[2] or ''} {'💎' if u[3] else ''}" for u in users])
    await state.set_state(AdminState.manage_user)
    await callback.message.edit_text(text, reply_markup=admin_menu_keyboard(lang, db.get_maintenance_mode()), parse_mode="Markdown")

@router.message(AdminState.manage_user)
async def manage_u(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    lang = db.get_user_language(message.from_user.id)
    try:
        tid = int(message.text)
        db.cursor.execute("SELECT is_premium, is_banned FROM users WHERE user_id = ?", (tid,))
        r = db.cursor.fetchone()
        if r:
            prem, ban = r
            await message.answer(f"ID: {tid}\nPrem: {prem}\nBan: {ban}", reply_markup=admin_user_action_keyboard(tid, prem, ban, lang))
        else:
            await message.answer(get_text('no_data', lang))
    except:
        await message.answer(get_text('admin_audit_id_ask', lang))

@router.callback_query(F.data.startswith("adm_premium_"))
async def tg_prem(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    p = callback.data.split("_"); tid, st = int(p[2]), int(p[3])
    db.update_user_premium(tid, st)
    await callback.answer(get_text('admin_premium_given' if st else 'admin_premium_taken', db.get_user_language(callback.from_user.id)))
    try: await callback.bot.send_message(tid, "💎 **Premium ON**" if st else "❌ **Premium OFF**", parse_mode="Markdown")
    except: pass
    await list_users(callback, state)

@router.callback_query(F.data.startswith("adm_ban_"))
async def tg_ban(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    p = callback.data.split("_"); tid, st = int(p[2]), int(p[3])
    db.update_user_ban_status(tid, st)
    await callback.answer(get_text('admin_user_banned' if st else 'admin_user_unbanned', db.get_user_language(callback.from_user.id)))
    await list_users(callback, state)

@router.callback_query(F.data.startswith("approve_"))
async def app_pay(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    tid = int(callback.data.split("_")[1])
    db.cursor.execute("SELECT user_id, amount, status FROM transactions WHERE id = ?", (tid,))
    tr = db.cursor.fetchone()
    if not tr or tr[2] != 'pending': return
    db.cursor.execute("UPDATE transactions SET status = 'approved' WHERE id = ?", (tid,))
    db.update_real_balance(tr[0], tr[1]); db.deposit_to_goal(tr[0], tr[1]); db.connection.commit()
    await callback.message.edit_caption(caption="✅ Tasdiqlandi"); await callback.answer("OK")

@router.callback_query(F.data.startswith("reject_"))
async def rej_pay(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    tid = int(callback.data.split("_")[1])
    db.cursor.execute("UPDATE transactions SET status = 'rejected' WHERE id = ?", (tid,))
    db.connection.commit(); await callback.message.edit_caption(caption="❌ Rad etildi"); await callback.answer("OK")

# --- Ads Handlers ---
@router.callback_query(F.data == "admin_ads")
async def start_ad_creation(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    lang = db.get_user_language(callback.from_user.id)
    kb = [
        [types.InlineKeyboardButton(text=get_text('btn_yes', lang), callback_data="ad_has_photo_yes"),
         types.InlineKeyboardButton(text=get_text('btn_no', lang), callback_data="ad_has_photo_no")],
        [types.InlineKeyboardButton(text=get_text('btn_cancel', lang), callback_data="cancel_ad")]
    ]
    await callback.message.edit_text(get_text('ad_ask_photo', lang), reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(AdState.waiting_for_has_photo)

@router.callback_query(F.data == "cancel_ad")
async def cancel_ad_creation(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(get_text('ad_cancelled', lang))

@router.callback_query(AdState.waiting_for_has_photo, F.data.startswith("ad_has_photo_"))
async def process_has_photo(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    if callback.data == "ad_has_photo_yes":
        await callback.message.edit_text(get_text('ad_send_photo', lang))
        await state.set_state(AdState.waiting_for_photo)
    else:
        await state.update_data(photo_id=None)
        await callback.message.edit_text(get_text('ad_send_text', lang))
        await state.set_state(AdState.waiting_for_text)

@router.message(AdState.waiting_for_photo, F.photo)
async def process_ad_photo(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await message.answer(get_text('ad_send_text', lang))
    await state.set_state(AdState.waiting_for_text)

@router.message(AdState.waiting_for_text, F.text)
async def process_ad_text(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    await state.update_data(text=message.text)
    await message.answer(get_text('ad_send_title_phone', lang))
    await state.set_state(AdState.waiting_for_details)

@router.message(AdState.waiting_for_details, F.text)
async def process_ad_details(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    parts = message.text.split("-")
    if len(parts) >= 2:
        title = parts[0].strip()
        phone = "-".join(parts[1:]).strip()
    else:
        title = message.text
        phone = ""
    await state.update_data(title=title, phone=phone)
    await message.answer(get_text('ad_send_duration_advanced', lang))
    await state.set_state(AdState.waiting_for_duration)

@router.message(AdState.waiting_for_duration, F.text)
async def process_ad_duration(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    duration = parse_duration_hours(message.text)
    if duration is None:
        await message.answer(get_text('ad_duration_invalid', lang))
        return
        
    await state.update_data(duration=duration)
    data = await state.get_data()
    preview_text = get_text('ad_preview', lang, title=data.get('title', ''), phone=data.get('phone', ''), text=data.get('text', ''), hours=message.text)
    kb = [
        [types.InlineKeyboardButton(text=get_text('btn_confirm', lang), callback_data="confirm_ad"),
         types.InlineKeyboardButton(text=get_text('btn_cancel', lang), callback_data="cancel_ad")]
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    if data.get('photo_id'):
        await message.answer_photo(photo=data['photo_id'], caption=preview_text, reply_markup=markup, parse_mode="Markdown")
    else:
        await message.answer(preview_text, reply_markup=markup, parse_mode="Markdown")
    await state.set_state(AdState.waiting_for_confirmation)

@router.callback_query(AdState.waiting_for_confirmation, F.data == "confirm_ad")
async def confirm_ad(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    data = await state.get_data()
    
    db.add_ad(data.get('photo_id'), data.get('text'), data.get('title'), data.get('phone'), data.get('duration'))
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply(get_text('ad_broadcast_started', lang))
    await state.clear()
    
    # Run broadcast in background
    asyncio.create_task(broadcast_ad_task(callback.bot, data.get('photo_id'), data.get('text'), data.get('title'), data.get('phone')))

async def broadcast_ad_task(bot, photo_id, text, title, phone):
    users = db.get_all_users_for_broadcast()
    count = 0
    ad_content = f"📣 **{title}**\n📞 {phone}\n\n{text}"
    for u_id in users:
        try:
            if photo_id:
                await bot.send_photo(u_id, photo=photo_id, caption=ad_content, parse_mode="Markdown")
            else:
                await bot.send_message(u_id, ad_content, parse_mode="Markdown")
            count += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
        
    try:
        lang = db.get_user_language(ADMIN_ID)
        await bot.send_message(ADMIN_ID, get_text('ad_broadcast_done', lang, count=count))
    except Exception:
        pass

# --- Ad History System ---

@router.callback_query(F.data == "admin_ads_history")
async def start_ad_history(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    lang = db.get_user_language(callback.from_user.id)
    ads = db.get_ads_history(limit=10)
    if not ads:
        await callback.answer("Tarxi yo'q (No history)", show_alert=True)
        return
    kb = []
    for ad in ads:
        title = ad[1][:20] + "..." if len(ad[1]) > 20 else ad[1]
        kb.append([types.InlineKeyboardButton(text=f"{'🟢' if ad[4] else '⚪️'} {title}", callback_data=f"ad_hist_{ad[0]}")])
    kb.append([types.InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_menu")])
    
    await callback.message.edit_text(get_text('ad_history_list', lang), reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(AdHistoryState.view_history)

@router.callback_query(AdHistoryState.view_history, F.data.startswith("ad_hist_"))
async def select_history_ad(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    ad_id = int(callback.data.split("_")[2])
    ad = db.get_ad_by_id(ad_id)
    if not ad:
        await callback.answer("Ad not found", show_alert=True)
        return
    await state.update_data(photo_id=ad[1], text=ad[2], title=ad[3], phone=ad[4])
    
    kb = [
        [types.InlineKeyboardButton(text=get_text('btn_edit_yes', lang), callback_data="ad_hist_edit_yes"),
         types.InlineKeyboardButton(text=get_text('btn_edit_no', lang), callback_data="ad_hist_edit_no")],
        [types.InlineKeyboardButton(text=get_text('btn_cancel', lang), callback_data="cancel_ad")]
    ]
    
    preview = f"📣 **{ad[3]}**\n📞 {ad[4]}\n\n{ad[2]}"
    if ad[1]:
        await callback.message.answer_photo(photo=ad[1], caption=preview)
    else:
        await callback.message.answer(preview)
        
    await callback.message.answer(get_text('ad_edit_ask', lang), reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(AdHistoryState.ask_edit)

@router.callback_query(AdHistoryState.ask_edit, F.data.startswith("ad_hist_edit_"))
async def process_edit_ask(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    if callback.data == "ad_hist_edit_no":
        await callback.message.edit_text(get_text('ad_send_duration_advanced', lang))
        await state.set_state(AdHistoryState.waiting_for_duration)
    else:
        kb = [
            [types.InlineKeyboardButton(text=get_text('btn_edit_photo', lang), callback_data="edit_part_photo")],
            [types.InlineKeyboardButton(text=get_text('btn_edit_text', lang), callback_data="edit_part_text")],
            [types.InlineKeyboardButton(text=get_text('btn_edit_details', lang), callback_data="edit_part_details")],
            [types.InlineKeyboardButton(text=get_text('btn_cancel', lang), callback_data="cancel_ad")]
        ]
        await callback.message.edit_text(get_text('ad_edit_what', lang), reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
        await state.set_state(AdHistoryState.choose_edit_part)

@router.callback_query(AdHistoryState.choose_edit_part, F.data.startswith("edit_part_"))
async def choose_edit_part(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    part = callback.data.split("_")[2]
    if part == "photo":
        await callback.message.edit_text(get_text('ad_send_photo', lang))
        await state.set_state(AdHistoryState.edit_photo)
    elif part == "text":
        await callback.message.edit_text(get_text('ad_send_text', lang))
        await state.set_state(AdHistoryState.edit_text)
    elif part == "details":
        await callback.message.edit_text(get_text('ad_send_title_phone', lang))
        await state.set_state(AdHistoryState.edit_details)

@router.message(AdHistoryState.edit_photo, F.photo)
async def receive_edit_photo(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    await state.update_data(photo_id=message.photo[-1].file_id)
    await message.answer(get_text('ad_send_duration_advanced', lang))
    await state.set_state(AdHistoryState.waiting_for_duration)

@router.message(AdHistoryState.edit_text, F.text)
async def receive_edit_text(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    await state.update_data(text=message.text)
    await message.answer(get_text('ad_send_duration_advanced', lang))
    await state.set_state(AdHistoryState.waiting_for_duration)

@router.message(AdHistoryState.edit_details, F.text)
async def receive_edit_details(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    parts = message.text.split("-")
    title = parts[0].strip() if len(parts) > 0 else ""
    phone = "-".join(parts[1:]).strip() if len(parts) > 1 else ""
    await state.update_data(title=title, phone=phone)
    await message.answer(get_text('ad_send_duration_advanced', lang))
    await state.set_state(AdHistoryState.waiting_for_duration)

@router.message(AdHistoryState.waiting_for_duration, F.text)
async def process_hist_ad_duration(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    duration = parse_duration_hours(message.text)
    if duration is None:
        await message.answer(get_text('ad_duration_invalid', lang))
        return
        
    await state.update_data(duration=duration)
    data = await state.get_data()
    preview_text = get_text('ad_preview', lang, title=data.get('title', ''), phone=data.get('phone', ''), text=data.get('text', ''), hours=message.text)
    
    kb = [
        [types.InlineKeyboardButton(text=get_text('btn_confirm', lang), callback_data="confirm_ad"),
         types.InlineKeyboardButton(text=get_text('btn_cancel', lang), callback_data="cancel_ad")]
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb)
    if data.get('photo_id'):
        await message.answer_photo(photo=data['photo_id'], caption=preview_text, reply_markup=markup, parse_mode="Markdown")
    else:
        await message.answer(preview_text, reply_markup=markup, parse_mode="Markdown")
        
    await state.set_state(AdState.waiting_for_confirmation)
