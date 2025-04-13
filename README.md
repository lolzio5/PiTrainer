# PiTrainer

_Your gym Personal Trainer, in your pocket!_

PiTrainer is a fullstack Internet-of-Things (IoT) embedded system, designed to help beginners in the gym learn how to complete exercises with perfect form.

It comes with an Android and iOS compatible mobile app written in React Native, which displays tons of interesting information about your latest workout and your workout history.

The biggest selling point is tailored feedback on your form for each set, and an idea of the quality of each individual rep, as a score from 0 to 100.

This score is calculated using a custom-trained machine learning model, that we trained to learn what a perfect rep looks like.

The tailored feedback is determined using signal processing methods, to find how the current rep differs from a perfect rep and how to rectify this.

All user data is securely stored on an Amazon Web Services Dynamo database, associated with a unique user account.

## How it works
The entire system is designed as a state machine between 3 main states: idle, doing reps, and resting. These states are user controlled, the mobile app pushes workout starts, set endings and starts, and workout endings to the server, which is polled by the RaspberryPi to synchronise its state. 

This system allows multiple users to use the system at the same time, with multiple mobile apps and RaspberryPis connected, doing independent workouts.

### Signing Up and Logging In
The mobile app contains a signing up feature to create new accounts. When the user enters an email and password, as well as their RaspberryPi ID (so that the server knows to associate a Pi's data with the correct user), the data is pushed to the server, which creates an account in the database, and sends a session cookie. Only with this cookie can the user then access protected routes on the server, to view the user data and start workouts. 

The Log In page checks the provided user data against the database data, and returns a cookie if successful. Otherwise, it provides information about which part is wrong.

### Starting a new workout
When a user wants to start a workout, they need to make sure their RaspberryPi is turned on, so it can start polling the server to find out if a workout associated to its ID has been started. When the user presses the ```Start Workout``` button, the server receives a request to start a workout, for the user associated with the user cookie (generated on login). It can then start the workout, and the Pi will know to start counting reps. These reps are also synced across the server to the mobile app, displaying a live count. 

### Resting between sets
When the user finishes their set, they can end the set, which will trigger analysis of each rep, to be sent to the server, and displayed on the mobile app. The RaspberryPi enters a temporary ```Idle``` mode, where it stops recording reps (but expects to start again soon). The user can then view the set analysis while they rest, and follow the feedback to improve their form in the next set.

### Ending a workout
When a user wants to end their workout, they can click the ```End Workout``` button, which updates the state machine to the ```Idle``` state on the server, and triggers the RaspberryPi to upload the entire workout data to the server, so that the machine learning model can analyse the reps and give an overall workout quality analysis report, which is then stored in the database. This allows the user to navigate through the app and view their workout statistics, which are retrieved by querying the database for the relevant data.



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
