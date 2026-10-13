import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class LiveUpdatesConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        self.groups_joined = []

        # Join public stock and inventory updates group
        await self.channel_layer.group_add('stock_updates', self.channel_name)
        self.groups_joined.append('stock_updates')

        # If authenticated, join user-specific notification group
        if self.user and self.user.is_authenticated:
            user_group = f"user_{self.user.id}"
            await self.channel_layer.group_add(user_group, self.channel_name)
            self.groups_joined.append(user_group)

        await self.accept()

        await self.send_json({
            'type': 'connection_established',
            'message': 'Connected to LumaCart real-time notification stream.',
            'is_authenticated': bool(self.user and self.user.is_authenticated)
        })

    async def disconnect(self, close_code):
        for group in self.groups_joined:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, content):
        msg_type = content.get('type')
        if msg_type == 'ping':
            await self.send_json({'type': 'pong'})

    # Group event handlers
    async def stock_updated(self, event):
        await self.send_json({
            'type': 'stock_updated',
            'product_id': event.get('product_id'),
            'variant_id': event.get('variant_id'),
            'sku': event.get('sku'),
            'available_stock': event.get('available_stock')
        })

    async def order_status_updated(self, event):
        await self.send_json({
            'type': 'order_status_updated',
            'order_number': event.get('order_number'),
            'status': event.get('status'),
            'message': event.get('message')
        })

    async def cart_updated(self, event):
        await self.send_json({
            'type': 'cart_updated',
            'message': event.get('message', 'Cart updated')
        })

    async def broadcast_message(self, event):
        await self.send_json({
            'type': 'broadcast',
            'title': event.get('title'),
            'message': event.get('message')
        })
