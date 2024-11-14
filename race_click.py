import time
import picokeypad
import random

# Initialisation du pavé
keypad = picokeypad.PicoKeypad()
keypad.set_brightness(1.0)

NUM_PADS = keypad.get_num_pads()
MAX_BUTTONS_LIT = 7      # Nombre maximum de boutons bleus allumés simultanément
MAX_YELLOW_BUTTONS = 2   # Nombre maximum de boutons jaunes simultanés
MIN_TIME = 1.5           # Temps minimum pour appuyer sur un bouton
INITIAL_TIME = 3.0       # Temps initial pour appuyer sur un bouton
VICTORY_THRESHOLD = 50   # Nombre de boutons bleus éteints pour la victoire

# État du jeu
button_states = [False] * NUM_PADS  # False = éteint, True = allumé
yellow_buttons = set()              # Ensemble d'indices pour les boutons jaunes
buttons_to_light = 1                # Nombre initial de boutons bleus allumés
time_limit = INITIAL_TIME           # Temps initial pour éteindre chaque bouton
buttons_pressed_count = 0           # Nombre de boutons éteints par le joueur

def generate_unique_indices(count, exclude=set()):
    """Génère un ensemble d'indices aléatoires uniques, en excluant certains indices."""
    indices = set()
    while len(indices) < count:
        index = random.randint(0, NUM_PADS - 1)
        if index not in exclude:  # Exclut certains indices (évite les doublons bleus/jaunes)
            indices.add(index)
    return list(indices)

def illuminate_buttons_simultaneously(blue_indices, yellow_indices, duration):
    """Allume plusieurs boutons bleus et jaunes simultanément de façon progressive."""
    steps = 10  # Nombre d'étapes pour l'effet progressif
    for step in range(steps):
        button_states_snapshot = keypad.get_button_states()

        # Parcours chaque bouton bleu et jaune pour ajuster sa luminosité
        for index in blue_indices:
            if (button_states_snapshot >> index) & 0x01:  # Si bouton bleu appuyé
                keypad.illuminate(index, 0, 0, 0)  # Éteint immédiatement le bouton bleu
                button_states[index] = False       # Met à jour l'état du bouton
                print(f"[ACTION] Bouton {index} bleu appuyé et éteint par le joueur.")
                global buttons_pressed_count
                buttons_pressed_count += 1
            elif button_states[index]:  # Si le bouton est toujours allumé
                brightness = int((step / steps) * 0x20)
                keypad.illuminate(index, 0, 0, brightness)  # Lumière bleue progressive

        for index in yellow_indices:
            if (button_states_snapshot >> index) & 0x01:  # Si bouton jaune appuyé, défaite
                print(f"[DÉFAITE] Bouton {index} jaune appuyé. Fin du jeu.")
                return False
            elif button_states[index]:  # Si le bouton est toujours allumé en jaune
                brightness = int((step / steps) * 0x20)
                keypad.illuminate(index, brightness, brightness, 0)  # Lumière jaune progressive

        keypad.update()
        time.sleep(duration / steps)

    # Éteint les boutons jaunes si tous les boutons bleus sont éteints
    if all(not button_states[index] for index in blue_indices):
        for index in yellow_indices:
            keypad.illuminate(index, 0, 0, 0)
            button_states[index] = False
        keypad.update()

    # Vérifie si un bouton bleu atteint sa pleine luminosité sans appui
    for index in blue_indices:
        if button_states[index]:  # Le bouton n'a pas été appuyé, défaite
            keypad.illuminate(index, 0x20, 0x00, 0x00)  # Rouge pour signaler la défaite
            keypad.update()
            print(f"[DÉFAITE] Le bouton {index} est resté allumé. Fin du jeu.")
            return False  # Indique la défaite
    return True

def start_new_round():
    """Démarre un nouveau tour en allumant un ensemble de boutons bleus et jaunes simultanément."""
    global button_states, yellow_buttons

    # Génère des indices uniques pour les boutons bleus
    blue_buttons_indices = generate_unique_indices(buttons_to_light)

    # Génère des indices uniques pour les boutons jaunes, en évitant les boutons bleus
    yellow_buttons = set(generate_unique_indices(MAX_YELLOW_BUTTONS, exclude=set(blue_buttons_indices)))
    
    # Marque les boutons bleus et jaunes comme allumés dans `button_states`
    for index in blue_buttons_indices:
        button_states[index] = True
    for index in yellow_buttons:
        button_states[index] = True

    # Allume les boutons simultanément et gère l'extinction progressive
    success = illuminate_buttons_simultaneously(blue_buttons_indices, yellow_buttons, time_limit)
    
    # Réinitialise l'état des boutons pour le prochain tour
    for index in blue_buttons_indices + list(yellow_buttons):
        button_states[index] = False

    return success

def update_difficulty():
    """Augmente la difficulté en fonction du nombre de boutons éteints par le joueur."""
    global buttons_to_light, time_limit

    # Augmente le nombre de boutons bleus allumés jusqu'à un maximum de 7
    buttons_to_light = min(MAX_BUTTONS_LIT, 1 + buttons_pressed_count // 3)

    # Diminue le temps limite jusqu'à un minimum de 1.5 secondes
    time_limit = max(MIN_TIME, INITIAL_TIME - (buttons_pressed_count * 0.01))
    print(f"[DIFFICULTÉ] Boutons simultanés : {buttons_to_light}, Temps limite : {time_limit:.2f} secondes")

def victory_animation():
    """Affiche une animation de victoire."""
    print("[VICTOIRE] Félicitations ! Vous avez éteint 50 boutons.")
    colors = [(0x20, 0x00, 0x00), (0x00, 0x20, 0x00), (0x00, 0x00, 0x20)]
    for _ in range(10):
        for i in range(NUM_PADS):
            color = colors[i % len(colors)]
            keypad.illuminate(i, *color)
        keypad.update()
        time.sleep(0.5)
    for i in range(NUM_PADS):
        keypad.illuminate(i, 0x00,0x00,0x00)

def defeat_animation():
    """Affiche une animation de défaite."""
    print("[DÉFAITE] Animation de défaite.")
    for _ in range(5):
        for i in range(NUM_PADS):
            color = (0x20, 0x00, 0x00) if _ % 2 == 0 else (0x00, 0x00, 0x00)
            keypad.illuminate(i, *color)
        keypad.update()
        time.sleep(0.5)
    for i in range(NUM_PADS):
        keypad.illuminate(i, 0x00,0x00,0x00)

def reset_game():
    """Réinitialise les paramètres du jeu pour recommencer."""
    global button_states, yellow_buttons, buttons_to_light, time_limit, buttons_pressed_count
    button_states = [False] * NUM_PADS
    yellow_buttons.clear()
    buttons_to_light = 1
    time_limit = INITIAL_TIME
    buttons_pressed_count = 0
    keypad.update()
    print("[RESET] Nouveau jeu.")

# Boucle principale du jeu
while True:
    reset_game()  # Réinitialise le jeu à chaque début

    # Exécution du jeu
    while True:
        if rp2.bootsel_button():
            break
        game_continues = start_new_round()
        if not game_continues:
            defeat_animation()
            break  # Arrête le jeu si un bouton reste allumé trop longtemps ou si un bouton jaune est appuyé

        # Vérifie les conditions de victoire
        if buttons_pressed_count >= VICTORY_THRESHOLD:
            victory_animation()
            break

        # Met à jour la difficulté après chaque tour
        update_difficulty()

    # Retourne au début du jeu après une victoire ou une défaite


