import time
import board
import audiobusio
import array
import digitalio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

ble = BLERadio()
uart_service = UARTService()
advertisement = ProvideServicesAdvertisement(uart_service)

# Setup microphone power
micpwr = digitalio.DigitalInOut(board.MIC_PWR)
micpwr.direction = digitalio.Direction.OUTPUT
micpwr.value = True
time.sleep(0.1)

mic = audiobusio.PDMIn(board.PDM_CLK, board.PDM_DATA, sample_rate=16000, bit_depth=16)

buffer = array.array("H", [0] * 160)  # 0.01 seconds of audio at 16kHz, 16-bit

print("XIAO nRF52840 Audio Bluetooth Server")
print(f"UART Service UUID: {uart_service.uuid}")

while True:
    print("Starting advertising...")
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass
    
    print("Connected! Streaming audio...")
    start_time = time.monotonic()
    
    while ble.connected and time.monotonic() - start_time < 10:
        mic.record(buffer, len(buffer))
        uart_service.write(bytes(buffer))
        print(f"Sent {len(buffer)} samples. Time: {time.monotonic() - start_time:.2f}s")
    
    print("Finished streaming audio")
    ble.stop_advertising()
    while ble.connected:
        pass
    print("Disconnected. Waiting for next connection...")