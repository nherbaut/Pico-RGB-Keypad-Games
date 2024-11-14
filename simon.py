import time
import picokeypad
import random
import math
import _thread
from picozero import Speaker

speaker = Speaker(8)


def getNote(keypad: int):
    letter = 97+(keypad % 7)
    number = 3+math.floor((keypad/7))
    return chr(letter)+str(number)


def play_sound_for_key(keypad: int, speaker: object):
    speaker.play(getNote(keypad),0.5)

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


def play_intro(speaker):
    print("playing intro")
    speaker.play("g4", 0.05)
    speaker.play("e4", 0.04)
    speaker.play("d4", 0.06)
    speaker.play("c4", 0.05)
    speaker.play("g3", 0.04)
    speaker.play("e4", 0.06)
    speaker.play("b3", 0.05)
    speaker.play("a3", 0.06)
    speaker.play("d4", 0.04)
    speaker.play("c4", 0.05)
    print("done playing intro")


def play(key, repeat=999):
    global loops
    loops[key][1] = repeat


def play_stop():
    global loops
    for key in loops.keys():
        loops[key][1] = 0


def sound_loop(sound_loops, speaker):

    while True:
        for loop_name in sound_loops.keys():
            print("sound loops found")
            if sound_loops[loop_name][1] > 0:
                print(
                    f"its active, let's do it {sound_loops[loop_name][1]} times")
                for i in range(0, sound_loops[loop_name][1]):

                    if sound_loops[loop_name][1] <= 0:
                        break
                    sound_loops[loop_name][0](speaker)
                    sound_loops[loop_name][1] = sound_loops[loop_name][1]-1

            time.sleep(0.1)


loops = {"intro": [play_intro, 0], "win": [play_win, 0]}

_thread.stack_size(4096*2)
new_thread = _thread.start_new_thread(
    sound_loop, ((loops,)), {"speaker": speaker})


keypad = picokeypad.PicoKeypad()
keypad.set_brightness(1.0)

NUM_PADS = keypad.get_num_pads()
sequence = []  # Séquence de couleurs
player_input = []  # Séquence entrée par le joueur
colors = [(0x20, 0x00, 0x00),  # Rouge
          (0x00, 0x20, 0x00),  # Vert
          (0x00, 0x00, 0x20),  # Bleu
          (0x20, 0x20, 0x00)]  # Jaune


def add_random_color():
    """Ajoute une couleur aléatoire à la séquence."""
    sequence.append(random.randint(0, NUM_PADS - 1))


def show_sequence():
    """Affiche la séquence de couleurs pour le joueur."""
    print("[SEQUENCE] Affichage de la séquence : ", sequence)
    for index in sequence:
        color = colors[index % len(colors)]
        keypad.illuminate(index, *color)
        keypad.update()
        play_sound_for_key(index,speaker)
        time.sleep(0.3)
        keypad.illuminate(index, 0, 0, 0)  # Éteint le bouton
        keypad.update()
        time.sleep(0.2)  # Pause entre les couleurs


def defeat_animation():
    """Animation de défaite en rouge."""
    print("[DÉFAITE] Séquence incorrecte.")
    for _ in range(3):  # Clignotement rouge 3 fois
        for i in range(NUM_PADS):
            keypad.illuminate(i, 0x20, 0x00, 0x00)  # Rouge
        keypad.update()
        time.sleep(0.3)
        for i in range(NUM_PADS):
            keypad.illuminate(i, 0, 0, 0)  # Éteint les boutons
        keypad.update()
        time.sleep(0.3)


def victory_animation():
    """Animation de victoire."""
    print("[VICTOIRE] Séquence correctement reproduite !")
    for _ in range(6):  # Durée de 3 secondes environ
        for i in range(NUM_PADS):
            color = colors[(i + _) % len(colors)]
            keypad.illuminate(i, *color)
        keypad.update()
        time.sleep(0.1)
    for i in range(NUM_PADS):
        keypad.illuminate(i, 0, 0, 0)


def check_player_input():
    """Vérifie si le joueur a reproduit la séquence correctement."""
    for i in range(len(player_input)):
        if player_input[i] != sequence[i]:
            return False
    return True


# Initialisation du jeu
add_random_color()

while True:
    # Affiche la séquence actuelle au joueur
    show_sequence()

    # Réinitialise la séquence du joueur
    player_input = []
    input_index = 0
    correct_sequence = True

    # Récupère l'entrée du joueur
    while len(player_input) < len(sequence):
        button_states = keypad.get_button_states()
        for i in range(NUM_PADS):
            if (button_states >> i) & 0x01:
                if len(player_input) == input_index:  # Enregistre un appui unique
                    player_input.append(i)
                    input_index += 1
                    print(
                        f"[ENTRÉE JOUEUR] Bouton {i} appuyé. Séquence du joueur : {player_input}")

                    # Illumine brièvement le bouton pour indiquer l'appui
                    color = colors[i % len(colors)]
                    keypad.illuminate(i, *color)
                    keypad.update()
                    play_sound_for_key(i,speaker)
                    time.sleep(0.3)
                    keypad.illuminate(i, 0, 0, 0)
                    keypad.update()

        # Vérifie la séquence du joueur à chaque appui
        if not check_player_input():
            defeat_animation()
            sequence = []
            add_random_color()  # Redémarre avec une séquence d'un seul élément
            break

        time.sleep(0.1)

    # Si la séquence est correcte et complète
    if player_input == sequence:
        victory_animation()
        add_random_color()  # Ajoute une nouvelle couleur pour le tour suivant
