import time
import logging
import socket
import struct

# Setup logging
logging.basicConfig(
    filename="global_chat_monitor.log",  # Log file name
    filemode="a",  # Append mode
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO  # Log everything from DEBUG level and above
)

# RCON Connection Settings
HOST = "IP_ADDRESS"  # Replace with your IP address
PORT = PORT  # Change this to your RCON port
PASSWORD = "password"  # Replace with your RCON password  Remember RCON is in plaintext
TIMEOUT = 5  # Connection timeout in seconds

# Enable/Disable Global chat values
disablechatat = 50 # Default 50 - If 51 or more players are in the game when checked - disable global chat
enablechatat = 30 # Default 30 - If 30 players or less are in the game when checked - Re-enable global chat
howoften = 300 # Default 5 minutes/300 seconds - Check this often for the number of players in the game and perform action if needed

# Announcement messages
disable_announcement = "Global chat has been disabled. Enjoy your gaming!"
enable_announcement = "Global chat has been re-enabled. Be Kind, Rewind!"

# ----- DO NOT CHANGE ANYTHING BELOW THIS LINE ----- #
# Function to authenticate with RCON and send a command
def auth_rcon_command(command_bytes):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((HOST, PORT))
            
            # Send authentication packet
            auth_packet = b"\x01" + PASSWORD.encode() + b"\x00\x00"
            s.send(auth_packet)
            auth_response = s.recv(1024)

            # Validate authentication response
            if len(auth_response) < 12:
                logging.error("Failed to authenticate with RCON. Check the password.")
                return None

            s.send(command_bytes)
            message = s.recv(1024)
            return message.decode()
    except Exception as e:
        logging.error(f"Error sending RCON command: {e}")
        return None

# Function to get the player count
def get_player_count():
    try:
        logging.debug("Attempting to get player list...")
        LIST = bytes('\x02', 'utf-8') + bytes('\x40', 'utf-8') + bytes('\x00', 'utf-8')
        response = auth_rcon_command(LIST)

        if response:
            logging.debug(f"Server response: {response}")
            print("Raw response:", response)

            # Split the response into lines
            response_lines = response.splitlines()
            # The second line contains the Steam IDs
            if len(response_lines) > 1:
                steam_ids_line = response_lines[1]  # The line with Steam IDs
                # Split the Steam IDs
                steam_ids = steam_ids_line.split(",")
                # Filter out empty strings and count valid Steam IDs (length of 17 characters)
                valid_steam_ids = [s for s in steam_ids if s.strip() and len(s.strip()) == 17]

                player_count = len(valid_steam_ids)
                logging.info(f"Current player count: {player_count}")
                return player_count
            else:
                logging.warning("Unexpected response format.")
                return 0
        else:
            logging.warning("No response or empty response from player list command.")
            return 0
    except Exception as e:
        logging.error(f"Error while getting player list: {e}")
        return 0

# Define a global variable to store the chat status
global_chat_status = None  

# Function to get server details and check global chat status
def get_server_details():
    global global_chat_status  # Use the global variable

    try:
        logging.debug("Attempting to get server details...")
        details_command = bytes('\x02', 'utf-8') + bytes('\x12', 'utf-8') + bytes('\x00', 'utf-8')
        response = auth_rcon_command(details_command)

        if response:
            logging.debug(f"Server response: {response}")
            print("Raw response:", response)  # Debugging output

            # Check for bEnableGlobalChat in the response
            if "bEnableGlobalChat" in response:
                # Split response into key-value pairs
                for item in response.split(","):  
                    if "bEnableGlobalChat" in item:
                        key, value = item.split(":")  # Ensure splitting by `:` works
                        value = value.strip().lower()  # Normalize the value

                        # Convert to boolean and store in the global variable
                        global_chat_status = value == 'true'
                        logging.info(f"Global chat status retrieved: {global_chat_status}")
                        return global_chat_status

            logging.warning("bEnableGlobalChat not found in server details response.")
        else:
            logging.warning("No response or empty response from server details command.")

    except Exception as e:
        logging.error(f"Error while getting server details: {e}")

    # If something went wrong, return None
    return None



# Function to toggle global chat
def toggle_global_chat(action):
    command_id = b'\x84'  # RCON_TOGGLEGLOBALCHAT
    action_str = "Enable" if action else "Disable"

    # Create the command as bytes
    command = bytes('\x02', 'utf-8') + command_id + bytes(action_str, 'utf-8') + bytes('\x00', 'utf-8')

    try:
        logging.debug(f"Attempting to toggle global chat to: {action_str}")
        
        # Send command
        response = auth_rcon_command(command)

        if response:
            print("Toggled global chat:", action_str)
            logging.info(f"Toggled global chat: {action_str}")
            logging.debug(f"Server response: {response}")
        else:
            logging.warning("No response from toggle global chat command.")
    except Exception as e:
        logging.error(f"Error while toggling global chat: {e}")

# RCON Command to send an announcement (RCON_ANNOUNCE = 0x10)
def send_rcon_announcement(message):
    command_id = b'\x10'  # RCON_ANNOUNCE
    # Create the command as bytes
    command = bytes('\x02', 'utf-8') + command_id + bytes(message + '\x00', 'utf-8')

    try:
        logging.debug(f"Attempting to send RCON announcement: {message}")
        
        # Send command
        response = auth_rcon_command(command)

        if response:
            print(f"Announcement sent: {message}")
            logging.info(f"RCON Announcement sent: {message}")
            logging.debug(f"Server response: {response}")
        else:
            logging.warning("No response from RCON announcement command.")
    except Exception as e:
        logging.error(f"Error while sending RCON announcement: {e}")



# Main loop to check player count and toggle chat
def monitor_chat():
    global global_chat_status  # Use the global variable to track the state

    while True:
        try:
            logging.info("Checking player count...")
            player_count = get_player_count()
            logging.info(f"Current player count: {player_count}")

            # Always get the current global chat status
            current_global_chat_status = get_server_details()

            if current_global_chat_status is None:
                logging.error("Failed to retrieve global chat status. Skipping this cycle.")
                time.sleep(howoften)  # Use the adjustable value for sleep time
                continue  # Skip to the next iteration if we can't get the status

            # Check if global chat is enabled and player count exceeds disablechatat
            if current_global_chat_status and player_count >= disablechatat:
                logging.info("Conditions met to disable global chat.")
                toggle_global_chat(False)  # Disable global chat
                global_chat_status = False  # Update the state to disabled
                logging.info("Global chat disabled due to players connected.")
                send_rcon_announcement(disable_announcement)  # Send announcement for disabling global chat

            # Check if global chat is disabled and player count is less than or equal to enablechatat
            elif not current_global_chat_status and player_count <= enablechatat:
                logging.info("Conditions met to enable global chat.")
                toggle_global_chat(True)  # Enable global chat
                global_chat_status = True  # Update the state to enabled
                logging.info("Global chat enabled due to low player count.")
                send_rcon_announcement(enable_announcement)  # Send announcement for enabling global chat

            else:
                logging.info("No changes needed this cycle.")

        except Exception as e:
            logging.error(f"An error occurred in the main loop: {e}")

        # Wait for the specified interval before checking again
        time.sleep(howoften)

# Start the monitoring process
logging.info("Starting global chat monitor bot...")
print("Starting global chat monitor bot...")  # Print when script starts
monitor_chat()
