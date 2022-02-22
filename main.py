import os
import sys
import time
import numpy as np
import random as rng

import tcod
import tcod.event
import tcod.noise
import tcod.map as tmap

import class_camera as cam
import class_actor as act
import class_tile as tile
import class_race as race
import class_log as log
import class_map as mp
import class_ui as ui
import generate as gen

render_fov = True
current_floor = 0
paused = 0
turn = 0
state = 'MAIN' #MAIN, GAME, etc

def get_time():
    return int(round(time.time() * 1000))

rng.seed()

#Check if the tile at the actors position plus direction is a walkable tile
def check_collision(actor, cur_map, direction):
    can_move = False
    try:
        if not cur_map.occupied[actor.ypos+direction[1]][actor.xpos+direction[0]][0]:
            can_move = cur_map.map.walkable[actor.ypos+direction[1], actor.xpos+direction[0]]
    except:
        pass
    return can_move

#Check what symbol the tile is at the given location
def check_tile(cur_map, direction):
    return cur_map.tiles[direction[1]][direction[0]].sprite

#Check if there's an enemy for the player to melee attack
def check_melee(actor, cur_map, direction):
    act = actor.is_tile_occupied(cur_map, (actor.xpos+direction[0], actor.ypos+direction[1]))
    if act[0]:
        actor.target = act[1]
        return actor.melee_combat(actor.target)
    return ''

def move_player(actor, cur_map, direction):
    cur_map.occupied[actor.ypos][actor.xpos] = (False, None)
    actor.xpos += direction[0]
    actor.ypos += direction[1]
    cur_map.occupied[actor.ypos][actor.xpos] = (True, actors[0])

def handle_movement(actor, cur_map, direction):
    log_line = ''
    if check_collision(actor, cur_map, direction):
        move_player(actor, cur_map, direction)
    else: 
        log_line = check_melee(actor, cur_map, direction)
    global turn
    turn = 1
    return log_line

#~~~~Switcher definitions~~~~
def move_up():
    log_line = ''
    if not paused:
        global current_floor
        log_line = handle_movement(actors[0], dungeon[current_floor], (0, -1))
    return log_line

def move_down():
    log_line = ''
    if not paused:
        global current_floor
        log_line = handle_movement(actors[0], dungeon[current_floor], (0, 1))
    return log_line

def move_left():
    log_line = ''
    if not paused:
        global current_floor
        log_line = handle_movement(actors[0], dungeon[current_floor], (-1, 0))
    return log_line

def move_right():
    log_line = ''
    if not paused:
        global current_floor
        log_line = handle_movement(actors[0], dungeon[current_floor], (1, 0))
    return log_line

def move_ul():
    log_line = ''
    if not paused:
        global current_floor
        log_line = handle_movement(actors[0], dungeon[current_floor], (-1, -1))
    return log_line

def move_ur():
    log_line = ''
    if not paused:
        global current_floor
        log_line = handle_movement(actors[0], dungeon[current_floor], (1, -1))
    return log_line

def move_dl():
    log_line = ''
    if not paused:
        global current_floor
        log_line = handle_movement(actors[0], dungeon[current_floor], (-1, 1))
    return log_line

def move_dr():
    log_line = ''
    if not paused:
        global current_floor
        log_line = handle_movement(actors[0], dungeon[current_floor], (1, 1))
    return log_line

def ascend():
    global current_floor
    if check_tile(dungeon[current_floor], (actors[0].xpos, actors[0].ypos)) == '<':
        current_floor -= 1
        actors[0].xpos = dungeon[current_floor].stairs_down[0]
        actors[0].ypos = dungeon[current_floor].stairs_down[1]
    return ''

def descend():
    global current_floor
    if check_tile(dungeon[current_floor], (actors[0].xpos, actors[0].ypos)) == '>':
        current_floor += 1
        actors[0].xpos = dungeon[current_floor].stairs_up[0]
        actors[0].ypos = dungeon[current_floor].stairs_up[1]
    return ''

def idle():
    global turn
    turn = 1
    return ''

def pause_menu():
    global paused
    if paused:
        paused = 0
        main_ui.layers[1][0].visible = 0
    else:
        paused = 1
        main_ui.layers[1][0].visible = 1
    return ''

