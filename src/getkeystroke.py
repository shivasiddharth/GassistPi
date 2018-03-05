
import pyxhook
import time

# This function is called every time a key is presssed
def kbevent(event):
    global running
    # print key info

    print('Ascii value: {}'.format(event.Ascii))


# Create hookmanager
hookman = pyxhook.HookManager()
# Define our callback to fire when a key is pressed down
hookman.KeyDown = kbevent
# Hook the keyboard
hookman.HookKeyboard()
# Start our listener
hookman.start()

# Create a loop to keep the application running
running = True
print('Now press the button you want')
while running:
    time.sleep(0.1)

# Close the listener when we are done
hookman.cancel()