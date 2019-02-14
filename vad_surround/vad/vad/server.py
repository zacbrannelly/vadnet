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

    while True:
        source_addr = None

        while len(audio_input) < 48000:
            # Retrieve data from client (9600 samples in bytes = 9600 * 2 bytes (2 bytes per sample))
            data_bytes, source_addr = sock.recvfrom(2400 * 2 + 4)

            # If last packet received was 5 seconds ago, clear cache
            if last_packet_time + 5 < time.time():
                audio_input.clear()

            last_packet_time = time.time()

            # Get the packet id from the end of the byte array
            packet_id = int.from_bytes(data_bytes[2400 * 2:], sys.byteorder, signed=True)

            # Convert the byte array into an array of float samples (-1 to 1)
            for i in range(0, len(data_bytes) - 4, 2):
                sample = int.from_bytes(data_bytes[i : i + 2], sys.byteorder, signed=True)
                sample /= 32767.0

                audio_input.append(sample)

        # Process the audio data for voice activity 
        data = VadData(audio_input)
        surround.process(data)

        # Rolling window of 2400 samples (50ms)
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
