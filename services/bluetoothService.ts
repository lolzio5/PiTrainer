import { BleManager } from 'react-native-ble-plx';
import { Buffer } from 'buffer';

const bleManager = new BleManager();

const DEVICE_NAME = "WorkoutDataService"; // Adjust this to match Raspberry Pi's name

export async function connectToDevice() {
    const devices = await bleManager.startDeviceScan(null, null, (error, device) => {
        if (error) {
            console.error("Bluetooth Scan Error:", error);
            return;
        }

        if (device.name === DEVICE_NAME) {
            bleManager.stopDeviceScan();
            device.connect()
                .then((connectedDevice) => {
                    console.log("Connected to", connectedDevice.name);
                    return connectedDevice.discoverAllServicesAndCharacteristics();
                })
                .then((connectedDevice) => {
                    listenForData(connectedDevice);
                })
                .catch(err => console.error("Connection Error:", err));
        }
    });
}

async function listenForData(device) {
    const characteristicUUID = "your-characteristic-uuid"; // Replace with actual characteristic UUID

    device.monitorCharacteristicForService("your-service-uuid", characteristicUUID, (error, characteristic) => {
        if (error) {
            console.error("Error receiving data:", error);
            return;
        }

        if (characteristic?.value) {
            const decodedValue = Buffer.from(characteristic.value, 'base64').toString('utf-8');
            try {
                const parsedData = JSON.parse(decodedValue);
                console.log("Received Data:", parsedData);
                // Send data to server
                sendWorkoutData(parsedData);
                // Update state in the UI
            } catch (err) {
                console.error("Error parsing Bluetooth data:", err);
            }
        }
    });
}

async function sendWorkoutData(data) {
    try {
        await fetch('https://yourserver.com/api/workout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        console.log("Data sent to server successfully.");
    } catch (err) {
        console.error("Failed to send data to server:", err);
    }
}
