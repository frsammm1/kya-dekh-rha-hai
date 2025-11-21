# Telegram Reply Bot - Fixed & Enhanced

## Features
✅ Owner sees Owner Panel (not user panel)
✅ Replies work correctly (go to users, not back to owner)
✅ Advanced plan system with UPI auto-fill
✅ Clone bot system with expiry
✅ Clickable user names in stats
✅ Random greetings for users
✅ Always-alive deployment (never sleeps)
✅ No admin system (removed)
✅ No auth keys (removed)

## Deploy on Koyeb
1. Choose **Dockerfile** (not Buildpack)
2. Set environment variables:
   - BOT_TOKEN
   - OWNER_ID
   - OWNER_NAME
3. Port: 8080
4. Deploy!

## Plan System
Owner creates plans with:
- Days (e.g., 1, 7, 30)
- Price (e.g., 1, 5, 100)
- UPI ID

Users click plan button → UPI app opens with pre-filled amount → Pay → Send screenshot → Owner approves → User sends bot token → Clone bot created!
