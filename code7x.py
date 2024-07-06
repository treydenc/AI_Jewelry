import array
import time
import board
import audiobusio
import digitalio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

# Setup BLE
ble = BLERadio()
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)

# Setup microphone power
micpwr = digitalio.DigitalInOut(board.MIC_PWR)
micpwr.direction = digitalio.Direction.OUTPUT
micpwr.value = True
time.sleep(0.1)  # Give the microphone time to power up

# Setup PDM microphone
mic = audiobusio.PDMIn(board.PDM_CLK, board.PDM_DATA, sample_rate=16000, bit_depth=16)

buffer = array.array("H", [0] * 800)  # 0.05 seconds of audio at 16kHz

print("XIAO nRF52840 Audio Bluetooth Server")

while True:
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass
    
    print("Connected! Sending 15 seconds of audio...")
    print(f"Starting audio transmission at {time.monotonic():.2f}")
    
    start_time = time.monotonic()
    while ble.connected and time.monotonic() - start_time < 10:  # 15 seconds of audio
        mic.record(buffer, len(buffer))
        
        # Apply gain reduction
        gain = 0.8  # Adjust this value to change sensitivity (lower = less sensitive)
        scaled_buffer = array.array("H", [min(int(sample * gain), 65535) for sample in buffer])
        
        byte_data = bytes(scaled_buffer)
        
        chunk_size = 20  # Adjusted to match what the server is receiving
        for i in range(0, len(byte_data), chunk_size):
            chunk = byte_data[i:i+chunk_size]
            uart_server.write(chunk)
        
        print(f"Sent 0.05 seconds of audio. Time elapsed: {time.monotonic() - start_time:.2f}s. Bytes sent: {len(byte_data)}")
        time.sleep(0.01)  # Small delay to allow server processing
    
    print(f"Finished sending audio at {time.monotonic():.2f}")
    ble.stop_advertising()
    while ble.connected:
        pass
    print("Disconnected. Waiting for next connection...")