from http.server import SimpleHTTPRequestHandler, HTTPServer
import socketserver
import json
import threading
import time
import csv

invitados = {}  
last_post_data = {}  
detected_guests = set()  
EXPIRATION_TIME = 5
with open("invitados.csv", "r") as file:
    reader = csv.reader(file)
    for line in reader:
        if len(line) == 5:
            id_hex, nombre, apellido, organizacion, estado = line
            invitados[id_hex] = {
                "nombre": nombre,
                "apellido": apellido,
                "organizacion": organizacion,
                "estado": estado
            }
        else:
            print(f"Error: La siguiente línea tiene un número incorrecto de campos: {line}")

def find_invitado(id_hex):
    return invitados.get(id_hex, None)

def remove_expired_invitados():
    while True:
        current_time = time.time()
        non_expired_invitados = {invitado: last_post_time for invitado, last_post_time in last_post_data.items() if current_time - last_post_time <= EXPIRATION_TIME}
        last_post_data.update(non_expired_invitados)
        time.sleep(EXPIRATION_TIME)

def update_invitado_status_in_csv(id_hex, new_status):
    with open("invitados.csv", "r") as file:
        lines = file.readlines()

    with open("invitados.csv", "w") as file:
        for line in lines:
            if line.startswith(id_hex):
                line = ','.join(line.split(',')[:-1]) + f",{new_status}\n"
            file.write(line)

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/guests":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            current_time = time.time()
            non_expired_invitados = {invitado: last_post_time for invitado, last_post_time in last_post_data.items() if current_time - last_post_time <= EXPIRATION_TIME}

            response_data = []
            for invitado_id in non_expired_invitados.keys():
                invitado = find_invitado(invitado_id)
                if invitado and invitado["estado"] == "A":
                    response_data.append({
                        "nombre": invitado["nombre"],
                        "apellido": invitado["apellido"],
                        "organizacion": invitado["organizacion"]
                    })

            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        client_ip = self.client_address[0]
        print(f"Anthena: {client_ip}")

        decoded_data = post_data.decode('utf-8')
        json_data = json.loads(decoded_data)

        if isinstance(json_data, list):
            for item in json_data:
                self.process_post_data(item)
        elif isinstance(json_data, dict):
            self.process_post_data(json_data)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Received POST data")

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def process_post_data(self, item):
        id_hex = item['data'].get('idHex', None)
        if id_hex:
            invitado = find_invitado(id_hex)
            if invitado:
                last_post_data[id_hex] = time.time()
                print(f"Invitado: {invitado}, idHex: {id_hex}")
                if invitado["estado"] == "F":
                    invitado["estado"] = "A"
                    update_invitado_status_in_csv(id_hex, "A")


if __name__ == "__main__":
    t = threading.Thread(target=remove_expired_invitados, daemon=True)
    t.start()

    PORT = 6969
    handler = CustomHTTPRequestHandler
    httpd = socketserver.TCPServer(("0.0.0.0", PORT), handler)
    print(f"Serving on port {PORT}")
    httpd.serve_forever()

