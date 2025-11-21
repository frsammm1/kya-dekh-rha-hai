from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
import logging

logger = logging.getLogger(__name__)

async def user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if db.is_banned(user.id):
        await update.message.reply_text("⛔️ You are banned from using this bot.")
        return
    
    db.add_user(user.id, user.username, user.first_name)
    
    keyboard = [
        [InlineKeyboardButton("📩 Send Message to Owner", callback_data="user_send")],
        [InlineKeyboardButton("🤖 Purchase Bot Clone", callback_data="user_plans")],
        [InlineKeyboardButton("📋 My Clone Bot", callback_data="user_mybot")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="user_help")]
    ]
    
    text = f"""
👋 Welcome {user.first_name}!

🎯 User Panel
━━━━━━━━━━━━━━━━
Choose an option below:
"""
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    
    if db.is_banned(user.id):
        return
    
    db.add_user(user.id, user.username, user.first_name)
    owner_id = int(context.bot_data.get('OWNER_ID'))
    
    try:
        # Send header to owner
        header = f"""
📨 New Message from User
━━━━━━━━━━━━━━━━
👤 Name: {user.first_name}
🆔 ID: <code>{user.id}</code>
📱 Username: @{user.username or 'None'}

💬 Content below:
"""
        sent = await context.bot.send_message(owner_id, header, parse_mode='HTML')
        db.map_message(user.id, sent.message_id)
        
        # Forward actual content
        if msg.text:
            content = await context.bot.send_message(owner_id, msg.text)
            db.map_message(user.id, content.message_id)
        elif msg.photo:
            content = await context.bot.send_photo(owner_id, msg.photo[-1].file_id, caption=msg.caption or "")
            db.map_message(user.id, content.message_id)
        elif msg.video:
            content = await context.bot.send_video(owner_id, msg.video.file_id, caption=msg.caption or "")
            db.map_message(user.id, content.message_id)
        elif msg.document:
            content = await context.bot.send_document(owner_id, msg.document.file_id, caption=msg.caption or "")
            db.map_message(user.id, content.message_id)
        elif msg.voice:
            content = await context.bot.send_voice(owner_id, msg.voice.file_id)
            db.map_message(user.id, content.message_id)
        elif msg.audio:
            content = await context.bot.send_audio(owner_id, msg.audio.file_id, caption=msg.caption or "")
            db.map_message(user.id, content.message_id)
        elif msg.video_note:
            content = await context.bot.send_video_note(owner_id, msg.video_note.file_id)
            db.map_message(user.id, content.message_id)
        
        # Random greeting
        greeting = db.get_random_greeting()
        await msg.reply_text(greeting)
        
        logger.info(f"✅ Message from user {user.id} forwarded to owner")
        
    except Exception as e:
        logger.error(f"❌ Error forwarding message: {e}")
        await msg.reply_text("❌ Failed to send message. Please try again.")

async def user_send_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📝 Send your message now:\n\n"
        "You can send:\n"
        "• Text messages\n"
        "• Photos with captions\n"
        "• Videos\n"
        "• Documents\n"
        "• Voice messages\n"
        "• Audio files"
    )

