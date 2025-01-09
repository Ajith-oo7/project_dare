import slixmpp
import asyncio
from config import Config

class MessageClient(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        
    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        
    async def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            from database import send_message
            send_message(
                sender_id=self.boundjid.bare,
                receiver_id=msg['to'].bare,
                content=msg['body']
            )

class XMPPManager:
    def __init__(self):
        self.clients = {}
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    def connect_user(self, user_id, username):
        try:
            jid = f"{username}@{Config.XMPP_SERVER}"
            password = Config.SECRET_KEY
            
            client = MessageClient(jid, password)
            client.connect()
            
            def start_client():
                self.loop.run_until_complete(client.process())
            
            import threading
            thread = threading.Thread(target=start_client)
            thread.daemon = True
            thread.start()
            
            self.clients[user_id] = client
            return True
        except Exception as e:
            print(f"XMPP connection error: {str(e)}")
            return False
            
    def send_message(self, sender_id, receiver_id, content):
        try:
            if sender_id in self.clients:
                client = self.clients[sender_id]
                receiver_jid = f"{receiver_id}@{Config.XMPP_SERVER}"
                
                async def send():
                    client.send_message(
                        mto=receiver_jid,
                        mbody=content,
                        mtype='chat'
                    )
                
                self.loop.run_until_complete(send())
                return True
            return False
        except Exception as e:
            print(f"Send message error: {str(e)}")
            return False 