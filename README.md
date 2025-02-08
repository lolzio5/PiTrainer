# PiTrainer (name is work in progress)

_Your gym Personal Trainer, in your pocket!_

## Frontend

Build the frontend app using `npm run android -- --tunnel` on Firebase. This will host the Expo app, that you can then retrieve using the Expo Go app on your phone. Scan the QR code and it will automatically render on your phone!

**--> TO DO**

- Test control logic

## Backend

The backend is hosted on an AWS EC2 instance with IP address: '....'. The frontend automatically stores and retrieves information from the backend. Implemented as a Python Flask server, to communicate in HTTP as per the mark scheme with the app. Files found in
> backend

folder.

**--> TO DO**

- Train machine learning model for seated cable rows
- Test all control logic API routes
- Implement final processing route

## User Device

Raspberry Pi Zero that connects via Bluetooth to the app, sending data through which is then stored on the server. Uses $I^2C$ to connect to a magnetometer and accelerometer to collect data about the current exercise. Files found in
> pi

folder.

**--> TO DO**

- Test rep counting
- Package and send data correctly
