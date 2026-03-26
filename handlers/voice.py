import os
import json
import logging
from aiogram import Router, F, types
from database.db_manager import Database
from config import GEMINI_API_KEY
from utils.i18n import get_text
import google.generativeai as genai

router = Router()
db = Database("finance.db")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        logging.info(f"Available Gemini models: {models}")
        # Use first compatible 1.5-flash if available, otherwise gemini-pro
        if 'models/gemini-1.5-flash' in models:
            model_name = 'models/gemini-1.5-flash'
        elif 'models/gemini-1.5-flash-latest' in models:
            model_name = 'models/gemini-1.5-flash-latest'
        else:
            model_name = 'models/gemini-pro'
        
        model = genai.GenerativeModel(model_name)
        logging.info(f"Selected model: {model_name}")
    except Exception as e:
        logging.error(f"Error listing models: {e}")
        model = None
else:
    model = None
    logging.warning("GEMINI_API_KEY not found in config!")

@router.message(F.voice)
async def handle_voice_message(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    # Check premium status
    if not db.is_user_premium(user_id):
        await message.answer(get_text('voice_premium_required', lang))
        return

    if not GEMINI_API_KEY:
        await message.answer("AI API key not configured.")
        return

    processing_msg = await message.answer(get_text('voice_processing', lang))
    
    try:
        # 1. Download voice file
        file_id = message.voice.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        
        # Temporary path to save the voice file
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        local_filename = f"{temp_dir}/voice_{user_id}_{message.message_id}.ogg"
        await message.bot.download_file(file_path, local_filename)
        
        # 2. Prepare prompt
        prompt = """
        Analyze the audio and extract the financial transaction details in JSON format.
        Fields:
        - "amount": number (extract the value)
        - "category": string (must be one of: Ovqat, Transport, Ijara, Kommunal, O'yin-kulgi, Oylik, Sotuv, Boshqa)
        - "type": string ("income" or "expense")
        - "comment": string or null
        
        If it's not a transaction, return: {"error": "not_transaction"}
        Return ONLY valid JSON.
        """
        
        # 3. Upload and Process with Gemini
        # Using upload_file is more robust
        audio_file = genai.upload_file(path=local_filename, display_name="user_voice")
        
        # Send to Gemini
        response = model.generate_content([
            prompt,
            audio_file
        ])
        
        # Cleanup file from Gemini server (optional but good practice)
        # genai.delete_file(audio_file.name)
        
        # Cleanup local file
        if os.path.exists(local_filename):
            os.remove(local_filename)
        
        # 4. Parse response
        try:
            # Clean response text from formatting if any (e.g. ```json ... ```)
            res_text = response.text.strip()
            if res_text.startswith("```json"):
                res_text = res_text[7:-3].strip()
            elif res_text.startswith("```"):
                res_text = res_text[3:-3].strip()
                
            res_json = json.loads(res_text)
            
            if "error" in res_json:
                await processing_msg.edit_text(get_text('voice_error', lang))
                return
            
            amount = res_json.get('amount')
            cat_name = res_json.get('category')
            t_type = res_json.get('type')
            comment = res_json.get('comment')
            
            if not amount or not cat_name or not t_type:
                await processing_msg.edit_text(get_text('voice_error', lang))
                return
            
            # 5. Get category ID
            categories = db.get_categories(t_type)
            cat_id = None
            for c_id, name in categories:
                if name.lower() == cat_name.lower():
                    cat_id = c_id
                    break
            
            if not cat_id:
                # Default to 'Boshqa' (Other)
                for c_id, name in categories:
                    if name == 'Boshqa':
                        cat_id = c_id
                        break
            
            # 6. Save to DB
            db.add_transaction(user_id, amount, cat_id, t_type, comment)
            
            # 7. Success message
            from keyboards.menu import main_menu
            balance = db.get_real_balance(user_id)
            is_premium = db.is_user_premium(user_id)
            
            success_text = get_text('voice_success', lang).format(amount=amount, cat=cat_name)
            if comment:
                success_text += f"\n📝: {comment}"
                
            await processing_msg.edit_text(success_text, parse_mode="Markdown")
            # We don't necessarily need to resend the main menu after every voice entry to avoid cluttering
            
        except Exception as e:
            await processing_msg.edit_text(get_text('voice_error', lang))
            raise e
        finally:
            # Cleanup local file if it exists
            if 'local_filename' in locals() and os.path.exists(local_filename):
                os.remove(local_filename)
            
    except Exception as e:
        logging.error(f"Voice processing error FULL: {e}", exc_info=True)
        await message.answer(f"Error: {str(e)}")
