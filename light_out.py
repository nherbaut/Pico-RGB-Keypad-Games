import time
import picokeypad
import random
import _thread

from picozero import Speaker

speaker = Speaker(8)


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


def play(key, repeat):
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


loops = {"intro": [play_intro, 2], "win": [play_win, 0]}

_thread.stack_size(4096*2)
new_thread = _thread.start_new_thread(
    sound_loop, ((loops,)), {"speaker": speaker})


keypad = picokeypad.PicoKeypad()
keypad.set_brightness(1.0)

NUM_PADS = keypad.get_num_pads()
# Pour une disposition en grille, par exemple 4x4 pour 16 boutons
GRID_SIZE = int(NUM_PADS**0.5)
initial_difficulty = 1  # Démarre avec une difficulté de 1 coup

# Initialisation de l'état des boutons
button_states = [False] * NUM_PADS  # False = éteint, True = allumé
previous_button_states = 0  # Suivi des états précédents des boutons
current_difficulty = initial_difficulty



def toggle_button(index):
    """Change l'état du bouton spécifié et de ses voisins (haut, bas, gauche, droite)."""
    if index < 0 or index >= NUM_PADS:
        return  # Indice hors limites

    # Change l'état du bouton lui-même
    button_states[index] = not button_states[index]

    # Détermine les voisins
    neighbors = []
    if index % GRID_SIZE > 0:  # Bouton de gauche
        neighbors.append(index - 1)
    if index % GRID_SIZE < GRID_SIZE - 1:  # Bouton de droite
        neighbors.append(index + 1)
    if index >= GRID_SIZE:  # Bouton du haut
        neighbors.append(index - GRID_SIZE)
    if index < NUM_PADS - GRID_SIZE:  # Bouton du bas
        neighbors.append(index + GRID_SIZE)

    # Change l'état des voisins
    for neighbor in neighbors:
        button_states[neighbor] = not button_states[neighbor]
    print(
        f"[ACTION] Bouton {index} appuyé. Nouvel état des boutons : {button_states}")


def initialize_solvable_game():
    """Initialise une configuration de boutons solvable en appliquant `current_difficulty` transformations."""
    global button_states
    # Commence avec tous les boutons éteints
    button_states = [False] * NUM_PADS

    # Applique `current_difficulty` appuis aléatoires pour générer une configuration solvable
    for _ in range(current_difficulty):
        random_index = random.randint(0, NUM_PADS - 1)
        # Change l'état du bouton et de ses voisins
        toggle_button(random_index)

    print(f"[DÉMARRAGE] Puzzle généré en {current_difficulty} coups.")

    # Éteint tous les boutons pour la seconde phase du clignotement
    for i in range(NUM_PADS):
        keypad.illuminate(i, 0x00, 0x00, 0x00)


def check_victory():
    """Vérifie si tous les boutons sont éteints."""
    return all(not state for state in button_states)


def special_animation():
    """Animation spéciale pour célébrer la victoire (durée de 3 secondes)."""
    global speaker, loops
    print("[VICTOIRE] Début de l'animation spéciale pour célébrer la victoire !")
    play("win",99)
    colors = [(0x20, 0x00, 0x10), (0x10, 0x20, 0x00), (0x00, 0x10, 0x20), (0x20, 0x20, 0x00),
              (0x10, 0x00, 0x20), (0x00, 0x20, 0x10), (0x20, 0x00, 0x20), (0x00, 0x20, 0x20)]
    for _ in range(15):  # Animation pendant 3 secondes
        for i in range(NUM_PADS):
            color = colors[(i + _) % len(colors)]
            keypad.illuminate(i, *color)
        keypad.update()
        time.sleep(0.1)
    play_stop()
    print("[VICTOIRE] Fin de l'animation spéciale")


# Initialise le jeu avec une configuration solvable
initialize_solvable_game()

while True:
    button_states_snapshot = keypad.get_button_states()

    # Vérifie les interactions de l'utilisateur avec les boutons
    for i in range(NUM_PADS):
        # Détecte un appui unique (changement d'état de non-appuyé à appuyé)
        if (button_states_snapshot >> i) & 0x01 and not (previous_button_states >> i) & 0x01:
            toggle_button(i)  # Change l'état du bouton et de ses voisins
            speaker.play("a4", 0.05)
            speaker.play("c5", 0.05)

    # Met à jour les états précédents pour la prochaine boucle
    previous_button_states = button_states_snapshot

    # Vérifie la condition de victoire
    if check_victory():
        special_animation()
        current_difficulty += 1  # Augmente la difficulté pour la prochaine partie
        initialize_solvable_game()  # Réinitialise le jeu avec une difficulté accrue

    # Affiche l'état des boutons
    for i in range(NUM_PADS):
        if button_states[i]:
            keypad.illuminate(i, 0x00, 0x00, 0x20)  # Boutons allumés en bleu
        else:
            # Boutons éteints en blanc faible
            keypad.illuminate(i, 0x05, 0x05, 0x05)

    keypad.update()
    time.sleep(0.1)

