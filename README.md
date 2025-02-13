# PiTrainer

_Your gym Personal Trainer, in your pocket!_

PiTrainer is a fullstack Internet-of-Things (IoT) embedded system, designed to help beginners in the gym learn how to complete exercises with perfect form.

It comes with an Android and iOS compatible mobile app written in React Native, which displays tons of interesting information about your latest workout and your workout history.

The biggest selling point is tailored feedback on your form for each set, and an idea of the quality of each individual rep, as a score from 0 to 100.

This is calculated using a custom-trained machine learning model, that we trained to learn what a perfect rep looks like.

All user data is securely stored on an Amazon Web Services database, associated with a unique user account.

## Usage Guide

### Mobile App

Run the frontend app using `npm run android -- --tunnel` or `npm run iOS -- --tunnel` depending on which OS your user's phone runs. This will host the Expo app on your computer, which you can load on your phone using the Expo Go app. Just scan the QR code and it will automatically render on your phone!

The mobile app is entirely built in React Native, and handles login connections and rendering all the data.

To start a new workout, head to the workout page, and all the logic is directly handled by the app, connected to the server.

The files for the app are found in the
>app
folder.

### Server

The backend is hosted on an AWS EC2 instance with IP address `3.10.117.27`. The backend authentifies users when logging in, allows for user account creation, reads and writes to the Dynamo database, handles all control logic, and runs the machine learning model to find the quality of each rep. It also receives all data sent from the Raspberry Pi, connected to the sensors.

This is implemented as a Python Flask server, which communicates using HTTP to the app and the Pi. Files found in
> backend
folder.

### User Device

SSH into the Raspberry Pi and upload all the Python scripts found in the
>pi
folder. Reboot the Pi, and get it to connect to your mobile hotspot or home Wifi. It will then automatically connect to the server.

Raspberry Pi Zero that sends data via HTTP to the server, sending data through which is then stored on the server. Uses $I^2C$ to connect to a magnetometer and accelerometer to collect data about the current exercise.
