import json
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.file = 'data.json'
        self.load()
    
    def load(self):
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {
                'users': {},
                'banned': [],
                'plans': [],
                'pending_payments': [],
                'cloned_bots': {},
                'message_map': {},
                'greetings': [
                    "✅ Message sent to owner!",
                    "✨ Your message has been forwarded!",
                    "📨 Message delivered successfully!",
                    "👍 Owner will see your message!",
                    "🎯 Message sent! Owner will reply soon!",
                    "💬 Your message is on its way!",
                    "✉️ Successfully sent to owner!",
                    "🚀 Message delivered!",
                    "📬 Owner has received your message!"
                ]
            }
            self.save()
    
    def save(self):
        with open(self.file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_user(self, uid, username, fname):
        s = str(uid)
        if s not in self.data['users']:
            self.data['users'][s] = {
                'id': uid,
                'username': username,
                'name': fname,
                'joined': datetime.now().isoformat(),
                'is_active': True
            }
            self.save()
    
    def get_user(self, uid):
        return self.data['users'].get(str(uid))
    
    def get_all_users(self):
        return self.data['users']
    
    def get_active_users(self):
        return {k: v for k, v in self.data['users'].items() if v.get('is_active', True)}
    
    def get_banned_users(self):
        return {k: v for k, v in self.data['users'].items() if int(k) in self.data['banned']}
    
    def ban_user(self, uid):
        if uid not in self.data['banned']:
            self.data['banned'].append(uid)
            if str(uid) in self.data['users']:
                self.data['users'][str(uid)]['is_active'] = False
            self.save()
    
    def unban_user(self, uid):
        if uid in self.data['banned']:
            self.data['banned'].remove(uid)
            if str(uid) in self.data['users']:
                self.data['users'][str(uid)]['is_active'] = True
            self.save()
    
    def is_banned(self, uid):
        return uid in self.data['banned']
    
    def add_plan(self, days, price, upi_id):
        plan = {
            'id': len(self.data['plans']) + 1,
            'days': days,
            'price': price,
            'upi_id': upi_id,
            'created': datetime.now().isoformat()
        }
        self.data['plans'].append(plan)
        self.save()
        return plan
    
    def get_plans(self):
        return self.data['plans']
    
    def delete_plan(self, plan_id):
        self.data['plans'] = [p for p in self.data['plans'] if p['id'] != plan_id]
        self.save()
    
    def add_pending_payment(self, user_id, plan_id, screenshot):
        plan = next((p for p in self.data['plans'] if p['id'] == plan_id), None)
        if not plan:
            return None
        
        payment = {
            'id': len(self.data['pending_payments']) + 1,
            'user_id': user_id,
            'plan_id': plan_id,
            'plan_days': plan['days'],
            'plan_price': plan['price'],
            'screenshot': screenshot,
            'time': datetime.now().isoformat(),
            'status': 'pending'
        }
        self.data['pending_payments'].append(payment)
        self.save()
        return payment
    
    def get_pending_payments(self):
        return [p for p in self.data['pending_payments'] if p['status'] == 'pending']
    
    def approve_payment(self, payment_id):
        for p in self.data['pending_payments']:
            if p['id'] == payment_id:
                p['status'] = 'approved'
                self.save()
                return p
        return None
    
    def reject_payment(self, payment_id):
        for p in self.data['pending_payments']:
            if p['id'] == payment_id:
                p['status'] = 'rejected'
                self.save()
                return True
        return False
    
    def add_cloned_bot(self, user_id, bot_token, plan_days):
        expiry = datetime.now() + timedelta(days=plan_days)
        self.data['cloned_bots'][str(user_id)] = {
            'bot_token': bot_token,
            'created': datetime.now().isoformat(),
            'expiry': expiry.isoformat(),
            'plan_days': plan_days,
            'active': True
        }
        self.save()
    
    def get_cloned_bot(self, user_id):
        bot = self.data['cloned_bots'].get(str(user_id))
        if bot and bot['active']:
            expiry = datetime.fromisoformat(bot['expiry'])
            if datetime.now() > expiry:
                bot['active'] = False
                self.save()
                return None
            return bot
        return None
    
    def map_message(self, user_id, owner_msg_id):
        self.data['message_map'][str(owner_msg_id)] = user_id
        self.save()
    
    def get_user_from_msg(self, owner_msg_id):
        return self.data['message_map'].get(str(owner_msg_id))
    
    def get_random_greeting(self):
        import random
        return random.choice(self.data['greetings'])

db = Database()
