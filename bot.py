import os
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters
)
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env
TOKEN = os.getenv("BOT_TOKEN")

# --- ক্রেডিট কার্ড জেনারেটর ফাংশন ---
def generate_credit_card_number(prefix, length):
    number = [int(digit) for digit in prefix]
    while len(number) < length - 1:
        number.append(random.randint(0, 9))
    return number

def luhn_algorithm(number):
    number = [int(digit) for digit in number]
    reversed_number = number[::-1]
    total_sum = 0
    for i in range(len(reversed_number)):
        digit = reversed_number[i]
        if (i + 1) % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total_sum += digit
    return total_sum % 10 == 0

def complete_number_with_luhn(number):
    temp_number = number.copy()
    temp_number.append(0)
    if luhn_algorithm(temp_number):
        return number + [0]
    else:
        for last_digit in range(1, 10):
            temp_number[-1] = last_digit
            if luhn_algorithm(temp_number):
                return number + [last_digit]

def generate_valid_credit_card_number(prefix, length):
    max_attempts = 1000
    for attempt in range(max_attempts):
        number = generate_credit_card_number(prefix, length)
        completed_number = complete_number_with_luhn(number)
        if luhn_algorithm(completed_number):
            return ''.join(map(str, completed_number))
    return None

def generate_card_data(prefix, length, expiry_month=None, expiry_year=None, cvv=None):
    card_number = generate_valid_credit_card_number(prefix, length)
    if card_number is None:
        return None, None, None

    if expiry_month is None or expiry_year is None:
        today = datetime.now()
        future_date = today + timedelta(days=random.randint(365, 5*365))
        expiry_month = future_date.strftime("%m")
        expiry_year = future_date.strftime("%Y")

    expiry_date = f"{expiry_month}|{expiry_year}"

    if cvv is None:
        cvv = str(random.randint(100, 999))

    return card_number, expiry_date, cvv

# --- হ্যান্ডলার ফাংশন ---
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Send me a BIN like this: 123456|MM|YYYY|CVV")

async def generate_card_from_bin(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.strip()
    parts = user_input.split('|')

    bin_number = parts[0].strip()
    expiry_month = parts[1].strip() if len(parts) > 1 else None
    expiry_year = parts[2].strip() if len(parts) > 2 else None
    cvv = parts[3].strip() if len(parts) > 3 else None

    if not bin_number.isdigit() or len(bin_number) < 6:
        await update.message.reply_text("Invalid BIN. Please send a valid BIN.")
        return

    card_length = 16
    num_cards = 10
    response = ""

    for _ in range(num_cards):
        card_number, exp, card_cvv = generate_card_data(
            bin_number, card_length,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv
        )
        if card_number:
            response += f"`{card_number}` \\| `{exp}` \\| `{card_cvv}`\n"
        else:
            response += "❌ Could not generate valid card number.\n"

    await update.message.reply_text(response, parse_mode="MarkdownV2")

# --- মূল বট সেটআপ ---
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_card_from_bin))

    # Claw Cloud-এর জন্য Webhook চালু
    port = int(os.environ.get("PORT", 8443))
    webhook_url = f"https://{os.environ.get('APP_URL')}/{TOKEN}"

    await app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=webhook_url
    )

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())