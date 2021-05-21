import random 
import json
from majortom_gateway.command import Command

# TRANSLATION

def translate_command_to_binary(command):
    # For the stub, we will go to a json string and back instead of binary
    bytes = json.dumps(command.json_command).encode('utf-8')
    return bytes

def translate_binary_to_command(bytes):
    command = json.loads(bytes.decode('utf-8'))
    return Command(command)

# PACKETIZATION

def packetize(data):
    # Placeholder for packetization
    return data

def depacketize(data):
    # Stub for depacketization
    return data


# ENCRYPTION

def decrypt(data):
    # Stub for decryption logic
    return data

def encrypt(data):
    # Stub for encryption logic
    return data

# DATA PROCESSING

def is_payload_data(data):
    return random.choice([True, False])


# ROUTING
def send_to_data_pipeline(data):
    pass


# DEBUG

def debug_hexprint(bytes):
    print(bytes.hex("-"))