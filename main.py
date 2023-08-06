from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_polling
import os
import time

bot = Bot(token='6439853794:AAGxvsiXgw1HfqP3CnwIGWBCFsLMES9hTSQ')
dp = Dispatcher(bot)

ADMIN_ID = '5097258505'  # Replace with your admin user ID

live_messages = []
charge_messages = ["No More Charge CC Left"]
users_received = {}
users_received_time = {}
charge_single_line = True
broadcast_charge = False
live_single_line = True
broadcast_live = False

premium_users = set()
pending_payments = {}

# Function to load premium user IDs from the file
def load_premium_users():
    try:
        with open('premium_users.txt', 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Function to save premium user IDs to the file
def save_premium_users(premium_users_set):
    with open('premium_users.txt', 'w') as file:
        file.write('\n'.join(premium_users_set))

# Load premium user IDs from the file at the start of the bot
premium_users = load_premium_users()

@dp.message_handler(Command("viewpremium"))
async def view_premium_users(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.answer("You are not authorized to use this command.")
    
    if not premium_users:
        return await message.answer("No premium users found.")

    users_info = []
    for user_id in premium_users:
        user = await bot.get_chat(user_id)
        users_info.append(f"{user.full_name} (ID: {user_id})")

    premium_list = "\n".join(users_info)
    return await message.answer(f"<b>Premium Users:</b>\n{premium_list}", parse_mode='HTML')


@dp.message_handler(commands=['disablepremium'])
async def disable_premium_access(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.answer("You are not authorized to use this command.")
    
    user_id_to_disable = message.text.split("/disablepremium ", 1)[1]
    if user_id_to_disable in premium_users:
        premium_users.remove(user_id_to_disable)
        save_premium_users(premium_users)
        await message.answer("Premium access disabled for the user.")
    else:
        await message.answer("User ID not found in premium users list.")


admin_commands = {
    "/addlivemessage": "Add a live message to the list",
    "/addchargemessage": "Add a charge message to the list",
    "/togglechargemode": "Toggle between single line and whole message for charge CC",
    "/togglelivemode": "Toggle between single line and whole message for live CC",
    "/addpromo": "Add a promocode for free users to get premium access",
    "/viewpremium": "View the list of premium users",
    "/disablepremium": "Disable premium access for a specific user",
    "/adminhelp": "View all admin commands"
}


@dp.message_handler(commands=['adminhelp'])
async def show_admin_commands(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.answer("You are not authorized to use this command.")
    
    admin_commands_list = "\n".join([f"<b>{command}</b>: {description}" for command, description in admin_commands.items()])
    return await message.answer(f"<b>Admin Commands:</b>\n{admin_commands_list}", parse_mode='HTML')



@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in premium_users:
        await message.answer("👑 You Are A Premium User")
        keyboard = InlineKeyboardMarkup()
        button1 = InlineKeyboardButton("Get Live", callback_data='get_live')
        button2 = InlineKeyboardButton("Get Charged", callback_data='get_charge')
        keyboard.add(button1, button2)
        await message.answer("⚡ Select Your CC: ", reply_markup=keyboard)
    else:
        await message.answer("<b>🚫 You are a Free User.</b>\n－－－－－－－－－－－－\n<b>Redeem Promocode :</b> /redeem\n－－－－－－－－－－－－\n💰To access premium features, you can purchase a subscription using the /purchase command.", parse_mode='HTML')

@dp.message_handler(commands=['addpromo'])
async def add_promo_code(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.answer("You are not authorized to use this command.")
    
    promo_code = message.text.split("/addpromo ", 1)[1]
    with open('promo.txt', 'a') as file:
        file.write(f"{promo_code}\n")
    
    return await message.answer("Promocode added successfully")

@dp.message_handler(commands=['redeem'])
async def redeem_promo_code(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in premium_users:
        return await message.answer("You are already a Premium User.")

    promo_code = message.get_args().strip()
    if not promo_code:
        return await message.answer("<b>⛔ Invalid promocode</b>\n－－－－－－－－－－－\nPlease use the format : <code>/redeem XXX-XXX</code>", parse_mode='HTML')

    if redeem_promo(promo_code):
        premium_users.add(user_id)
        save_premium_users(premium_users)
        return await message.answer("Promocode redeemed. You are now a Premium User.")
    else:
        return await message.answer("Invalid or expired promocode.")

def redeem_promo(promo_code):
    if not os.path.exists('promo.txt'):
        return False

    with open('promo.txt', 'r') as file:
        promo_codes = file.read().splitlines()

    if promo_code in promo_codes:
        promo_codes.remove(promo_code)
        with open('promo.txt', 'w') as file:
            file.write('\n'.join(promo_codes))
        return True

    return False



@dp.message_handler(commands=['purchase'])
async def send_upi_id(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in premium_users:
        await message.answer("You are already a Premium User.")
    else:
        await message.answer("<b>⚡To purchase a Premium subscription\n━━━━━━━━━━━━</b>\n<b>➔ UPI :</b> <code>sukytopatillalitli@fam</code>\n－－－－－－－－－－－－\nMake sure to send a screenshot of the payment proof.", parse_mode='HTML')
        await message.answer("Please note that it may take some time for admin confirmation.")
        pending_payments[user_id] = False

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_payment_proof(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in pending_payments and not pending_payments[user_id]:
        pending_payments[user_id] = True
        await message.answer("Payment proof received. Please wait for admin confirmation.")

        admin_keyboard = InlineKeyboardMarkup()
        approve_button = InlineKeyboardButton("Approve", callback_data=f'approve_{user_id}')
        reject_button = InlineKeyboardButton("Reject", callback_data=f'reject_{user_id}')
        admin_keyboard.add(approve_button, reject_button)

        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption="Payment Proof", reply_markup=admin_keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('approve_') or c.data.startswith('reject_'))
async def process_payment_confirmation(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.data.split('_')[1]
    if user_id in pending_payments and pending_payments[user_id]:
        if callback_query.data.startswith('approve_'):
            premium_users.add(user_id)
            # Save the updated premium users list to the file
            save_premium_users(premium_users)
            await bot.send_message(user_id, "<b>PAYMENT SUCCESSFUL ✅</b>\n－－－－－－－－－－－－\n<b>Thanks For Purchasing Our Premium Plan this is a receipt for your plan.saved it in a Secure Place.This will help you if anything goes wrong with your plan purchases . </b>", parse_mode='HTML')
        else:
            await bot.send_message(user_id, "❌ Your payment proof has been rejected.Please send a valid proof.")
        pending_payments[user_id] = False

@dp.callback_query_handler(lambda c: c.data == 'get_live')
async def process_callback_btn1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    current_time = time.time()
    if user_id not in users_received or current_time - users_received_time[user_id] >= 15:  # Changed from 60 to 15 seconds
        if live_messages:
            if live_single_line:
                live_message = live_messages[0]
                first_line = live_message.split('\n')[0]
                users_received[user_id] = first_line
                users_received_time[user_id] = current_time
                if not broadcast_live:
                    live_messages[0] = live_message[len(first_line)+1:]
                    if not live_messages[0]:
                        live_messages.pop(0)
                await bot.send_message(user_id, first_line)
            else:
                live_message = live_messages[0]
                users_received[user_id] = live_message
                users_received_time[user_id] = current_time
                if not broadcast_live:
                    live_messages.pop(0)
                await bot.send_message(user_id, live_message)
        else:
            await bot.send_message(user_id, "No more live CC available")
    else:
        await bot.send_message(user_id, "You have 15 seconds to claim new live CC")  # Changed from 60 to 15 seconds

@dp.callback_query_handler(lambda c: c.data == 'get_charge')
async def process_callback_btn2(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    if charge_messages:
        if charge_single_line:
            charge_message = charge_messages[0]
            first_line = charge_message.split('\n')[0]
            if not broadcast_charge:
                charge_messages[0] = charge_message[len(first_line)+1:]
                if not charge_messages[0]:
                    charge_messages.pop(0)
            await bot.send_message(callback_query.from_user.id, first_line)
        else:
            charge_message = charge_messages[0]
            if not broadcast_charge:
                charge_messages.pop(0)
            await bot.send_message(callback_query.from_user.id, charge_message)
    else:
        await bot.send_message(callback_query.from_user.id, "No more charged available")

@dp.message_handler(commands=['addlivemessage'])
async def add_live_message(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.answer("You are not authorized to use this command.")
    live_message = message.text.split("/addlivemessage ", 1)[1]
    live_messages.append(live_message)
    return await message.answer("Live messages added successfully")

@dp.message_handler(commands=['addchargemessage'])
async def add_charge_message(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.answer("You are not authorized to use this command.")
    charge_message = message.text.split("/addchargemessage ", 1)[1]
    # Check if the charge_messages still contains the initial message
    if "No More Charge CC Left" in charge_messages:
        charge_messages.remove("No More Charge CC Left")
    charge_messages.append(charge_message)
    return await message.answer("Charge message added successfully")

@dp.message_handler(commands=['togglechargemode'])
async def toggle_charge_mode(message: types.Message):
    global charge_single_line, broadcast_charge
    if str(message.from_user.id) != ADMIN_ID:
        return await message.answer("You are not authorized to use this command.")
    charge_single_line = not charge_single_line
    broadcast_charge = not broadcast_charge
    mode = "single line" if charge_single_line else "whole message"
    broadcast_mode = "broadcast to all users" if broadcast_charge else "individual users"
    return await message.answer(f"Charge mode changed to: {mode}\nCharge broadcast mode: {broadcast_mode}")

@dp.message_handler(commands=['togglelivemode'])
async def toggle_live_mode(message: types.Message):
    global live_single_line, broadcast_live
    if str(message.from_user.id) != ADMIN_ID:
        return await message.answer("You are not authorized to use this command.")
    live_single_line = not live_single_line
    broadcast_live = not broadcast_live
    mode = "single line" if live_single_line else "whole message"
    broadcast_mode = "broadcast to all users" if broadcast_live else "individual users"
    return await message.answer(f"Live mode changed to: {mode}\nLive broadcast mode: {broadcast_mode}")

start_polling(dp, skip_updates=True)
  
