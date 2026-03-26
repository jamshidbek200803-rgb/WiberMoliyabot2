from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from states.security import PinState
import time

class SecurityMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        from aiogram.types import CallbackQuery
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user_id = event.from_user.id
        state: FSMContext = data.get("state")

        # Check if user is banned
        if self.db.is_user_banned(user_id):
            lang = self.db.get_user_language(user_id)
            from utils.i18n import get_text
            msg = get_text('user_banned_msg', lang)
            if isinstance(event, Message):
                await event.answer(msg)
            else:
                await event.answer(msg, show_alert=True)
            return

        # Check Premium Block (3 days)
        blocked_until = self.db.is_premium_blocked(user_id)
        if blocked_until:
            lang = self.db.get_user_language(user_id)
            from utils.i18n import get_text
            msg = get_text('premium_blocked_msg', lang, date=blocked_until.strftime('%d.%m.%Y %H:%M'))
            if isinstance(event, Message):
                await event.answer(msg)
            else:
                await event.answer(msg, show_alert=True)
            return
        
        # Check Maintenance Mode
        from config import ADMIN_ID
        is_admin_user = str(user_id) == str(ADMIN_ID) or self.db.is_extra_admin(user_id)
        if self.db.get_maintenance_mode() and not is_admin_user:
            lang = self.db.get_user_language(user_id)
            from utils.i18n import get_text
            msg = get_text('maintenance_msg', lang)
            if isinstance(event, Message):
                await event.answer(msg, parse_mode="Markdown")
            else:
                await event.answer(msg, show_alert=True)
            return

        # /start buyrug'i bosilganda har safar PIN so'raladi
        if isinstance(event, Message) and event.text == "/start":
            self.db.clear_session(user_id)

        # PIN-kod o'rnatilganmi?
        try:
            pin = self.db.get_pin_code(user_id)
            if pin and state:
                current_state = await state.get_state()
                
                # Agar foydalanuvchi hozirgina PIN kiritayotgan bo'lmasa
                if current_state not in [PinState.check_pin, PinState.enter_new_pin, PinState.confirm_new_pin]:
                    auth_time = self.db.get_session(user_id)
                    current_time = time.time()
                    
                    # Agar foydalanuvchi tasdiqlanmagan bo'lsa yoki 1 soatdan ko'p vaqt o'tgan bo'lsa (3600 sekund)
                    if not auth_time or (current_time - auth_time > 3600):
                        await state.set_state(PinState.check_pin)
                        msg = "🔐 Bot qulflangan. Iltimos, 4 xonali PIN-kodni kiriting:"
                        if isinstance(event, Message):
                            return await event.answer(msg)
                        else:
                            return await event.answer(msg, show_alert=True)
        except Exception as e:
            import logging
            logging.error(f"SecurityMiddleware error: {e}")

        return await handler(event, data)
