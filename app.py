from aiohttp import web
import socketio

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

user_data = {}

async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

@sio.on('join')
async def join(sid, data):
    room = data['room']
    await sio.enter_room(sid, room)
    user_data[sid] = {'x': 0, 'y': 0, 'last_click': None}
    for user_sid, user_info in user_data.items():
        if user_sid != sid:
            await sio.emit('update_position', {'sid': user_sid, 'x': user_info['x'], 'y': user_info['y']}, room=sid)
            if user_info['last_click']:
                await sio.emit('update_left_click', {'sid': user_sid, 'x': user_info['last_click'][0], 'y': user_info['last_click'][1]}, room=sid)
    print(f"{sid} has joined room {room}")

@sio.on('mouse_position')
async def mouse_position(sid, data):
    room = data.get('room')
    if sid not in user_data:
        user_data[sid] = {}
    user_data[sid]['x'] = data['x']
    user_data[sid]['y'] = data['y']
    await sio.emit('update_position', {'sid': sid, 'x': data['x'], 'y': data['y']}, room=room)

@sio.on('left_click')
async def left_click(sid, data):
    room = data.get('room')
    user_data[sid]['last_click'] = (data['x'], data['y'])
    await sio.emit('update_left_click', {'sid': sid, 'x': data['x'], 'y': data['y']}, room=room)

@sio.on('disconnect')
async def disconnect(sid):
    rooms = sio.rooms(sid)
    for room in rooms:
        await sio.leave_room(sid, room)
    del user_data[sid]
    print(f"{sid} has left the room(s)")

app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)
