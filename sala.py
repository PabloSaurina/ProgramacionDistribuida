from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, Value, Lock
import traceback
import sys
import pygame as pg
from settings import*
from os import path
from tilemap import *


class Player():
    def __init__(self, g_team, x, y,team,dt):
        self.team = team
        self.gteam = g_team
        self.dt = dt
        self.vx, self.vy = 0, 0
        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.rot = 0
    
    def get_pos(self):
        return([self.x,self.y,self.rot])
    
    def set_pos(self,pos):
        self.x = pos[0]
        self.y = pos[1]
        self.rot = pos[2]

class PlayerSprite(pg.sprite.Sprite):
    def __init__(self,player,game):
        self.game = game
        self.player = player
        self.groups = self.game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = pg.Surface((TILESIZE, TILESIZE))
        if self.player.team == 0:
            self.image.fill(BLUE)
        else:
            self.image.fill(RED)
        self.rect = self.image.get_rect()
        
    def update(self):
        self.rect.x = self.player.x
        self.rect.y = self.player.y


class Wall(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Game():
    def __init__(self,manager):
        self.team = -5
        self.manager = manager
        self.playing = Value('i',1)
        self.clock = pg.time.Clock()
        self.dt = self.clock.tick(FPS) / 1000
        self.load_data()
        self.score = manager.list( [0,0] )
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '1':
                    Wall(self, col, row)
                elif tile == 'P':
                    self.player1 = manager.list([Player(self.team, col, row,0,self.dt)])
                    self.sprite1 = PlayerSprite(self.player1[0],self)
                elif tile == 'Q':
                    self.player2 = manager.list([Player(self.team, col, row,1,self.dt)])
                    self.sprite2 = PlayerSprite(self.player2[0],self)
        self.bullets1 = manager.list([[]])
        self.bullets2 = manager.list([[]])
        self.lock = Lock()

    def load_data(self):
        game_folder = path.dirname(__file__)
        self.map = Map(path.join(game_folder, 'map2.txt'))

    def run(self):
        # game loop - set self.playing = False to end the game
        while self.playing.value:
            self.dt = self.clock.tick(FPS) / 1000
            self.update()
#            self.draw()
    
    def get_all_sprites(self):
        return self.all_sprites
    
    def get_walls(self):
        return self.walls
    
    def get_map(self):
        return self.map

    def quit(self):
        pg.quit()
        sys.exit()
        
    def stop(self):
        self.playing.value = 0

    def update(self):
        self.all_sprites.update()
    
    def is_running(self):
        return self.playing.value == 1
    
    def get_info(self):
        info = {
            'pos_blue_player': self.player1[0].get_pos(),
            'pos_red_player': self.player2[0].get_pos(),
            'bullets1': self.bullets1[0],
            'bullets2': self.bullets2[0],
            'is_running': self.playing.value == 1,
            'score': [self.score[0],self.score[1]]
        }
        return info

    def show_start_screen(self):
        pass

    def show_go_screen(self):
        pass
    
    def set_pos_1(self,pos):
        self.lock.acquire()
        p = self.player1[0]
        p.set_pos(pos)
        self.player1[0] = p
        self.lock.release()
    
    def set_pos_2(self,pos):
        self.lock.acquire()
        p = self.player2[0]
        p.set_pos(pos)
        self.player2[0] = p
        self.lock.release()
    
    def set_bullets(self,bullets,team):
        self.lock.acquire()
        if team:
            self.bullets2[0] = bullets
        else:
            self.bullets1[0] = bullets
        self.lock.release()
    
    def set_score(self,score,team):
        self.lock.acquire()
        self.score[team] = score
        self.lock.release()

def player(side, conn, game):
    try:
        print(f"starting player {TEAM[side]}:{game.get_info()}")
        conn.send( (side, game.get_info()) )
        while game.is_running():
            command = ""
            while command != "next":
                command = conn.recv()
                if command == "quit":
                    game.stop()
                elif command[0] == 'a':
                    game.set_pos_1([int(float(x)) for x in command[1:].split(',')])
                elif command[0] == 'b':
                    game.set_pos_2([int(float(x)) for x in command[1:].split(',')])
                elif command[0] == 'c':
                    if len(command) > 1:
                        game.set_bullets([[float(y) for y in x.split('P')] for x in command[1:].split(',')],0)
                    else:
                        game.set_bullets([],0)
                elif command[0] == 'd':
                    if len(command) > 1:
                        game.set_bullets([[float(y) for y in x.split('P')] for x in command[1:].split(',')],1)
                    else:
                        game.set_bullets([],1)
                elif command[0] == 'e':
                    game.set_score(int(command[1:]),0)
                elif command[0] == 'f':
                    game.set_score(int(command[1:]),1)
            conn.send(game.get_info())
    except:
        traceback.print_exc()
        conn.close()
    finally:
        print(f"Game ended {game}")
        sys.exit()


def main(ip_address,port):
    manager = Manager()
    try:
        with Listener((ip_address, port),
                      authkey=b'secret password') as listener:
            n_player = 0
            players = [None, None]
            game = Game(manager)
            while True:
                print(f"accepting connection {n_player}")
                conn = listener.accept()
                players[n_player] = Process(target=player,
                                            args=(n_player, conn, game))
                n_player += 1
                if n_player == 2:
                    players[0].start()
                    players[1].start()
                    game.run()
                    n_player = 0
                    players = [None, None]
                    game = Game(manager)

    except Exception as e:
        traceback.print_exc()

if __name__=='__main__':
    ip_address = "127.0.0.1"
    port = 7000
    if len(sys.argv)>1:
        ip_address = sys.argv[1]
    if len(sys.argv)>2:
        port=sys.argv[2]

    main(ip_address,port)
