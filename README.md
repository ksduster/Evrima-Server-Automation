# Evrima-Server-Automation
## Automatically Manage Global Chat
> [!NOTE]
> Tested with Python 3.12.5
> You can get Python from https://www.python.org/
> Requires mcrcon `pip install mcrcon`

## What does this do?   
This script will check your The Isle - Evrima server for the number of players connected.
If the selected high value threshold is met, it will disable Global Chat using RCON commands.
Once the low threshold is met, it will re-enable the chat.

## What is the purpose?
With public servers, the more people you get in the server the more toxic or distracting the chat can be that takes away from the gameplay. 
This script will help prevent that when the population reaches the disablechatat threshold. 
Global chat will be re-enabled when it gets below the enable chat threshold.

## Configuration:
RCON Connection Settings
```
HOST = "enter_ip_address"  # Replace with your IP address
PORT = 7772  # Change this to your RCON port
PASSWORD = "rcon_password_here"  # Replace with your RCON password  Remember RCON is in plaintext
timeout = 5  # Connection timeout in seconds

 Enable/Disable Global chat values
disablechatat = 50 # Default 50 - If 51 or more players are in the game when checked - disable global chat
enablechatat = 30 # Default 30 - If 30 players or less are in the game when checked - Re-enable global chat
howoften = 300 # Default 5 minutes/300 seconds - Check this often for the number of players in the game and perform action if needed

 Announcement messages
disable_announcement = "Global chat has been disabled. Enjoy your gaming!"
enable_announcement = "Global chat has been re-enabled. Be Kind, Rewind!"
```
### Running the script
In windows, just double click the script and the console will show. Errors will show in the log file located in the same directory.
