import socket
import sys
from time import strftime, localtime
import os
import json
import sqlite3


host = 'localhost'
port = 8080
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
DB_FILE = 'socket.db'

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
db = sqlite3.connect(DB_FILE)


def db_init():

    cur = db.cursor()
    cur.execute("""
        Create table if not exists users (
        username text primary key,
        password text
        );
    """)
    cur.execute("""
        Create table if not exists tweets (
        id integer primary key autoincrement,
        username text,
        tweets text,
        FOREIGN KEY(username) REFERENCES users(username)
        );
    """)
    cur.execute('INSERT OR IGNORE into users (username,password) values (?, ?)',
                ('admin', 'admin'))
    cur.execute('INSERT OR IGNORE into users (username,password) values (?, ?)',
                ('Rick', 'glipglop'))
    cur.execute('INSERT OR IGNORE into users (username,password) values (?, ?)',
                ('Morty', 'awjeez'))
    cur.execute('INSERT OR IGNORE into users (username,password) values (?, ?)',
                ('Summer', 'toocool'))
    cur.execute('INSERT OR IGNORE into users (username,password) values (?, ?)',
                ('Jerry', 'weak'))
    cur.execute('INSERT OR IGNORE into users (username,password) values (?, ?)',
                ('Beth', 'animals'))
    cur.execute("select * from users")
    rows = cur.fetchall()
    print("[🔑 Here's the username/passwords that you can login with!]:")
    for row in rows:
        print(row)
    db.commit()
    print('====================================================================')
    # DB INIT !


print("Launching HTTP server on", host, ":", port)
try:
    sock.bind((host, port))
    work = True
    print("Server successfully acquired the socket with port:", port)
except:
    work = False
    print("Port is not free.")
print('====================================================================')


def generate_headers(code, auth=False):
    header_server = 'Server: Http-Server-Po\n'
    header_connection = 'Connection: close\n\n'
    CORS = "Access-Control-Allow-Credentials: true\nAccess-Control-Allow-Origin: *\n"
    if code == 200:
        h = 'HTTP/1.1 200 OK\n'
        h += f'Set-Cookie:auth:{auth};\n'
        h += 'Content-Type: text/html; charset=UTF-8\n'
        h += CORS
    elif code == 404:
        h = 'HTTP/1.1 404 Not Found\n'
    elif code == 401:
        h = 'HTTP/1.1 401 Wrong username/pass\n'

    return h + 'Date: ' + str(strftime("%a, %d %b %Y %H:%M:%S", localtime())) + '\n' + header_server + header_connection


def shutdown():
    global work, sock
    try:
        print("Shutting down the server")
        work = False
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        sys.exit()
    except Exception as e:
        print("Warning: could not shut down the socket. Maybe it was already closed? " + str(e))


def send_file(file_requested, response_headers):

    file_requested = os.path.join(
        THIS_FOLDER + "\\" + file_requested)
    print("Serving web page [", file_requested, "]")
    # Load file content
    try:
        file_handler = open(file_requested, 'rb')
        response_content = file_handler.read()
        file_handler.close()

    except Exception as e:
        print("Warning, file not found. Serving response code 404\n")
        response_headers = generate_headers(404)
        response_content = b"<html><body><p>Error 404: File not found</p><p>Python HTTP server</p></body></html>"
    data = response_headers.encode() + response_content
    conn.send(data)
    print("[🚫 Closing connection with client]")
    conn.close()


def is_auth(request):
    try:
        authCookie = request.split(
            "Cookie:")[1].split(':')[1].strip().split(',')[0]
        cookieUsername = request.split("Cookie:")[1].split(",")[1]
        if authCookie == "True":
            print("[✔️ Auth Successful!]")
            response_json = {"authorized": True, "username": str()}
            response_json['username'] = cookieUsername
            response_headers = generate_headers(200, f'True,{cookieUsername}')
            return response_headers.encode() + bytes(json.dumps(response_json), encoding="utf-8")

        else:
            print("[❌ Auth Failed]: Not authorized ?")
            response_json = {"authorized": False, "username": str()}
            response_json['username'] = 'null'
            response_headers = generate_headers(401)
            return response_headers.encode() + bytes(json.dumps(response_json), encoding="utf-8")
    except Exception as e:
        print("[❌ Auth Failed]: No cookie was found ?", e)
        response_json = {"authorized": False, "username": str()}
        response_json['username'] = 'null'
        response_headers = generate_headers(401)
        return response_headers.encode() + bytes(json.dumps(response_json), encoding="utf-8")