def toggle_fov():
    global render_fov
    render_fov *= -1
    return ''

def save():
    save_game(actors, dungeon)
    return ''
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Function to act as a switch statement based on the key pressed by the user
def key_switcher(arg):
    switcher = {
        tcod.event.K_UP: move_up,
        tcod.event.K_DOWN: move_down,
        tcod.event.K_LEFT: move_left,
        tcod.event.K_RIGHT: move_right,

        tcod.event.K_KP_1: move_dl,
        tcod.event.K_KP_2: move_down,
        tcod.event.K_KP_3: move_dr,
        tcod.event.K_KP_4: move_left,
        tcod.event.K_KP_5: idle,
        tcod.event.K_KP_6: move_right,
        tcod.event.K_KP_7: move_ul,
        tcod.event.K_KP_8: move_up,
        tcod.event.K_KP_9: move_ur,

        tcod.event.K_F2: save,

        tcod.event.K_COMMA: ascend,
        tcod.event.K_PERIOD: descend,

        tcod.event.K_ESCAPE: pause_menu,

        tcod.event.K_SPACE: toggle_fov
        }

    func = switcher.get(arg, lambda: '')

    return func()

def update_UI(main_ui, actors, combat_log):
    main_ui.layers[0][0].content_layers[0].lines[0] = f'Race: {actors[0].race[1]}'
    main_ui.layers[0][0].content_layers[0].lines[1] = '──────────────────'
    main_ui.layers[0][0].content_layers[0].lines[2] = f'HP: {actors[0].stats[0]} / {actors[0].stats[1]}'
    main_ui.layers[0][0].content_layers[0].lines[3] = f'SP: {actors[0].stats[2]} / {actors[0].stats[3]}'
    main_ui.layers[0][0].content_layers[0].lines[4] = f'STR: {actors[0].stats[4]:<4} INT: {actors[0].stats[7]}'
    main_ui.layers[0][0].content_layers[0].lines[5] = f'DEX: {actors[0].stats[5]:<4} WIL: {actors[0].stats[8]}'
    main_ui.layers[0][0].content_layers[0].lines[6] = f'CON: {actors[0].stats[6]:<4} SPI: {actors[0].stats[9]}'
    main_ui.layers[0][0].content_layers[0].lines[7] = f'PER: {actors[0].stats[10]:<4} LUK: {actors[0].stats[11]}'

    a = ''
    text = ['Race: ',
            f'Level: {actors[0].level:<4} Exp: {actors[0].exp}',
            f'Hit Points   - {actors[0].stats[0]} / {actors[0].stats[1]}',
            f'Magic Points - {actors[0].stats[2]} / {actors[0].stats[3]}',
            '',
            f'{a:<12} - {actors[0].stats[4]}',
            f'{a:<12} - {actors[0].stats[5]}',
            f'{a:<12} - {actors[0].stats[6]}',
            f'{a:<12} - {actors[0].stats[7]}',
            f'{a:<12} - {actors[0].stats[8]}',
            f'{a:<12} - {actors[0].stats[9]}',
            f'{a:<12} - {actors[0].stats[10]}',
            f'{a:<12} - {actors[0].stats[11]}'
            ]

    #main_ui.layers[0][1].content_layers[0] = (ui.Content(combat_log.text, [], []))
    main_ui.layers[1][0].content_layers[0] = (ui.Content(text,[],[]))
    return

def save_game(actors, dungeon):
    act_path = os.path.join('saves', f'{actors[0].name}')
    dun_path = os.path.join('saves', f'{actors[0].name}')

    if not os.path.exists(act_path): os.makedirs(act_path, exist_ok=True)
    if not os.path.exists(dun_path): os.makedirs(dun_path, exist_ok=True)

    np.save(act_path+'/actors', actors)
    np.save(dun_path+'/dungeon', dungeon)

    print('Saved.')
    return

def load_game(save_folder):
    act_path = os.path.join('saves', save_folder)
    dun_path = os.path.join('saves', save_folder)
    
    temp_act = np.load(act_path+'\\actors.npy', allow_pickle=True)
    temp_dun = np.load(dun_path+'\\dungeon.npy', allow_pickle=True)

    actors = temp_act.tolist()
    dungeon = temp_dun.tolist()
    return (actors, dungeon)

