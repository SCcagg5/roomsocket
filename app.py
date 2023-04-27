from aiohttp import web
import socketio

class User:
    def __init__(self, sid, x, y, last_click=None):
        self.sid = sid
        self.x = x
        self.y = y
        self.email = None
        self.last_click = last_click

sio = socketio.AsyncServer(cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

user_data = {}
rooms = {}

async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

@sio.on('join')
async def join(sid, data):
    room = data['room']
    sio.enter_room(sid, room)
    user_data[sid] = User(sid, 0, 0, data['email'])
    if room not in rooms:
        rooms[room] = set()
    rooms[room].add(sid)
    for user_sid in rooms[room]:
        if user_sid != sid:
            user = user_data[user_sid]
            await sio.emit('update_position', {'sid': user.sid, 'email': user.email, 'x': user.x, 'y': user.y}, room=sid)
            if user.last_click:
                await sio.emit('update_left_click', {'sid': user.sid, 'x': user.last_click[0], 'y': user.last_click[1]}, room=sid)
    print(f"{sid} has joined room {room}")

@sio.on('get_rooms')
async def get_rooms(sid, data):
    room_data = {}
    for room, users in rooms.items():
        room_data[room] = list(users)
    print(room_data)
    await sio.emit('room_data', room_data)

@sio.on('mouse_position')
async def mouse_position(sid, data):
    room = data.get('room')
    if sid not in user_data:
        user_data[sid] = User(sid, 0, 0)
    user_data[sid].x = data['x']
    user_data[sid].y = data['y']
    await sio.emit('update_position', {'sid': sid, 'x': data['x'], 'y': data['y']}, room=room)
    
@sio.on('email')
async def email_update(sid, data):
    room = data.get('room')
    if sid not in user_data:
        user_data[sid] = User(sid, 0, 0)
    user_data[sid].email = data['email']
    await sio.emit('update_position', {'sid': sid, 'email': data['email']}, room=room)

@sio.on('left_click')
async def left_click(sid, data):
    room = data.get('room')
    if sid not in user_data:
        user_data[sid] = User(sid, 0, 0)
    user_data[sid].last_click = (data['x'], data['y'])
    await sio.emit('update_left_click', {'sid': sid, 'x': data['x'], 'y': data['y']}, room=room)

@sio.on('disconnect')
async def disconnect(sid):
    for room in sio.rooms(sid):
        sio.leave_room(sid, room)
        if room in rooms:
            rooms[room].discard(sid)
    if sid in user_data:
        del user_data[sid]
    room_data = {}
    for room, users in rooms.items():
        room_data[room] = list(users)
    await sio.emit('room_data', room_data)
    print(f"{sid} has left the room(s)")

app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)
