import pygame as pg


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0,0,255)
YELLOW = (255, 255, 0)

COLOR = [BLUE,RED]

# game settings
WIDTH = 1024   # 16 * 64 or 32 * 32 or 64 * 16
HEIGHT = 768  # 16 * 48 or 32 * 24 or 64 * 12
FPS = 60
TITLE = "CUTRECOD"
BGCOLOR = DARKGREY


TILESIZE = 32
BULLETSIZE = 8


GRIDWIDTH = WIDTH / TILESIZE
GRIDHEIGHT = HEIGHT / TILESIZE

# Player settings
PLAYER_SPEED = 300
PLAYER_ROT_SPEED = 250
PLAYER_IMG = 'manBlue_gun.png'
PLAYER_HIT_RECT = pg.Rect(0, 0, 35, 35)

TEAM = ["Azul","Rojo"]

PLAYER_SPEED = 400
BULLET_SPEED = 600
BULLET_RATE = 300