def initialize_game(actors, races, dungeon, current_floor, main_ui, con, camera, save_folder, load=False):
    if load:
        arrays = load_game(save_folder)
        actors = arrays[0]
        dungeon = arrays[1]
    else:
        for i in range(3):
            dungeon.append(gen.make_dungeon(60, 50, 15, False, con))
        gen.connect_floors(dungeon)

        #Put the player in a random room
        i = rng.randint(0, len(dungeon[current_floor].tree))
        x = rng.randint(dungeon[current_floor].rooms[i][0]+1, dungeon[current_floor].rooms[i][0]+dungeon[current_floor].rooms[i][2]-1)
        y = rng.randint(dungeon[current_floor].rooms[i][1]+1, dungeon[current_floor].rooms[i][1]+dungeon[current_floor].rooms[i][3]-1)
        actors.append(act.Actor(name='Test', sprite='@',xpos=x, ypos=y, race=races.stats[0].split(','), floor=current_floor))
        dungeon[current_floor].occupied[y][x] = (True, actors[0])
        dungeon[current_floor].calculate_fov((actors[0].xpos, actors[0].ypos), int(actors[0].vision))
        for i in range(len(dungeon)):
            actors[0].memory.append(np.zeros((dungeon[i].height,dungeon[i].width), dtype=bool, order='F'))
        actors[0].fov = dungeon[current_floor].map.fov
        actors[0].memory[current_floor] |= dungeon[current_floor].map.fov
        camera.center_on_actor(actors[0], (dungeon[current_floor].width, dungeon[current_floor].height))

        #Add enemies into random rooms
        for z in range(32):
            i = rng.randint(0, len(dungeon[current_floor].tree))
            x = rng.randint(dungeon[current_floor].rooms[i][0]+1, dungeon[current_floor].rooms[i][0]+dungeon[current_floor].rooms[i][2]-1)
            y = rng.randint(dungeon[current_floor].rooms[i][1]+1, dungeon[current_floor].rooms[i][1]+dungeon[current_floor].rooms[i][3]-1)
            if x != actors[0].xpos and y != actors[0].ypos:
                actors.append(act.Actor(sprite='b', xpos=x, ypos=y, fg=(255,255,255), race=races.stats[2].split(','), floor=current_floor, level=rng.randint(1, 3)))
                dungeon[current_floor].occupied[y][x] = (True, actors[-1])

    content = ui.Content(['Test'], [], [])
    win = ui.Window(60, 0, 19, 15, content, [], (255,255,255), (0,0,0), 0, 1)
    main_ui.add_window(win, 0)

    content = ui.WrapContent()
    win = ui.ScrollableWindow(60, 16, 19, 15, content, [], (255,255,255), (0,0,0), 0, 1)
    main_ui.add_window(win, 0)

    content = ui.Content([''], [], [])
    win = ui.Window(5, 5, 70, 40, content, [], (255,255,255), (0,0,0), 0, 0)
    main_ui.add_window(win, 1)

    for x in range(len(actors)):
        main_ui.layers[0][0].hoverables[current_floor].append(None)

    for x in range(8):
        main_ui.layers[0][0].content_layers[0].add_line()

    main_ui.layers[1][0].clickables.append(ui.Clickable('Stats', 6, 3, value=0))
    main_ui.layers[1][0].clickables[0].clicked = 1
    main_ui.layers[1][0].clickables[0].args = main_ui.layers[1][0]
    main_ui.layers[1][0].clickables.append(ui.Clickable('Skills', 15, 3, value=1))

    main_ui.layers[1][0].hoverables.append([])
    main_ui.layers[1][0].hoverables.append([])

    content = ['Melee Skills:']
    for i in range(len(actors[0].melee_skills)):
        content.append(f'{actors[0].melee_skills[i][1]:<15}- Level')
        main_ui.layers[1][0].hoverables[1].append(ui.Hoverable(f'{actors[0].get_skill_level("me", i)}', f'{int(actors[0].melee_skills[i][2])} / {actors[0].get_skill_next("me", i)}', 29, 7+i))
    main_ui.layers[1][0].content_layers.append(ui.Content(content,[],[]))

    main_ui.layers[1][0].clickables.append(ui.Clickable('Items', 25, 3, value=2))
    main_ui.layers[1][0].clickables[1].args = main_ui.layers[1][0]
    main_ui.layers[1][0].clickables[2].args = main_ui.layers[1][0]
    main_ui.layers[1][0].content_layers.append(ui.Content(['Empty'],[],[]))

    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable(f'{actors[0].race[1]}', f'{actors[0].race[12]}', 12, 6))
    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable('Strength', 'Determines the amount of damage inflicted in melee combat.', 6, 11))
    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable('Dexterity', 'Determines the chance of successfully hitting a melee attack.', 6, 12))
    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable('Constitution', 'Determines the amount of HP and physical damage reduction.', 6, 13))
    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable('Intelligence', 'Determines the amount of damage inflicted by spells.', 6, 14))
    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable('Willpower', 'Determines the chance of a spell hitting the target.', 6, 15))
    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable('Spirit', 'Determines the amount of SP and magical damage reduction.', 6, 16))
    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable('Perception', 'Determines the visible distance and ranged accuracy.', 6, 17))
    main_ui.layers[1][0].hoverables[0].append(ui.Hoverable('Luck', 'Influences all chances by a certain amount.', 6, 18))
    return (actors, dungeon)

