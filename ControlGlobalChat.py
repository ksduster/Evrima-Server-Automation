import time
from mcrcon import MCRcon

# RCON Connection Settings
HOST = "your_server_ip"
PORT = 12345  # Change this to your RCON port
PASSWORD = "your_rcon_password"

# Function to get player count
def get_player_count():
    with MCRcon(HOST, PASSWORD, port=PORT) as mcr:
        response = mcr.command("Get Player List")
        # Parse the player list response (assuming it's a comma-separated string)
        players = response.split(",")
        return len(players)  # Returns the number of players

# Function to toggle global chat
def toggle_global_chat(turn_on):
    command = "Toggle global chat"
    with MCRcon(HOST, PASSWORD, port=PORT) as mcr:
        mcr.command(command)
        print(f"Global chat {'ENABLED' if turn_on else 'DISABLED'}")

# Main loop to check player count and toggle chat
def monitor_chat():
    while True:
        player_count = get_player_count()
        print(f"Current player count: {player_count}")

        if player_count < 30:
            toggle_global_chat(True)  # Enable global chat
        else:
            toggle_global_chat(False)  # Disable global chat

        # Wait for 5 minutes (300 seconds)
        time.sleep(300)

# Start the monitoring process
monitor_chat()
