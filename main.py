from http.server import SimpleHTTPRequestHandler, HTTPServer
import socketserver
import json
import threading
import time

invitados = {}  
last_post_data = {}  
detected_guests = set()  # Conjunto para almacenar los nombres de los invitados detectados
EXPIRATION_TIME = 5


with open("invitados.txt", "r") as file:
    for line in file:
        name, id_hex = line.strip().split(",")
        invitados[id_hex] = name

def find_invitado(id_hex):
    return invitados.get(id_hex, None)

def remove_expired_invitados():
    
    while True:
        current_time = time.time()
        non_expired_invitados = {invitado: last_post_time for invitado, last_post_time in last_post_data.items() if current_time - last_post_time <= EXPIRATION_TIME}

        # Reemplazar el diccionario last_post_data con el diccionario de invitados no expirados
        last_post_data.update(non_expired_invitados)

        time.sleep(EXPIRATION_TIME)


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == "/api/guests":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            # Filtrar invitados no expirados
            current_time = time.time()
            non_expired_invitados = {invitado: last_post_time for invitado, last_post_time in last_post_data.items() if current_time - last_post_time <= EXPIRATION_TIME}
            
            response_data = json.dumps(list(non_expired_invitados.keys()))
            self.wfile.write(response_data.encode("utf-8"))
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
            # Busca al invitado aquí en lugar de hacerlo fuera de este método
            invitado = find_invitado(id_hex)
            if invitado:
                last_post_data[invitado] = time.time()
                print(f"Invitado: {invitado}, idHex: {id_hex}")


if __name__ == "__main__":
  
    t = threading.Thread(target=remove_expired_invitados, daemon=True)
    t.start()

    PORT = 6969
    handler = CustomHTTPRequestHandler
    httpd = socketserver.TCPServer(("0.0.0.0", PORT), handler)
    print(f"Serving on port {PORT}")
    httpd.serve_forever()