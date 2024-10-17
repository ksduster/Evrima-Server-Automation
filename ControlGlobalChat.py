import tkinter as tk
from tkinter import messagebox
import time
import logging
import socket
import threading

# Setup logging
logging.basicConfig(
    filename="global_chat_monitor.log",  # Log file name
    filemode="a",  # Append mode
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG  # Log everything from DEBUG level and above
)
# Global Variable to control the bot's running state
bot_running = False

# Function to start the bot with user inputs
def start_bot():
    # Get values from user inputs
    global HOST, PORT, PASSWORD, disablechatat, enablechatat, howoften, disable_announcement, enable_announcement, timeout, greeting, greeting_timer, bot_running

    HOST = host_entry.get()
    PORT = int(port_entry.get())
    PASSWORD = password_entry.get()
    disablechatat = int(disablechatat_entry.get())
    enablechatat = int(enablechatat_entry.get())
    howoften = int(howoften_entry.get())
    timeout = int(timeout_entry.get())
    disable_announcement = disableannouncement_entry.get()
    enable_announcement = enableannouncement_entry.get()
    greeting = greeting_entry.get()
    greeting_timer = int(greeting_timer_entry.get())
   
    # Start the monitoring process in a new thread
    bot_running = True  # Set flag to indicate the bot is running
    update_status("Running")  # Update status label to Running
    start_button.config(state=tk.DISABLED)  # Disable start button while running
    stop_button.config(state=tk.NORMAL)  # Enable stop button when bot is running
    threading.Thread(target=monitor_chat_thread).start()


# Function to send an RCON command via socket
def send_rcon_command(command_bytes):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((HOST, PORT))
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
        response = send_rcon_command(LIST)

        if response:
            logging.debug(f"Server response: {response}")
            print("Raw response:", response)

            # Split the response into lines
            response_lines = response.splitlines()

            if len(response_lines) > 1:
                # The second line should contain comma-separated Steam64 IDs
                steam_ids_line = response_lines[1].strip()  # Ensure no extra spaces
                steam_ids = steam_ids_line.split(",")

                # Filter out empty and invalid Steam IDs
                valid_steam_ids = [s.strip() for s in steam_ids if s.strip() and len(s.strip()) == 17]

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

# Function to toggle global chat
def toggle_global_chat(action):
    command_id = b'\x84'  # RCON_TOGGLEGLOBALCHAT
    action_str = "Enable" if action else "Disable"

    command = bytes('\x02', 'utf-8') + command_id + bytes(action_str, 'utf-8') + bytes(PASSWORD, 'utf-8') + bytes('\x00', 'utf-8')

    try:
        logging.debug(f"Attempting to toggle global chat to: {action_str}")
        
        response = send_rcon_command(command)

        if response:
            print("Toggled global chat:", action_str)
            logging.info(f"Toggled global chat: {action_str}")
            logging.debug(f"Server response: {response}")
        else:
            logging.warning("No response from toggle global chat command.")
    except Exception as e:
        logging.error(f"Error while toggling global chat: {e}")

# Function to send announcements
def send_rcon_announcement(message):
    command_id = b'\x10'  # RCON_ANNOUNCE
    command = bytes('\x02', 'utf-8') + command_id + bytes(message + '\x00', 'utf-8') + bytes(PASSWORD + '\x00', 'utf-8')

    try:
        logging.debug(f"Attempting to send RCON announcement: {message}")
        
        response = send_rcon_command(command)

        if response:
            print(f"Announcement sent: {message}")
            logging.info(f"RCON Announcement sent: {message}")
            logging.debug(f"Server response: {response}")
        else:
            logging.warning("No response from RCON announcement command.")
    except Exception as e:
        logging.error(f"Error while sending RCON announcement: {e}")

