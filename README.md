# File-backing-drive
## About
A Python program for file backing, implementing both client and server side, on Linux and on Windows.
Based on TCP connection, protocols and sockets.
This project was a part of a Communication Networks course I took during the second year of my bachelor degree.

## Server
- Always on, waiting for clients. 
- Can handle several clients at a time.
- Supports multiple devices of the same client.

## Client
- Monitors it's folder (using Python's watchdog library) and informs the server about any change.
- Gets updated from the server everytime he connects, or if he doesn't, every few seconds.

## Contributors
- Coral Kuta
- Noa Eitan