async def user_plans_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plans = db.get_plans()
    
    if not plans:
        await query.message.reply_text("📋 No subscription plans available yet.\n\nPlease check back later!")
        return
    
    text = "🤖 Clone Bot Subscription Plans\n━━━━━━━━━━━━━━━━\n\nChoose a plan:\n"
    
    keyboard = []
    for plan in plans:
        button_text = f"{plan['days']} Day{'s' if plan['days'] > 1 else ''} - ₹{plan['price']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"plan_{plan['id']}")])
    
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    plan_id = int(query.data.split('_')[1])
    
    plans = db.get_plans()
    plan = next((p for p in plans if p['id'] == plan_id), None)
    
    if not plan:
        await query.answer("❌ Plan not found!", show_alert=True)
        return
    
    await query.answer()
    
    # Create UPI payment link
    upi_id = plan['upi_id']
    amount = plan['price']
    note = f"{plan['days']}days"
    
    upi_link = f"upi://pay?pa={upi_id}&am={amount}&cu=INR&tn={note}"
    
    text = f"""
💳 Payment Details
━━━━━━━━━━━━━━━━
📦 Plan: {plan['days']} Day{'s' if plan['days'] > 1 else ''}
💰 Amount: ₹{plan['price']}
🔗 UPI ID: {upi_id}

📝 Instructions:
1. Click "Pay Now" button below
2. Complete payment in your UPI app
3. Take a screenshot of payment
4. Send the screenshot here

⚠️ Note: Send only payment screenshot after completing payment!
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Pay Now", url=upi_link)],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
    ]
    
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Store plan selection
    context.user_data['selected_plan'] = plan_id

async def handle_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment screenshot from user"""
    if 'selected_plan' not in context.user_data:
        return
    
    msg = update.message
    user = update.effective_user
    
    if not msg.photo:
        return
    
    plan_id = context.user_data['selected_plan']
    screenshot = msg.photo[-1].file_id
    
    # Add to pending payments
    payment = db.add_pending_payment(user.id, plan_id, screenshot)
    
    if payment:
        # Notify user
        await msg.reply_text(
            "✅ Payment screenshot received!\n\n"
            "🔍 Your payment is under review.\n"
            "⏳ Please wait for owner approval.\n\n"
            f"Payment ID: #{payment['id']}"
        )
        
        # Notify owner
        owner_id = int(context.bot_data.get('OWNER_ID'))
        owner_text = f"""
💳 New Payment Received!
━━━━━━━━━━━━━━━━
Payment ID: #{payment['id']}
👤 User: {user.first_name}
🆔 ID: <code>{user.id}</code>
📱 Username: @{user.username or 'None'}

📦 Plan: {payment['plan_days']} days
💰 Amount: ₹{payment['plan_price']}
"""
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{payment['id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{payment['id']}")
            ]
        ]
        
        await context.bot.send_photo(
            owner_id,
            screenshot,
            caption=owner_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        # Clear selection
        del context.user_data['selected_plan']
        
        logger.info(f"💳 Payment screenshot from user {user.id} sent to owner")
    else:
        await msg.reply_text("❌ Error processing payment. Please try again.")

async def user_mybot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    clone = db.get_cloned_bot(user_id)
    
    if not clone:
        await query.message.reply_text(
            "�� You don't have an active clone bot.\n\n"
            "Purchase a plan to get your own bot!"
        )
        return
    
    from datetime import datetime
    expiry = datetime.fromisoformat(clone['expiry'])
    days_left = (expiry - datetime.now()).days
    
    text = f"""
🤖 Your Clone Bot
━━━━━━━━━━━━━━━━
✅ Status: Active
📅 Days Left: {days_left}
⏰ Expires: {expiry.strftime('%Y-%m-%d')}

�� Features:
✅ Send messages to users
✅ Receive messages from users
✅ Reply to user messages

Your bot is running! Users can start it and send you messages.
"""
    
    await query.message.reply_text(text)

async def user_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = """
ℹ️ Help & Information
━━━━━━━━━━━━━━━━

🎯 How to use:

1️⃣ Send Message
   Send any message, photo, video, or document to the owner

2️⃣ Purchase Clone Bot
   - View available plans
   - Choose a plan
   - Pay via UPI (auto-filled)
   - Send payment screenshot
   - Wait for approval
   - Send your bot token
   - Your clone bot is ready!

3️⃣ Clone Bot Features
   - Receive messages from your users
   - Reply to user messages
   - All message formats supported

Need help? Send a message to the owner!
"""
    
    await query.message.reply_text(text)

async def cancel_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("❌ Payment cancelled")
    
    if 'selected_plan' in context.user_data:
        del context.user_data['selected_plan']
    
    await query.message.reply_text("❌ Payment cancelled. Use /start to try again.")