# Function to get server details and check global chat status
def get_server_details():
    try:
        logging.debug("Attempting to get server details...")
        details_command = bytes('\x02', 'utf-8') + bytes('\x12', 'utf-8') + bytes('\x00', 'utf-8')
        response = send_rcon_command(details_command)

        if response:
            logging.debug(f"Server response: {response}")
            print("Raw response:", response)

            # Check for bEnableGlobalChat in the response
            if "bEnableGlobalChat" in response:
                # Extract the value
                lines = response.split(",")  # Use comma as the delimiter since it's a single line
                for line in lines:
                    if "bEnableGlobalChat" in line:
                        # Assuming the line is in the format: bEnableGlobalChat:<value>
                        parts = line.split(':')  # Split by colon
                        if len(parts) > 1:
                            # Check if the value is 'true' (case insensitive)
                            global_chat_status = parts[1].strip().lower() == 'true'  # Check if it's true, convert to lower case for comparison
                            logging.info(f"Global chat status retrieved: {global_chat_status}")
                            return global_chat_status
            else:
                logging.warning("bEnableGlobalChat not found in server details response.")
                return None
        else:
            logging.warning("No response or empty response from server details command.")
            return None
    except Exception as e:
        logging.error(f"Error while getting server details: {e}")
        return None

# Global variable to track the global chat state
global_chat_enabled = True

# Log the initial state of global chat
if global_chat_enabled is not None:
    logging.info(f"Global chat is {'enabled' if global_chat_enabled else 'disabled'}.")
else:
    logging.error("Failed to retrieve global chat status.")


# Main loop to check player count and toggle chat
def monitor_chat():
    global global_chat_enabled

    while bot_running:
        try:
            logging.info("Checking player count...")
            player_count = get_player_count()
            logging.debug(f"Current player count: {player_count}")

            current_global_chat_status = get_server_details()
            
            if current_global_chat_status is None:
                logging.error("Failed to retrieve global chat status. Skipping this cycle.")
                time.sleep(30)  # Use the adjustable value for sleep time
                continue  # Skip to the next iteration if we can't get the status

            if current_global_chat_status and player_count <= disablechatat:
                if global_chat_enabled:
                    logging.info("Conditions met to disable global chat.")
                    toggle_global_chat(False)
                    global_chat_enabled = False
                    logging.info("Global chat disabled due to players connected.")
                    send_rcon_announcement(disable_announcement)
                else:
                    logging.info("Global chat is already disabled, no action taken.")

            elif not current_global_chat_status and player_count > enablechatat:
                if not global_chat_enabled:
                    logging.info("Conditions met to enable global chat.")
                    toggle_global_chat(True)
                    global_chat_enabled = True
                    logging.info("Global chat enabled due to low player count.")
                    send_rcon_announcement(enable_announcement)
                else:
                    logging.info("Global chat is already enabled, no action taken.")

        except Exception as e:
            logging.error(f"An error occurred in the main loop: {e}")

        time.sleep(howoften)

def greeting_announcement():
    global greeting
    
    while bot_running:
        try:
            logging.info("Sending greeting announcement")
            send_rcon_announcement(greeting)
        except Exception as e:
            logging.error(f"Error sending greeting announcement: {e}")
        time.sleep(greeting_timer)  # Add proper indentation
            
# moved start_bot from here

# A threaded version of the monitor_chat function
def monitor_chat_thread():
    monitor_chat()  # Run the main monitoring loop in this thread
    update_status("Stopped")  # Update status label when bot stops
    start_button.config(state=tk.NORMAL)  # Re-enable Start button when stopped
    stop_button.config(state=tk.DISABLED)  # Disable stop button when bot is stopped

# Function to stop the bot
def stop_bot():
    global bot_running
    if bot_running:
        bot_running = False  # Set flag to stop the bot
        logging.info("Stopping global chat monitor bot...")
        update_status("Stopping...")  # Temporarily show Stopping status
        stop_button.config(state=tk.DISABLED)  # Disable stop button while stopping

