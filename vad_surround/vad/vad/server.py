import socket 
import sys 

from surround import Surround, Config
from .stages import VadData, ValidateData, VadDetection

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 1024))

    surround = Surround([ValidateData(), VadDetection()])
    config = Config()
    surround.set_config(config)

    surround.init_stages()

    while True:
        # Retrieve data from client (9600 samples in bytes = 9600 * 2 bytes (2 bytes per sample))
        data_bytes, _ = sock.recvfrom(9600 * 2)
        data = []

        # Convert the byte array into an array of float samples (-1 to 1)
        j = 0
        for _ in range(int(len(data_bytes) / 2)):
            two_bytes = [data_bytes[j], data_bytes[j+1]]
            data.append(int.from_bytes(two_bytes, sys.byteorder, signed=True) / 32767.0)
            j += 2

        data = VadData(data)
        surround.process(data)

        if data.error is None:
            print(data.output_data)
        else:
            print(data.error)
        

if __name__ == "__main__":
    main()