import socket 
import sys 
import json
import time
import logging

from surround import Surround, Config
from stages import VadData, ValidateData, VadDetection

#logging.basicConfig(level=logging.INFO)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 1024))

    surround = Surround([ValidateData(), VadDetection()])
    config = Config()
    surround.set_config(config)

    surround.init_stages()

    audio_input = []
    last_packet_time = time.time()
    packet_id = -1
    last_id = -1
    counter = 0
    packet_loss = 0

    while True:
        source_addr = None

        while len(audio_input) < 48000:
            # Retrieve data from client (9600 samples in bytes = 9600 * 2 bytes (2 bytes per sample))
            data_bytes, source_addr = sock.recvfrom(2400 * 2 + 4)

            if last_packet_time + 5 < time.time():
                audio_input.clear()
                counter = 0
                last_id = -1
                packet_loss = 0

            last_packet_time = time.time()

            packet_id = int.from_bytes(data_bytes[2400 * 2:], sys.byteorder, signed=True)
            
            if last_id + 1 != packet_id: 
                print('Expected: ' + str(last_id + 1) + ' Got: ' + str(packet_id))
                if last_id + 1 < packet_id:
                    packet_loss += packet_id - (last_id + 1)
                print('Packet Loss: ' + str(packet_loss))

            last_id = packet_id

            # Convert the byte array into an array of float samples (-1 to 1)
            for i in range(0, len(data_bytes) - 4, 2):
                sample = int.from_bytes(data_bytes[i : i + 2], sys.byteorder, signed=True)
                sample /= 32767.0

                audio_input.append(sample)

        data = VadData(audio_input)
        surround.process(data)

        audio_input = audio_input[2400:]

        if data.error is None and data.output_data is not None:
            print("Noise: " + str(data.output_data[0] * 100.0) + " Voice: " + str(data.output_data[1] * 100.0))

            # Sending the results back to who made the request
            results = { "id": packet_id, "noise": float(data.output_data[0]), "voice": float(data.output_data[1]) }
            sock.sendto(json.dumps(results).encode(), (source_addr[0], 25565))
        else:
            print(data.error)
            break

if __name__ == "__main__":
    main()