# Function to update the status label
def update_status(status):
    status_label.config(text=f"Bot Status: {status}")

# Default values
default_host = "127.0.0.1"
default_port = "12345"
default_password = "rcon_password"
default_disablechatat = "50"
default_enablechatat = "30"
default_howoften = "300"
default_timeout = "5"
default_disable_announcement = "Global chat has been disabled. Enjoy your gaming!"
default_enable_announcement = "Global chat has been re-enabled. Be Kind, Rewind!"
default_greeting = "Welcome to our server! Chat disables at a population of 50. Have fun!"
default_greeting_timer = "1800"

# Create a basic UI
root = tk.Tk()
root.title("Global Chat Monitor Bot Settings")

# Create and place labels and entry fields with default values
tk.Label(root, text="RCON IP Address").grid(row=0, column=0)
host_entry = tk.Entry(root)
host_entry.insert(0, default_host)  # Set default value
host_entry.grid(row=0, column=1)

tk.Label(root, text="RCON Port").grid(row=1, column=0)
port_entry = tk.Entry(root)
port_entry.insert(0, default_port)  # Set default value
port_entry.grid(row=1, column=1)

tk.Label(root, text="RCON Password").grid(row=2, column=0)
password_entry = tk.Entry(root, show="*")
password_entry.insert(0, default_password)  # Set default value
password_entry.grid(row=2, column=1)

tk.Label(root, text="Disable Chat At (Players)").grid(row=3, column=0)
disablechatat_entry = tk.Entry(root)
disablechatat_entry.insert(0, default_disablechatat)  # Set default value
disablechatat_entry.grid(row=3, column=1)

tk.Label(root, text="Enable Chat At (Players)").grid(row=4, column=0)
enablechatat_entry = tk.Entry(root)
enablechatat_entry.insert(0, default_enablechatat)  # Set default value
enablechatat_entry.grid(row=4, column=1)

tk.Label(root, text="Check Interval (Seconds)").grid(row=5, column=0)
howoften_entry = tk.Entry(root)
howoften_entry.insert(0, default_howoften)  # Set default value
howoften_entry.grid(row=5, column=1)

tk.Label(root, text="RCON Timeout (Seconds)").grid(row=6, column=0)
timeout_entry = tk.Entry(root)
timeout_entry.insert(0, default_timeout)  # Set default value
timeout_entry.grid(row=6, column=1)

tk.Label(root, text="Disable Global Chat Message").grid(row=7, column=0)
disableannouncement_entry = tk.Entry(root)
disableannouncement_entry.insert(0, default_disable_announcement)  # Set default value
disableannouncement_entry.grid(row=7, column=1)

tk.Label(root, text="Enable Global Chat Message").grid(row=8, column=0)
enableannouncement_entry = tk.Entry(root)
enableannouncement_entry.insert(0, default_enable_announcement)  # Set default value
enableannouncement_entry.grid(row=8, column=1)

tk.Label(root, text="Greeting Announcement").grid(row=8, column=0)
greeting_entry = tk.Entry(root)
greeting_entry.insert(0, default_greeting)  # Set default value
greeting_entry.grid(row=9, column=1)
 
tk.Label(root, text="Greeting Timer(in seconds)").grid(row=9, column=0)
greeting_timer_entry = tk.Entry(root)
greeting_timer_entry.insert(0, default_greeting_timer)  # Set default value
greeting_timer_entry.grid(row=10, column=1)

# Status label
status_label = tk.Label(root, text="Bot Status: Stopped", fg="red")
status_label.grid(row=11, column=0, columnspan=2)

# Create and place start and stop buttons
start_button = tk.Button(root, text="Start Bot", command=start_bot)
start_button.grid(row=12, column=0)

stop_button = tk.Button(root, text="Stop Bot", command=stop_bot, state=tk.DISABLED)
stop_button.grid(row=12, column=1)

# Start the main Tkinter loop
root.mainloop()
