#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Quildreen <http://www.mottaweb.com.br/>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
Simple pong game to test how ecore and evas work together.
"""

from os.path     import abspath, join as join_path
from functools   import partial
from collections import defaultdict
from random      import uniform as randf, seed

from ecore.evas  import SoftwareX11
from ecore       import main_loop_begin, animator_add, animator_frametime_set,\
                        main_loop_quit
from evas        import Rect
from emotion     import Emotion
from edje        import Edje


# Initializes the random number generation
seed()


# The size of the screen
SCREEN_SIZE  = (480, 480)

# Whether the game is running or not
GAME_RUNNING = True

# Directory where the freaking assets are
DATA_DIR = abspath("./data")
THEME    = join_path(DATA_DIR, 'theme.edj')

# The game (you just lost it :3) 
def game_main():
    # Instantiate a canvas using the SoftwareX11 rendering engine. This
    # does all the work of creating the canvas, assigning it to the
    # rendering engine and integrating it with the `ecore' loop.
    #
    # From there onwards, the only thing left is add objects to the
    # Canvas, and manipulate these objects. The `ecore' loop will call
    # render automatically on `idle'.
    w, h   = SCREEN_SIZE
    ee     = SoftwareX11(w=w, h=h)
    canvas = ee.evas

    # Setups the game window and field by creating objects and adding
    # them to the canvas.
    setup_field(ee)

    # Sets the framerate of the game to 60FPS
    animator_frametime_set(1.0 / 60.0)

    # Finally, shows all this stuff to the user and enters the main
    # loop. From there ownards the only say we have is on the callbacks
    # from the events we've set to watch.
    ee.title = "Pong"
    ee.size_max_set(*SCREEN_SIZE)
    ee.size_min_set(*SCREEN_SIZE)

    ee.show()
    main_loop_begin()

    # Stops stuff when the game ends
    fire_hooks('the:end')

# Whenever we lose the gayme, this function is called, showing a "nice"
# game-over screen and disabling the game object's handlers.
def game_over(canvas):
    global GAME_RUNNING

    bg  = background(canvas, (0, 0, 0, 128))
    txt = text(canvas, "GAME OVER", 48)
    GAME_RUNNING = False



# Hooks are collections of functions that are called when a certain
# user-defined event happens. This dictionary maps each user-defined
# event (by name) to a list of functions to be called.
hooks = defaultdict(list)

# Allows the user to add new hooks to a certain kind of event
def add_hook(kind, fn, *args, **kwargs):
    hooks[kind].append(partial(fn, *args, **kwargs))

# Allows the user to fire all hooks related to the given event, with any
# optional positional/keyword arguments
def fire_hooks(kind, *args, **kwargs):
    for hook in hooks[kind]:
        hook(*args, **kwargs)



# Setups the field, by adding background, paddles, ball and the textual
# representations of scores and player-names to the canvas. These are
# self-aware objects that know how to update themselves, so we don't
# need to worry either about re-rendering them (which is done by
# Evas/Ecore itself), nor with manipulating them.
def setup_field(engine):
    canvas = engine.evas

    make_player(canvas)

    splash_screen(canvas)
    main_menu(canvas)
    game_screen(canvas)

    # Adds some useful hooks
    add_hook('game:over', game_over, canvas)
    fire_hooks('play:bgm', 'bgm.mp3')



# Abstract "classes" for the standard Evas objects. These include simple
# things like background and centered text, to full featured objects,
# like the paddles and the ball itself.
#
# Basically these use the underlying canvas methods to add simple
# geometry objects to the canvas (ie.: canvas.Rectangle()) will create a
# Rectangle object and assign it to the canvas, automatically rendering
# it whenever it's needed.
def background(canvas, colour):
    bg = canvas.Rectangle(color=colour)
    bg.resize(*canvas.size)
    bg.show()

    return bg

# Centered text stuff
def text(canvas, string, size, colour=(200, 200, 200, 128)):
    text = canvas.Text(color=colour)
    text.text_set(string)
    text.font_set('Monospace', size)
    text.show()
    center_text(canvas.rect, text)

    return text

# Centers a text object in the given rectangle
def center_text(rect, text):
    x, y = rect.center
    text.move(x - text.horiz_advance/2
             ,y - text.vert_advance/2)



# Splash screen and main menu
def splash_screen(canvas):
    def show_main_menu(obj, signal, source):
        fire_hooks('show:main-menu')

    splash = Edje(canvas, file=THEME, group='splash')
    splash.signal_callback_add("show,main-menu", "", show_main_menu)
    splash.show()


def main_menu(canvas):
    def on_show():
        menu.signal_emit("show,main-menu", "")

    def quit_game(obj, signal, source):
        main_loop_quit()

    def start_game(obj, signal, source):
        fire_hooks('game:new')

    menu = Edje(canvas, file=THEME, group="main-menu")
    menu.signal_callback_add("game,new",  "", start_game)
    menu.signal_callback_add("game,quit", "", quit_game)
    menu.show()
    
    add_hook('show:main-menu', on_show)


def game_screen(canvas):
    def start_game():
        set_score(0)
        xpaddle('top', canvas, 10)
        xpaddle('bottom', canvas, canvas.rect.right - PADDLE_WIDTH - 10)
        ypaddle('left', canvas, 10)
        ypaddle('right', canvas, canvas.rect.bottom - PADDLE_WIDTH - 10)
        ball(canvas)
        game.show()

    def on_score_change(new_score):
        game.part_text_set("game/score", str(new_score))

    game = Edje(canvas, file=THEME, group="game-screen")
    add_hook("game:new", start_game)
    add_hook('score:change', on_score_change)




# The sizes of the paddle
PADDLE_WIDTH  = 20
PADDLE_HEIGHT = 200 

# Creates a base paddle, at the given position, and using the given
# controller function. The controller is called at 60FPS, in the
# animator callback set by this object, and it's expected to update the
# paddle's state depending on the mouse input.
def paddle(name, canvas, pos, size, controller):
    # Handles the mouse input by updating the paddle's position. This is
    # run at 60 FPS, as long as the game is running (ie.: no
    # game-over).
    #
    # Since the animator expects each callback to return whether it
    # should continue running or not — by signaling with either True or
    # False — we just return the value of GAME_RUNNING here.
    def handle_input():
        screen = canvas.rect.move_by(10, 10).inflate(-20, -20)
        px, py = canvas.pointer_canvas_xy
        controller(pad, px, py)
        pad.rect = pad.rect.clamp(screen)

        return GAME_RUNNING

    pad = canvas.Rectangle(name=name, color=(238, 238, 236, 255))
    pad.resize(*size)
    pad.move(*pos)
    pad.show()

    # Adds the pad area as a solid area, so the ball collides with it.
    add_collision_object(pad)

    # Adds the input handler to the list of animator callbacks
    animator_add(handle_input)

    return pad

# Provides a paddle that's controlled by the x-axis of the mouse input.
def xpaddle(name, canvas, pos):
    def controller(pad, mouse_x, mouse_y):
        pad.move(mouse_x, pad.rect.y)

    return paddle(name, canvas
                 ,(canvas.rect.center_x, pos)
                 ,(PADDLE_HEIGHT, PADDLE_WIDTH)
                 ,controller)

# Provides a paddle that's controlled by the y-axis of the mouse input.
def ypaddle(name, canvas, pos):
    def controller(pad, mouse_x, mouse_y):
        pad.move(pad.rect.x, mouse_y)

    return paddle(name, canvas
                 ,(pos, canvas.rect.center_y)
                 ,(PADDLE_WIDTH, PADDLE_HEIGHT)
                 ,controller) 



# Checks for collisions
solid_areas = []

def add_collision_object(obj):
    solid_areas.append(obj)

def collidesp(rect):
    for obj in solid_areas:
        if obj.rect.intercepts(rect):
            return obj



# The "ball"
BALL_SIZE = (20, 20)

def ball(canvas):
    def clamp_bounds(solid):
        rect = ball.rect
        if solid.name == 'right':  rect.right  = solid.rect.left
        if solid.name == 'left':   rect.left   = solid.rect.right
        if solid.name == 'bottom': rect.bottom = solid.rect.top
        if solid.name == 'top':    rect.top    = solid.rect.bottom

        ball.rect = rect

    def check_collisions():
        solid = collidesp(ball.rect)
        w, h  = BALL_SIZE
        if solid:
            fire_hooks('play:sfx', 'hit.wav')
            increase_score()
            clamp_bounds(solid)
            reverse(x=(solid.name in ['left', 'right'])
                   ,y=(solid.name in ['top', 'bottom']))

    def outta_screen_p():
        return ball.rect.left < 0 or ball.rect.right  > canvas.rect.right \
            or ball.rect.top  < 0 or ball.rect.bottom > canvas.bottom

    def input_handler():
        move()
        check_collisions()
        if outta_screen_p():
            fire_hooks('game:over')

        return GAME_RUNNING

    def move():
        pos[0] += speed['x']
        pos[1] += speed['y']
        ball.move(*pos)

    def init_ball(ball):
        ball.resize(*BALL_SIZE)
        ball.move(*canvas.rect.center)
        ball.show()
        animator_add(input_handler)
        return ball

    def reverse(x=False, y=False):
        w, h = BALL_SIZE
        if x: speed['x'] = max(min(speed['x'], w/2), -w/2) * -1.1
        if y: speed['y'] = max(min(speed['y'], h/2), -h/2) * -1.1

    ball    = init_ball(canvas.Rectangle(color=(171, 180, 161, 200)))
    speed   = {'x': randf(1, 2), 'y': randf(1, 2)}
    pos     = list(ball.pos)

    return ball



# The player's stuff
SCORE = 0

def increase_score():
    set_score(SCORE + 1)
    return True

def set_score(new_score):
    global SCORE
    SCORE = new_score
    fire_hooks('score:change', SCORE)

def score(canvas):
    def on_score_change(new_score):
        score_text.text_set(str(new_score))
        center_text(canvas.rect, score_text)

    score_text = text(canvas, '0', 200, (85, 87, 83, 255))
    add_hook('score:change', on_score_change)
    add_hook('game:new', set_score, 0)
    return score_text



# Brings in some Emotion.
#
# The emotion lib is used to play sounds and videos, and it uses
# the usual Ecore event loop and Evas for rendering.
#
# Emotion can use either `xine' or `gstreamer' as the sound engine, it
# seems, but I haven't dug too much into this. But well, these two are
# fo sho :3
def make_player(canvas, engine="gstreamer"):
    def stop(player):
        player.file = ""
    
    def play(player, media):
        stop(player)
        player.file = join_path(DATA_DIR, media)
        player.play = True

    def replay(player):
        fname = player.file
        stop(player)
        play(player, fname)

    sfx_player = Emotion(canvas, module_filename=engine)
    bgm_player = Emotion(canvas, module_filename=engine)

    bgm_player.on_playback_finished_add(replay)

    add_hook('play:sfx',  play, sfx_player)
    add_hook('game:end',   stop, sfx_player)

    add_hook('play:bgm',  play, bgm_player)
    add_hook('game:over', stop, bgm_player)
    add_hook('game:end',   stop, bgm_player)




########################################################################
if __name__ == '__main__':
    game_main()
    
