import sys
import os
import platform
from MegaMekTimeline import MegaMekTimeline
from AIembedding import AIembedding

# Define getch() based on the operating system
try:
    # Windows
    import msvcrt

    def getch():
        """Get a single character on Windows."""
        return msvcrt.getch().decode()
except ImportError:
    # Unix/Linux
    import tty
    import termios

    def getch():
        """Get a single character on Unix/Linux."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# Function to clear the terminal screen
def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def wait_for_space_bar():
    print("\nPress the space bar to return to the menu...")
    while True:
        key = getch()
        if key == ' ':
            break

# Create an instance of MegaMekTimeline
timeline = MegaMekTimeline()

# Create AIembedding instance
ai = AIembedding()

# Create a command prompt for the user to select which process to run
def main():
    running = True
    clear_screen()
    while running:
        if ai.enabled:
            print("What would you like to do?\n(1) Combine XML files\n(2) Index Documents\n(3) Exit program\n")
        else:
            print("What would you like to do?\n(1) Combine XML files\n(2) Exit program\n")

        choice = getch().upper()

        if ai.enabled:
            if choice == '1':
                timeline.run()
                wait_for_space_bar()
                clear_screen()
            elif choice == '2':
                ai.run()
                wait_for_space_bar()
                clear_screen()
            elif choice == '3':
                running = False  # Exit the loop to end the program
            else:
                print("\nInvalid choice. Please choose '1', '2', or '3'.")
        else:
            if choice == '1':
                timeline.run()
                wait_for_space_bar()
                clear_screen()
            elif choice == '2':
                running = False  # Exit the loop to end the program
            else:
                print("\nInvalid choice. Please choose '1' or '2'.")


if __name__ == "__main__":
    main()