def initialize_main_menu(main_ui):
    content = ui.Content([''], [], [])
    win = ui.Window(5, 5, 70, 40, content, [], (255,255,255), (0,0,0), 0, 1)
    main_ui.add_window(win, 0)

    content = ui.Content([''], [], [])
    win = ui.Window(10, 10, 55, 25, content, [], (255,255,255), (0,0,0), 0, 0)
    main_ui.add_window(win, 0)

    text = next(os.walk('Saves'))[1]
    y = 0
    for save in text:
        main_ui.layers[0][1].clickables.append(ui.Clickable(save, 11, 11+y, value=y, border=0))
        main_ui.layers[0][1].content_layers.append(content)

        main_ui.layers[0][1].clickables[y].function = load_save
        main_ui.layers[0][1].clickables[y].args = (main_ui, save)
        print(main_ui.layers[0][1].clickables[y].args)
        y += 1

    main_ui.layers[0][1].clickables.append(ui.Clickable('Back', 60, 10, border=0))
    main_ui.layers[0][1].clickables[y].function = cancel_load
    
    main_ui.layers[0][0].content_layers.append(ui.Content())
    main_ui.layers[0][0].content_layers.append(ui.Content())

    main_ui.layers[0][0].clickables.append(ui.Clickable('Start new game', 10, 10, value=0, border=0))
    
    main_ui.layers[0][0].clickables.append(ui.Clickable('Load saved game', 10, 14, value=1, border=0))
    main_ui.layers[0][0].clickables.append(ui.Clickable('Quit game', 10, 18, value=2, border=0))
    return

def new_game_button(actors, races, dungeon, current_floor, main_ui, con, camera):
    global state
    main_ui.__init__(con)
    initialize_game(actors, races, dungeon, current_floor, main_ui, con, camera, '', False)
    state = 'GAME'
    return

def load_game_button(actors, dungeon, main_ui):
    main_ui.layers[0][1].visible = 1
    return

def quit_game_button(con):
    sys.exit()

def load_save(main_ui, file):
    global actors, races, dungeon, current_floor, con, camera, state
    main_ui.__init__(con)
    arrays = initialize_game(actors, races, dungeon, current_floor, main_ui, con, camera, file, True)
    actors = arrays[0]
    dungeon = arrays[1]
    state = 'GAME'
    return

def cancel_load():
    main_ui.layers[0][1].visible = 0
    return

#Set up constants and load data
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

font_path = 'anikki16x16_gs_tc.png'
font_flags = tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_ASCII_INROW
tcod.console_set_custom_font(font_path, font_flags)

window_title = 'Roguelike'
fullscreen = False

mousex = 0
mousey = 0
mousebutton = 0

#Initialize the game objects
con = tcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, window_title, fullscreen, tcod.RENDERER_SDL2, 'F', True)
actors = []
races = race.Actor_Race()
dungeon = []
main_ui = ui.UI(con)
camera = cam.Camera()
combat_log = log.TextLog()