def send_response(string, conn):
    global work
    request_method = string.split(' ')[0]
    request_body = string.replace('\n', '\n\t')
    print("[🟢 Request body:]\n\t", request_body)

    if request_method == 'GET':
        path = string.split(' ')[1].split('?')[0]

        if path == '/feed':
            try:
                authCookie = request_body.split(
                    "Cookie:")[1].split(':')[1].strip()
                cookieUsername = request_body.split("Cookie:")[1].split(",")[1]

                cur = db.cursor()
                cur.execute("select tweets,username from tweets")

                rows = cur.fetchall()
                feed = []
                for row in rows:
                    dits = str(row).translate(
                        {ord(c): " " for c in "!@#$%^&*()[]{};:./<>?\|`~-=_+ '"})
                    tweet = dits.split(',')[0]
                    username = dits.split(',')[1]
                    response_json = {"username": str(), "tweet": str()}
                    response_json['username'] = username
                    response_json['tweet'] = tweet
                    feed.append(response_json)

                response = bytes(json.dumps(feed), encoding="utf-8")
                response_headers = generate_headers(
                    200, f'True,{cookieUsername}')
                print('response', type(feed), feed)
                conn.send(response_headers.encode() + response)
                print("[🚫 Closing connection with client]")
                conn.close()
            except:
                response_json = {"authorized": False, "username": str()}
                response_json['username'] = 'null'
                response = bytes(json.dumps(response_json), encoding="utf-8")
                response_headers = generate_headers(401)
                conn.send(response_headers.encode() + response)
                print("[🚫 Closing connection with client]")
                conn.close()

        if path == "/":
            try:
                authCookie = request_body.split(
                    "Cookie:")[1].split(':')[1].strip()
                response_headers = generate_headers(200, authCookie)
                send_file('index.html', response_headers)
            except:
                response_headers = generate_headers(200)
                send_file('index.html', response_headers)

        if path == '/login':
            conn.send(is_auth(request_body))
            print("[🚫 Closing connection with client]")
            conn.close()

    elif request_method == "POST":
        path = string.split(' ')[1].split('?')[0]
        if path == '/feed':
            tweet = request_body.split("tweet:")[1].split(',')[0]
            username = request_body.split("username:")[1].strip()
            print("[username]", username, "[tweet]",  tweet)
            db.execute("Insert into tweets (username,tweets) values (?, ?)",
                       (username, tweet, ))

            cur = db.cursor()
            cur.execute(
                "SELECT username,tweets FROM tweets ")

            rows = cur.fetchall()
            for row in rows:
                response_json = {"username": str(), "tweet": str()}
                response_json['username'] = username
                response_json['tweet'] = tweet

            response_headers = generate_headers(200, f'True,{username}')
            data = response_headers.encode() + bytes(json.dumps(response_json), encoding="utf-8")
            conn.send(data)
            db.commit()
            print("[🚫 Closing connection with client]")
            conn.close()
        if path == '/login':
            try:
                username = request_body.split("user_name:")[1].split(',')[0]
                password = request_body.split("password:")[1]
                cur = db.cursor()
                cur.execute(
                    'select * from users where username = ?', (username,))
                rows = cur.fetchall()
                dits = str(rows).translate(
                    {ord(c): " " for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+ '"})

                if username+password == dits.replace(' ', ''):
                    response_json = {"authorized": True, "username": str()}
                    response_json['username'] = username
                    response_headers = generate_headers(
                        200, f'authTrue,{username}')
                    response = response_headers.encode(
                    ) + bytes(json.dumps(response_json), encoding="utf-8")
                    conn.send(response)
                    print("[🚫 Closing connection with client]")
                    conn.close()
                else:
                    response_json = {"authorized": False, "username": str()}
                    response_json['username'] = 'null'
                    response_headers = generate_headers(401)

                    response = response_headers.encode(
                    ) + bytes(json.dumps(response_json), encoding="utf-8")
                    conn.send(response)
                    print("[🚫 Closing connection with client]")
                    conn.close()

            except Exception as e:
                print("❌ [Post Error]:", e)
        if path == '/logout':
            response_headers = generate_headers(200)
            response_content = "You've been logged out successfully!"
          #  send_file('index.html', response_headers)
            response = response_headers.encode() + response_content.encode()
            conn.send(response)
            print("[🚫 Closing connection with client]")
            conn.close()

    elif request_method == "OPTIONS":
        try:
            authCookie = request_body.split(
                "Cookie:")[1].split(':')[1].strip()
            response_headers = generate_headers(200, True)
            conn.send(response_headers)
            print("Options")
            print("[🚫 Closing connection with client]")
            conn.close()
        except:
            print("error options")

    else:
        print("❌ [Unknown HTTP request method]:", request_method)


sock.listen(3)
db_init()

while work:
    print('waiting... ')
    conn, addr = sock.accept()
    print("Got connection from:", addr)
    data = conn.recv(1024)
    send_response(bytes.decode(data), conn)
    print('--------------------------------------------------------------------------------')

print('Shutting down')
shutdown()
