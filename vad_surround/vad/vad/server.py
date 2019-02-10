import socket 
import sys 
import json

from surround import Surround, Config
from stages import VadData, ValidateData, VadDetection

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 1024))

    surround = Surround([ValidateData(), VadDetection()])
    config = Config()
    surround.set_config(config)

    surround.init_stages()

    while True:
        audio_input = []
        source_addr = None

        while len(audio_input) < 48000:
            # Retrieve data from client (9600 samples in bytes = 9600 * 2 bytes (2 bytes per sample))
            data_bytes, source_addr = sock.recvfrom(9600 * 2)

            # Convert the byte array into an array of float samples (-1 to 1)
            for i in range(0, len(data_bytes), 2):
                sample = int.from_bytes(data_bytes[i : i + 2], sys.byteorder, signed=True)
                sample /= 32767.0

                audio_input.append(sample)

        data = VadData(audio_input)
        surround.process(data)

        if data.error is None and data.output_data is not None:
            print("Noise: " + str(data.output_data[0] * 100.0) + " Voice: " + str(data.output_data[1] * 100.0))

            # Sending the results back to who made the request
            sock.sendto(json.dumps({ "noise": data.output_data[0], "voice:": data.output_data[1] }), address=(source_addr[0], 25565))
        else:
            print(data.error)
            break
        

if __name__ == "__main__":
    main()
