import pygame
import random
import copy

class Chip8:
    def __init__(self):
        self.current_rom_path = ""
        self.bg_colour = (0,0,0)
        self.memory = bytearray(4096)
        self.v = bytearray(16)
        self.i = 0
        self.pc = 0x200
        self.stack = []

        # --- DISPLAY SEPARATION ---
        self.display = [0] * (64 * 32)          # True logical state (0 or 1)
        self.visual_display = [0.0] * (64 * 32) # Fade state (0.0 to 1.0)
        
        self.delay_timer = 0
        self.sound_timer = 0
        self.keypad = [0] * 16

        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0, 0x20, 0x60, 0x20, 0x20, 0x70,
            0xF0, 0x10, 0xF0, 0x80, 0xF0, 0xF0, 0x10, 0xF0, 0x10, 0xF0,
            0x90, 0x90, 0xF0, 0x10, 0x10, 0xF0, 0x80, 0xF0, 0x10, 0xF0,
            0xF0, 0x80, 0xF0, 0x90, 0xF0, 0xF0, 0x10, 0x20, 0x40, 0x40,
            0xF0, 0x90, 0xF0, 0x90, 0xF0, 0xF0, 0x90, 0xF0, 0x10, 0xF0,
            0xF0, 0x90, 0xF0, 0x90, 0x90, 0xE0, 0x90, 0xE0, 0x90, 0xE0,
            0xF0, 0x80, 0x80, 0x80, 0xF0, 0xE0, 0x90, 0x90, 0x90, 0xE0,
            0xF0, 0x80, 0xF0, 0x80, 0xF0, 0xF0, 0x80, 0xF0, 0x80, 0x80
        ]
        for i, val in enumerate(fontset):
            self.memory[i] = val

    def load_rom(self, path):
        with open(path, "rb") as f:
            rom_data = f.read()
            self.memory[0x200:0x200+len(rom_data)] = rom_data
        self.current_rom_path = path

    def cycle(self):
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        n = (opcode & 0x000F)
        nn = (opcode & 0x00FF)
        nnn = (opcode & 0x0FFF)
        
        self.decode(opcode, x, y, n, nn, nnn)

    def decode(self, opcode, x, y, n, nn, nnn):
        first = (opcode & 0xF000) >> 12
        match first:
            case 0x0:
                if opcode == 0x00E0: #Clear Screen
                    self.display = [0] * (64 * 32)
                elif opcode == 0x00EE: self.pc = self.stack.pop()
            case 0x1: self.pc = nnn
            case 0x2:
                self.stack.append(self.pc)
                self.pc = nnn
            case 0x3: 
                if self.v[x] == nn: self.pc += 2
            case 0x4: 
                if self.v[x] != nn: self.pc += 2
            case 0x5: 
                if self.v[x] == self.v[y]: self.pc += 2
            case 0x6: self.v[x] = nn
            case 0x7: self.v[x] = (self.v[x] + nn) & 0xFF
            case 0x8:
                if   n == 0x0: self.v[x] = self.v[y]
                elif n == 0x1: self.v[x] |= self.v[y]
                elif n == 0x2: self.v[x] &= self.v[y]
                elif n == 0x3: self.v[x] ^= self.v[y]
                elif n == 0x4:
                    total = self.v[x] + self.v[y]
                    self.v[0xF] = 1 if total > 255 else 0
                    self.v[x] = total & 0xFF
                elif n == 0x5:
                    self.v[0xF] = 1 if self.v[x] >= self.v[y] else 0
                    self.v[x] = (self.v[x] - self.v[y]) & 0xFF
                elif n == 0x6:
                    self.v[0xF] = self.v[x] & 0x1
                    self.v[x] >>= 1
                elif n == 0x7:
                    self.v[0xF] = 1 if self.v[y] >= self.v[x] else 0
                    self.v[x] = (self.v[y] - self.v[x]) & 0xFF
                elif n == 0xE:
                    self.v[0xF] = (self.v[x] & 0x80) >> 7
                    self.v[x] = (self.v[x] << 1) & 0xFF
            case 0x9: 
                if self.v[x] != self.v[y]: self.pc += 2
            case 0xA: self.i = nnn
            case 0xB: self.pc = nnn + self.v[0]
            case 0xC: self.v[x] = random.randint(0, 255) & nn
            case 0xD: self.draw_sprite(x, y, n)
            case 0xE:
                if nn == 0x9E: 
                    if self.keypad[self.v[x]]: self.pc += 2
                elif nn == 0xA1: 
                    if not self.keypad[self.v[x]]: self.pc += 2
            case 0xF:
                if nn == 0x07: self.v[x] = self.delay_timer
                elif nn == 0x15: self.delay_timer = self.v[x]
                elif nn == 0x18: self.sound_timer = self.v[x]
                elif nn == 0x1E: self.i = (self.i + self.v[x]) & 0xFFF
                elif nn == 0x29: self.i = self.v[x] * 5
                elif nn == 0x33:
                    self.memory[self.i] = self.v[x] // 100
                    self.memory[self.i+1] = (self.v[x] // 10) % 10
                    self.memory[self.i+2] = self.v[x] % 10
                elif nn == 0x55:
                    for reg in range(x + 1): self.memory[self.i + reg] = self.v[reg]
                elif nn == 0x65:
                    for reg in range(x + 1): self.v[reg] = self.memory[self.i + reg]
                elif nn == 0x0A:
                    pressed = False
                    for idx, key in enumerate(self.keypad):
                        if key:
                            self.v[x] = idx
                            pressed = True
                            break
                    if not pressed: self.pc -= 2

    def update_timers(self):
        if self.delay_timer > 0: self.delay_timer -= 1
        if self.sound_timer > 0: self.sound_timer -= 1

    def draw_sprite(self, x_reg, y_reg, height):
        x_start = self.v[x_reg] % 64
        y_start = self.v[y_reg] % 32
        self.v[0xF] = 0

        for row in range(height):
            sprite_byte = self.memory[self.i + row]
            for col in range(8):
                if (sprite_byte & (0x80 >> col)):
                    x_pos = (x_start + col) % 64
                    y_pos = (y_start + row) % 32
                    index = x_pos + (y_pos * 64)

                    #XOR
                    if self.display[index] == 1:
                        self.v[0xF] = 1
                        self.display[index] = 0
                    else:
                        self.display[index] = 1

    def draw(self, surface, scale, bg_color, fg_color, crt_enabled):
        fade_speed = 0.90 if crt_enabled else 0.0 # Instant clear if CRT off
        
        for index in range(len(self.display)):
            # Logic vs Visual separation
            if self.display[index] == 1:
                self.visual_display[index] = 1.0
            else:
                self.visual_display[index] *= fade_speed
            
            val = self.visual_display[index]
                
            if val > 0.01: # Slight threshold for performance
                x = (index % 64) * scale
                y = (index // 64) * scale
                
                # Linear Interpolation Formula: 
                # color = bg_color + (fg_color - bg_color) * val
                r = int(bg_color[0] + (fg_color[0] - bg_color[0]) * val)
                g = int(bg_color[1] + (fg_color[1] - bg_color[1]) * val)
                b = int(bg_color[2] + (fg_color[2] - bg_color[2]) * val)
                
                pygame.draw.rect(surface, (r, g, b), (x, y, scale, scale))

    def get_snapshot(self):
        return copy.deepcopy(self)

    def load_snapshot(self, snapshot):
        # Overwrite current state with the saved state
        self.memory = copy.deepcopy(snapshot.memory)
        self.v = copy.deepcopy(snapshot.v)
        self.i = snapshot.i
        self.pc = snapshot.pc
        self.stack = copy.deepcopy(snapshot.stack)
        self.display = copy.deepcopy(snapshot.display)
        self.delay_timer = snapshot.delay_timer
        self.sound_timer = snapshot.sound_timer
        # We usually don't save keypad state to avoid "stuck" keys