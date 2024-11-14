import time
import picokeypad
import _thread
from picozero import Speaker

speaker = Speaker(8)

# Function to play sound
def play(note):
    global loops
    if note in loops:
        loops[note][1] = 999
    else:
        def play_note(speaker): speaker.play(note.lower(), 0.08)
        loops[note] = [play_note, 999]  # Set up for one-time play

def play_stop():
    global loops
    for key in loops.keys():
        loops[key][1] = 0

# Background thread to manage sound playback
def sound_loop(sound_loops, speaker):
    while True:
        for loop_name in sound_loops.keys():
            if sound_loops[loop_name][1] > 0:
                for i in range(0, sound_loops[loop_name][1]):
                    if sound_loops[loop_name][1] <= 0:
                        break
                    sound_loops[loop_name][0](speaker)
                    sound_loops[loop_name][1] -= 1
            time.sleep(0.01)

def play_win(speaker):
    speaker.play("a4", 0.05)
    speaker.play("c5", 0.05)
    speaker.play("e5", 0.05)
    speaker.play("g5", 0.05)
    speaker.play("b5", 0.05)
    speaker.play("d6", 0.05)
    speaker.play("f6", 0.05)
    speaker.play("c7", 0.05)
    speaker.play("e7", 0.05)
    
loops = { "win": [play_win, 0]}
_thread.stack_size(4096*2)
new_thread = _thread.start_new_thread(
    sound_loop, ((loops,)), {"speaker": speaker})

# Keypad and LED setup
keypad = picokeypad.PicoKeypad()
keypad.set_brightness(1.0)
NUM_PADS = keypad.get_num_pads()

# Button colors
colors = [
    (0x20, 0x10, 0x00),  
    (0x00, 0x20, 0x10),  
    (0x10, 0x00, 0x20),  
    (0x20, 0x20, 0x00),  
]

# Note grid on keypad


# Define the note sequence to follow
#note_sequence = ["C4","C4","C4","D4","E4","D4","C4","E4","D4","D4","C4","C4","C4","C4","D4","E4","D4","C4","E4","D4","D4","C4","D4","D4","D4","D4","A3","A3","D4","C4","B3","A3","G3","C4","C4","C4","D4","E4","D4","C4","E4","D4","D4","C4"]
#note_duration = [0.05,0.05,0.05,0.05,0.1,0.1,0.05,0.05,0.05,0.05,0.1,0.05,0.05,0.05,0.05,0.1,0.1,0.05,0.05,0.05,0.05,0.1,0.05,0.05,0.05,0.05,0.1,0.1,0.05,0.05,0.05,0.05,0.1,0.05,0.05,0.05,0.05,0.1,0.1,0.05,0.05,0.05,0.05,0.1]
note_sequence=["G4","C4","C4","C4","D4","D#4","D#4","F4","G4","G4","F4","A#4","A#4","G4","C4","D4","D#4","F4","F4","F4","F4","D4","D#4","F4","D4","C4","A#3","C4","D4","D#4","D#4","D4","A#3","C4","C4","C4"]
note_duration = [0.05] * len(note_sequence)

for i in range(0,min(10,len(note_sequence))):
    play(note_sequence[i])
    time.sleep(note_duration[i]*2)
    play_stop()
    time.sleep(0.1)
    


notes=(sorted(set(note_sequence),key=lambda k:k[1]+str((ord(k[0].lower())-ord("c")+7)%7))*16)[0:16]
notes=[[notes[i+j*4] for i in range(0,4)] for j in range(0,4)]
sequence_index = 0  # Current position in the sequence

# Start and stop sound functions
def start_sound(note):
    print(f"play note {note}")
    play(note)

def stop_sound():
    print(f"stop any sound")
    play_stop()

def illuminate_button(keypad_index, color):
    keypad.illuminate(keypad_index, *color)
    keypad.update()

def find_note_position(note):
    """Finds the keypad index for the given note."""
    for row in range(4):
        for col in range(4):
            if notes[row][col] == note:
                return row * 4 + col
    return None

def play_note_while_pressed(keypad_index):
    """Plays a note while the button is pressed and checks it against the sequence."""
    global sequence_index

    # Get the row, column, note, and color
    row = keypad_index // 4
    col = keypad_index % 4
    note = notes[row][col]
    color = colors[row]

    # Check if the note matches the current sequence note
    if note == note_sequence[sequence_index]:
        print(f"[CORRECT] Played {note}, advancing in sequence.")
        
        # Play the sound and light up the button in its color if correct
        illuminate_button(keypad_index, color)
        start_sound(note)

        # Wait until button is released
        while (keypad.get_button_states() >> keypad_index) & 0x01:
            time.sleep(0.05)

        # Stop sound and turn off the light when the button is released
        stop_sound()
        keypad.illuminate(keypad_index, 0, 0, 0)
        keypad.update()

        # Move to the next note in the sequence
        sequence_index += 1  

        # If the sequence is complete, play the victory animation
        if sequence_index >= len(note_sequence):
            print("[VICTORY] Sequence completed!")
            play("win")  # Play the win sound
            victory_animation()  # Show the animation
            stop_sound()
            sequence_index = 0  # Reset for the next round

        # Illuminate the next note in the sequence in green
        next_note = note_sequence[sequence_index]
        next_index = find_note_position(next_note)
        if next_index is not None:
            illuminate_button(next_index, (0x00, 0x20, 0x00))  # Green for the next note

    else:
        print(f"[INCORRECT] Played {note}. Flashing red.")
        
        # Flash the button red if incorrect and do not reset the sequence
        illuminate_button(keypad_index, (0x20, 0x00, 0x00))  # Red for incorrect
        time.sleep(0.2)
        keypad.illuminate(keypad_index, 0, 0, 0)  # Turn off after flashing
        keypad.update()

def victory_animation():
    """Displays a victory animation by cycling colors on the keypad."""
    print("[ANIMATION] Displaying victory animation!")
    colors_cycle = [(0x20, 0x00, 0x00), (0x00, 0x20, 0x00), (0x00, 0x00, 0x20), (0x20, 0x20, 0x00)]
    
    for cycle in range(8):  # Run the animation for 8 cycles
        for i in range(NUM_PADS):
            color = colors_cycle[(i + cycle) % len(colors_cycle)]
            keypad.illuminate(i, *color)
        keypad.update()
        time.sleep(0.1)
    
    # Turn off all LEDs after the animation
    for i in range(NUM_PADS):
        keypad.illuminate(i, 0, 0, 0)
    keypad.update()


next_note = note_sequence[sequence_index]
next_index = find_note_position(next_note)
if next_index is not None:
        illuminate_button(next_index, (0x00, 0x20, 0x00))  # Green for the next note
            
# Main loop for the game
while True:
    # Check button states
    button_states = keypad.get_button_states()
    for i in range(NUM_PADS):
        if (button_states >> i) & 0x01:  # If the button is pressed
            play_note_while_pressed(i)  # Play the note and handle sequence checking

    time.sleep(0.1)
