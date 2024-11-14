import time
import picokeypad
import random

keypad = picokeypad.PicoKeypad()
keypad.set_brightness(1.0)

NUM_PADS = keypad.get_num_pads()
initial_button_count = 3  # Nombre de boutons à allumer initialement
current_button_count = initial_button_count
victory_count = 0  # Compteur de victoires pour augmenter les boutons
last_button_states = 0
game_start_time = time.time()
animation_done = False
reset_requested = False
time_limit = 5.0  # Temps initial pour éteindre les boutons
incorrect_button = None  # Bouton incorrect si une erreur d'appui provoque la défaite

# Initialisation des boutons actifs pour éviter l'erreur NameError
active_buttons = set()
initial_active_buttons = set()  # Ensemble pour conserver les boutons initialement bleus

def calculate_score():
    """Calcule le score basé sur le nombre de boutons et le temps alloué."""
    raw_score = current_button_count / float(time_limit)
    score = min(5, raw_score)  # Score entre 1 et 5
    print(f"[SCORE] Score calculé : {score}/{raw_score} (nombre de boutons : {current_button_count}, temps alloué : {time_limit:.2f})")
    return score

def reset_game():
    global active_buttons, initial_active_buttons, game_start_time, animation_done, reset_requested, current_button_count, incorrect_button
    active_buttons = set()
    while len(active_buttons) < current_button_count:
        active_buttons.add(random.randint(0, NUM_PADS - 1))  # Ajoute des boutons uniques aléatoires
    initial_active_buttons = active_buttons.copy()  # Sauvegarde les boutons bleus initiaux
    game_start_time = time.time()
    animation_done = False
    reset_requested = False
    incorrect_button = None  # Réinitialise le bouton incorrect
    print(f"[RESET] Nouvelle partie. Boutons actifs : {active_buttons} - Temps limite : {time_limit:.2f} secondes")

def rainbow_animation(score):
    colors = [(0x20, 0x00, 0x00), (0x20, 0x10, 0x00), (0x10, 0x20, 0x00), (0x00, 0x20, 0x00),
              (0x00, 0x20, 0x10), (0x00, 0x00, 0x20), (0x10, 0x00, 0x20)]
    print(f"[VICTOIRE] Début de l'animation arc-en-ciel avec un score de {score}")
    
    max_buttons = 16
    normalized_score = int((score / 5.0) * max_buttons)

    for _ in range(10):  # Animation répétée 10 fois
        for index in range(max_buttons):
            if index < normalized_score:
                color = colors[index % len(colors)]
                keypad.illuminate(index, *color)
            else:
                keypad.illuminate(index, 0, 0, 0)
        keypad.update()
        time.sleep(0.1)
    
    print("[VICTOIRE] Fin de l'animation arc-en-ciel")

def defeat_animation(incorrect_button):
    """Animation de défaite avec clignotement rouge, sauf pour le bouton incorrect qui reste rouge fixe."""
    print("[DÉFAITE] Début de l'animation de défaite (clignotement rouge)")
    for _ in range(6):  # Durée de l'animation de défaite
        for i in range(NUM_PADS):
            if i == incorrect_button:
                # Laisse le bouton incorrect allumé en rouge fixe
                keypad.illuminate(i, 0x20, 0x00, 0x00)
            else:
                # Clignote les autres boutons en rouge
                color = (0x20, 0x00, 0x00) if _ % 2 == 0 else (0x00, 0x00, 0x00)
                keypad.illuminate(i, *color)
        keypad.update()
        time.sleep(0.5)
    print("[DÉFAITE] Fin de l'animation de défaite")

def special_animation():
    print("[SUPER ANIMATION] Début de l'animation spéciale pour un score de 5")
    colors = [(0x20, 0x00, 0x10), (0x10, 0x20, 0x00), (0x00, 0x10, 0x20), (0x20, 0x20, 0x00),
              (0x10, 0x00, 0x20), (0x00, 0x20, 0x10), (0x20, 0x00, 0x20), (0x00, 0x20, 0x20)]
    for _ in range(50):  # Animation pendant 10 secondes
        for i in range(NUM_PADS):
            color = colors[(i + _) % len(colors)]
            keypad.illuminate(i, *color)
        keypad.update()
        time.sleep(0.2)
    print("[SUPER ANIMATION] Fin de l'animation spéciale")

print(f"[DÉMARRAGE] Nombre de boutons actifs initiaux : {current_button_count} - Temps limite initial : {time_limit:.2f} secondes")

reset_game()  # Démarre la première partie avec les paramètres initiaux

while True:
    button_states = keypad.get_button_states()
    current_time = time.time()
    
    if button_states & 0x01 and not reset_requested:
        press_start_time = current_time
        reset_requested = True
    elif reset_requested and not (button_states & 0x01):
        if current_time - press_start_time >= 1.5:  # Appui long de 1.5s
            time_limit = 5.0
            current_button_count = initial_button_count
            print("[RÉINITIALISATION] Appui long sur le bouton 0 - Jeu réinitialisé")
            reset_game()
        reset_requested = False

    # Gère l'extinction des boutons en appuyant dessus
    if button_states != last_button_states:
        for i in range(NUM_PADS):
            if (button_states >> i) & 0x01:
                if i in active_buttons:
                    active_buttons.remove(i)
                    print(f"[ACTION] Bouton {i} pressé et éteint. Boutons restants : {active_buttons}")
                elif i not in initial_active_buttons:
                    print(f"[DÉFAITE] Bouton {i} pressé alors qu'il n'était pas actif initialement. Défaite immédiate.")
                    incorrect_button = i  # Enregistre le bouton incorrect pour l'animation
                    defeat_animation(incorrect_button)
                    current_button_count = max(initial_button_count, current_button_count - 1)
                    reset_game()
                    break

    for i in range(NUM_PADS):
        if i in active_buttons:
            keypad.illuminate(i, 0x00, 0x00, 0x20)
        else:
            keypad.illuminate(i, 0x05, 0x05, 0x05)

    keypad.update()
    last_button_states = button_states

    # Victoire : animation arc-en-ciel et réduction du temps
    if not active_buttons and not animation_done:
        print("[VICTOIRE] Tous les boutons éteints avant la limite de temps - Temps alloué : {:.2f} secondes".format(time_limit))
        score = calculate_score()
        if score >= 5:
            special_animation()  # Lance l'animation spéciale
            time_limit = 5.0  # Réinitialise le temps limite
            current_button_count = initial_button_count  # Réinitialise le nombre de boutons
            victory_count = 0  # Réinitialise le compteur de victoires
        else:
            rainbow_animation(score)
            time_limit *= 0.95
            time_limit = max(time_limit, 2)
            victory_count += 1
            if victory_count % 2 == 0:
                current_button_count = min(NUM_PADS, current_button_count + 1)
        animation_done = True
        reset_game()
        
    elif current_time - game_start_time >= time_limit and active_buttons:
        print(f"[DÉFAITE] Temps écoulé ({time_limit:.2f} secondes) avec des boutons encore allumés : {active_buttons}")
        defeat_animation(incorrect_button=None)
        current_button_count = max(initial_button_count, current_button_count - 1)
        time_limit *= 1.2
        time_limit=min(time_limit,5)
        reset_game()

    time.sleep(0.1)


