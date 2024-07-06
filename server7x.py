import asyncio
from bleak import BleakClient
import struct
import wave
import time
import os

ADDRESS = "dc:f6:dd:24:45:ca"
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

audio_data = bytearray()
is_receiving = True
last_receive_time = 0

def notification_handler(sender, data):
    global audio_data, is_receiving, last_receive_time
    audio_data.extend(data)
    last_receive_time = time.time()
    print(f"Received {len(data)} bytes of audio data. Total: {len(audio_data)} bytes")

async def main():
    global is_receiving, last_receive_time
    client = BleakClient(ADDRESS)
    try:
        await client.connect()
        print(f"Connected: {client.is_connected}")
        
        await client.start_notify(UART_TX_CHAR_UUID, notification_handler)
        
        start_time = time.time()
        last_receive_time = start_time
        while time.time() - start_time < 30 and is_receiving:  # Increased timeout to 30 seconds
            await asyncio.sleep(0.1)
            if time.time() - last_receive_time > 5:  # If no data received for 5 seconds, break
                print("No data received for 5 seconds. Stopping.")
                break
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if client.is_connected:
            try:
                await client.stop_notify(UART_TX_CHAR_UUID)
            except:
                pass
        await client.disconnect()
        print("Disconnected")
    
    # Save the received audio data to a WAV file
    if audio_data:
        i = 1
        while os.path.exists(f"received_audio_{i}.wav"):
            i += 1
        filename = f"received_audio_{i}.wav"
        
        with wave.open(filename, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_data)
        
        print(f"Audio saved to {filename} ({len(audio_data)} bytes)")
        print(f"Audio duration: {len(audio_data) / 32000:.2f} seconds")
        
        print("First 10 audio samples:")
        for i in range(0, min(20, len(audio_data)), 2):
            sample = struct.unpack("<h", audio_data[i:i+2])[0]
            print(f"{sample:5d}", end=" ")
        print()
    else:
        print("No audio data received")

asyncio.run(main())