import json
from bottle import Bottle, request, response, static_file, run
from gevent import monkey; monkey.patch_all()
from gevent.pywsgi import WSGIServer
from socketio import Server, WSGIApp

bottle_app = Bottle()
sio = Server(cors_allowed_origins='*')
app = WSGIApp(sio, bottle_app)

user_data = {}

@bottle_app.route('/')
def index():
    return static_file('index.html', root='./')

@sio.on('join')
def join(sid, data):
    room = data['room']
    sio.enter_room(sid, room)
    user_data[sid] = {'x': 0, 'y': 0, 'last_click': None}
    for user_sid, user_info in user_data.items():
        if user_sid != sid:
            sio.emit('update_position', {'sid': user_sid, 'x': user_info['x'], 'y': user_info['y']}, room=sid)
            if user_info['last_click']:
                sio.emit('update_left_click', {'sid': user_sid, 'x': user_info['last_click'][0], 'y': user_info['last_click'][1]}, room=sid)
    print(f"{sid} has joined room {room}")

@sio.on('mouse_position')
def mouse_position(sid, data):
    room = data.get('room')
    user_data[sid]['x'] = data['x']
    user_data[sid]['y'] = data['y']
    sio.emit('update_position', {'sid': sid, 'x': data['x'], 'y': data['y']}, room=room)

@sio.on('left_click')
def left_click(sid, data):
    room = data.get('room')
    user_data[sid]['last_click'] = (data['x'], data['y'])
    sio.emit('update_left_click', {'sid': sid, 'x': data['x'], 'y': data['y']}, room=room)

@sio.on('disconnect')
def disconnect(sid):
    rooms = sio.rooms(sid)
    for room in rooms:
        sio.leave_room(sid, room)
    del user_data[sid]
    print(f"{sid} has left the room(s)")

if __name__ == '__main__':
    server = WSGIServer(('0.0.0.0', 8080), app)
    server.serve_forever()
