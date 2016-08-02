#!/usr/bin/python3
#
# Matrix-Curses
# See how deep the rabbit hole goes.
# Copyright (c) 2012 Tom Wallroth
#
# Sources on github:
#   http://github.com/devsnd/matrix-curses/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#
import time
import curses
import random


class FallingChar(object):
    matrix_chars = list("ɀɁɂŧϢϣϤϥϦϧϨϫϬϭϮϯϰϱϢϣϤϥϦϧϨϩϪϫϬϭϮϯϰ߃߄")
    normal_attr = curses.A_NORMAL
    highlight_attr = curses.A_REVERSE
    
    def __init__(self, width, min_speed, max_speed, color_char_normal,
                 color_char_highlight):
        self.x = 0
        self.y = 0
        self.speed = 1
        self.char = ' '
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.color_char_normal = color_char_normal
        self.color_char_highlight = color_char_highlight
        self.reset(width)
    
    def reset(self, width):
        self.char = random.choice(FallingChar.matrix_chars)
        self.x = random.randint(1, width - 2)
        self.y = 0
        self.speed = random.randint(self.min_speed, self.max_speed - 1)
    
    def tick(self, scr, steps):
        height, width = scr.getmaxyx()
        if self.advances(steps):
            self.out_of_bounds_reset(width, height)
            scr.addstr(self.y, self.x, self.char,
                       curses.color_pair(self.color_char_normal))
            
            self.char = random.choice(FallingChar.matrix_chars)
            self.y += 1
            if not self.out_of_bounds_reset(width, height):
                scr.addstr(self.y, self.x, self.char,
                           curses.color_pair(self.color_char_highlight))
    
    def out_of_bounds_reset(self, width, height):
        if self.x > width - 2:
            self.reset(width)
            return True
        if self.y > height - 2:
            self.reset(width)
            return True
        return False
    
    def advances(self, steps):
        if steps % (self.speed + random.randint(0, self.speed - 1)) == 0:
            return True
        return False


def run(seconds):
    steps = 0
    scr = curses.initscr()
    scr.nodelay(1)
    curses.curs_set(0)
    curses.noecho()
    
    curses.start_color()
    curses.use_default_colors()
    color_char_normal = 1
    color_char_highlight = 2
    curses.init_pair(color_char_normal, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(color_char_highlight, curses.COLOR_WHITE,
                     curses.COLOR_GREEN)
    
    height, width = scr.getmaxyx()
    lines = []
    min_speed = 1
    max_speed = 6
    for i in range(50):
        line = FallingChar(width, min_speed, max_speed, color_char_normal,
                           color_char_highlight)
        line.y = random.randint(0, height - 3)
        lines.append(line)
    
    scr.refresh()
    
    start = time.time()
    
    fps = 25
    while True:
        height, width = scr.getmaxyx()
        for line in lines:
            line.tick(scr, steps)
        for i in range(100):
            x = random.randint(0, width - 2)
            y = random.randint(0, height - 2)
            scr.addstr(y, x, ' ')
        
        scr.refresh()
        if scr.getch() != -1:
            break
        
        if (time.time() - start) >= seconds:
            break
        
        time.sleep(1.0 / fps)
        
        steps += 1
    
    curses.endwin()
    curses.curs_set(1)
    curses.reset_shell_mode()
    curses.echo()
