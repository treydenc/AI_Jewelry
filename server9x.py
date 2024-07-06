import asyncio
from bleak import BleakClient
import struct
import wave
import time

ADDRESS = "e5:6e:0f:db:b0:08"  # Your XIAO's Bluetooth address
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

audio_data = bytearray()

def notification_handler(sender, data):
    global audio_data
    audio_data.extend(data)
    print(f"Received {len(data)} bytes of audio data. Total: {len(audio_data)} bytes")

async def main():
    client = BleakClient(ADDRESS)
    try:
        await client.connect()
        print(f"Connected: {client.is_connected}")
        
        services = await client.get_services()
        for service in services:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                print(f"  Characteristic: {char.uuid}")
                print(f"    Properties: {char.properties}")
        
        await client.start_notify(UART_TX_CHAR_UUID, notification_handler)
        print("Started notifications on UART TX characteristic")
        
        print("Waiting for audio data...")
        start_time = time.time()
        while time.time() - start_time < 15:  # 15 seconds timeout
            await asyncio.sleep(0.1)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if client.is_connected:
            try:
                await client.stop_notify(UART_TX_CHAR_UUID)
                await client.disconnect()
            except Exception as e:
                print(f"Error during disconnect: {e}")
        print("Disconnected")
    
    if audio_data:
        with wave.open("received_audio.wav", "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_data)
        
        print(f"Audio saved to received_audio.wav ({len(audio_data)} bytes)")
        print(f"Audio duration: {len(audio_data) / 32000:.2f} seconds")
    else:
        print("No audio data received")

asyncio.run(main())