log_line = ""

initialize_main_menu(main_ui)
main_ui.layers[0][0].clickables[0].function = new_game_button
main_ui.layers[0][0].clickables[0].args = (actors, races, dungeon, current_floor, main_ui, con, camera)

main_ui.layers[0][0].clickables[1].function = load_game_button
main_ui.layers[0][0].clickables[1].args = (actors, dungeon, main_ui)

main_ui.layers[0][0].clickables[2].function = quit_game_button
main_ui.layers[0][0].clickables[2].args = (con)

#arrays = initialize_game(actors, races, dungeon, current_floor, main_ui, con, camera, True)
#actors = arrays[0]
#dungeon = arrays[1]

#CORE GAME LOOP
while True:
    oldtime = get_time()
    con.clear()

    #Check if the game should be restricted to player vision or not
    if state == 'GAME':
        if render_fov == 1:
            dungeon[current_floor].render_fov(actors[0].memory[current_floor], con, camera)
        else:
            dungeon[current_floor].render(con, camera)

        i = 0
        for actor in actors:
            if i == 0:
                actor.render(con, camera)
            elif actor.floor == current_floor:
                if actor.death_check():
                    dungeon[current_floor].occupied[actor.ypos][actor.xpos] = (False, None)
                    main_ui.layers[0][0].hoverables[current_floor][i] = None
                    actors.remove(actor)
                if turn and not paused:
                    log_line = actor.alert_ai(dungeon[current_floor], actors)
                    if log_line != "":
                        combat_log.pushLine(log_line)
                        main_ui.layers[0][1].add_line(log_line)

                    actor.fov = tmap.compute_fov(dungeon[actor.floor].map.transparent, (actor.ypos, actor.xpos), actor.vision)
                    #Check if the player is visible, if so target them
                    if actor.check_sight(actors[0]):
                        actor.alert = 100
                        actor.target = actors[0]
                
                if render_fov == -1:
                    actor.render(con, camera)
                    enemyinfo = f'{actor.race[1]}\nLevel: {actor.level}'
                    main_ui.layers[0][0].hoverables[current_floor][i] = ui.Hoverable('', enemyinfo, actor.xpos-camera.xpos, actor.ypos-camera.ypos, actor.fg, actor.bg, actor.fg, actor.bg)
                elif actors[0].fov[actor.ypos][actor.xpos]:
                    actor.render(con, camera)
                    enemyinfo = f'{actor.race[1]}\nLevel: {actor.level}'
                    main_ui.layers[0][0].hoverables[current_floor][i] = ui.Hoverable('', enemyinfo, actor.xpos-camera.xpos, actor.ypos-camera.ypos, actor.fg, actor.bg, actor.fg, actor.bg)
                else:
                    main_ui.layers[0][0].hoverables[current_floor][i] = None
            i += 1

        turn = 0

        update_UI(main_ui, actors, combat_log)
    elif state == 'MAIN':
        pass

    #Handle user input and then enemy turns
    for event in tcod.event.get():
        if event.type == 'KEYDOWN':
            if not turn and state == 'GAME':
                log_line = key_switcher(event.sym)
                if(log_line != ''):
                    combat_log.pushLine(log_line)
                    main_ui.layers[0][1].add_line(log_line)
            
                camera.center_on_actor(actors[0], (dungeon[current_floor].width, dungeon[current_floor].height))
                dungeon[current_floor].calculate_fov((actors[0].xpos, actors[0].ypos), int(actors[0].vision))
                actors[0].fov = dungeon[current_floor].map.fov
                actors[0].memory[current_floor] |= dungeon[current_floor].map.fov
            break
        if event.type == 'MOUSEMOTION':
            mousex = int(event.pixel[0] / 16)
            mousey = int(event.pixel[1] / 16)
            main_ui.handle_input((mousex, mousey), mousebutton)
        if event.type == 'MOUSEBUTTONDOWN':
            mousebutton = event.button
            main_ui.handle_input((mousex, mousey), mousebutton)
        else:
            mousebutton = 0
    con.print(0,1,f'Game Loop Took: {get_time()-oldtime}ms')

    main_ui.render((mousex, mousey))
        
    tcod.console_flush()
