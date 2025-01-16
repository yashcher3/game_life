

import os
from game_of_life import Game
import tkinter as tk
from typing import Callable, Tuple, Dict
from game_of_life import Singleton

class LifeGameCanvas(tk.Canvas, metaclass=Singleton):

    def __init__(self, cell_size: int, height: int, width: int,
                camera_coef: int, *args, **kwargs)-> None:
        super().__init__(bg="black", height=height, width=width, *args, **kwargs)
        # Additional
        self.width = width
        self.height = height
        self.xcenter, self.ycenter = int(width/2), int(height/2)

        self.cell_size = cell_size, cell_size
        self.cells = []

        self.configure(xscrollincrement=1, yscrollincrement=1)
        self.bind("<B2-Motion>", self.move_camera)
        self.camera_coef = camera_coef
        self.xcamera, self.ycamera = 0, 0
        # Edit
        self.edit = True
        self.bind("<Button-1>", self.event_edit_maker(self.create_cell))
        self.bind("<Button-3>", self.event_edit_maker(self.remove_cell))

    def get_cells(self)-> Tuple[int, int]:

        return tuple(self.cells)

    def render_cells(self, cells):

        self.edit = False
        self.delete("all")
        self.cells = list(cells)
        for x, y in cells:
            self.create_cell(x, y)

    def move_camera(self, event: tk.Event)-> None:

        vector = (-(self.xcenter-event.x), -(self.ycenter-event.y))
        x_dir, y_dir = vector
        x_dir = self.camera_coef*x_dir//self.xcenter
        y_dir = self.camera_coef*y_dir//self.ycenter
        self.xcamera = self.xcamera + x_dir
        self.ycamera = self.ycamera + y_dir
        self.xview_scroll(x_dir, "units")
        self.yview_scroll(y_dir, "units")

    def event_edit_maker(self, func: Callable)-> Callable:

        def event_func(event: tk.Event):
            if self.edit:
                x, y = event.x, event.y
                x, y = self.xcamera+x, self.ycamera+y
                x //= self.cell_size[0]
                y //= self.cell_size[1]
                func(x, y)
        return event_func

    def create_cell(self, x: int, y: int)-> None:
        (x0, y0), (x1, y1) = self.convert_coordinates(x, y)
        self.create_rectangle(x0, y0, x1, y1, fill="#008013", outline="")
        self.cells.append((x, y))

    def remove_cell(self, x: int, y: int)-> None:
        """Remove cell from the canvas by cell coordinates(x, y)."""
        (x0, y0), (x1, y1) = self.convert_coordinates(x, y)
        self.create_rectangle(x0, y0, x1, y1, fill="white", outline="")
        if (x, y) in self.cells:
            self.cells.remove((x, y))

    def convert_coordinates(self, x: int, y: int)-> Tuple[Tuple[int, int]]:

        dx, dy = self.cell_size
        return (x*dx, y*dy), ((x+1)*dx, (y+1)*dy)


class Cycle(metaclass=Singleton):

    def __init__(self, canvas: LifeGameCanvas, delay: int=100)-> None:
        self.canvas = canvas
        self._delay = delay
        self.game = Game()
        self.stop = False

    def start(self)-> None:
        self.stop = False
        self.game.init(self.canvas.get_cells())
        self.update()

    def start_by_steps(self)-> None:
        self.stop = False
        self.game.init(self.canvas.get_cells())
        self.update_one_step()


    def update(self)-> None:
        if not self.stop:
            self.game.update()
            self.canvas.render_cells(self.game.get_cells())
            self.canvas.after(self._delay, self.update)
    def update_one_step(self):
        if not self.stop:
            self.game.update()
            self.canvas.render_cells(self.game.get_cells())


    def quit(self)-> None:
        self.canvas.edit = True
        self.canvas.delete("all")
        self.canvas.cells = []
        self.stop = True
        self.game.clear()

    def set_delay(self, delay: int)-> None:
        self._delay = delay

def set_delay_event(cycle: Cycle, entry: tk.Entry)-> Callable:

    def set_delay():
        try:
            entry_value = int(entry.get())
        except ValueError as e:
            print("The expected delay value was be Integer type.")
        if entry_value > 0:
            cycle.set_delay(entry_value)
        else:
            print("Delay must be bigger than 0!")
    return set_delay


class DoubleStateButton(tk.Button):

    def __init__(self, default_state: Dict, pressed_state: Dict)-> None:
        default_f = default_state.pop("command")
        pressed_f = pressed_state.pop("command")
        if len(pressed_state) == 0:
            pressed_state = default_state.copy()
        ds_command = self.get_double_state_command(default_f, pressed_f)
        super().__init__(command=ds_command, **default_state)
        #
        default_state = dict(self)
        default_state.pop("command")
        self.parity = True

        self.state_configs = {
            default_f:pressed_state,
            pressed_f:default_state
        }

    def set_config(self, f):
        self.configure(**self.state_configs[f])

    def get_double_state_command(
            self, default_f: Callable, pressed_f: Callable)-> Callable:
        def ds_command():
            main_f = default_f if self.parity else pressed_f
            self.set_config(main_f)
            self.parity = not self.parity
            main_f()
        return ds_command


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Игра в жизнь")
    root.geometry("1007x590")

    if os.path.exists("images/image_logo1.ico"):
        root.wm_iconbitmap("images/image_logo1.ico")
    
    canvas = LifeGameCanvas(master=root, width=850, height=550, cell_size=10, camera_coef=3)
    canvas.grid(row=0, column=0, sticky="n", columnspan=3, rowspan=3)

    cycle = Cycle(canvas)
    state_btn = DoubleStateButton(
        default_state={
            "command":cycle.start,
            "text":"Начать цикл",
        },
        pressed_state={
            "command":cycle.quit,
            "text":"Закончить цикл",
            "bg":"red",
            "fg":"white"

        }
    )
    state_btn.grid(row=0, column=3, sticky="n")

    delay_entry = tk.Entry(master=root, width=5)
    delay_entry.insert(tk.END, "100")
    delay_entry.grid(row=2, column=7)
    delay_btn = tk.Button(master=root, text="Установить задержку",
                          command=set_delay_event(cycle, delay_entry))
    delay_btn.grid(row=2, column=3)

    act_btn = tk.Button(master=root, text="Следующий шаг",
                          command=cycle.start_by_steps)
    act_btn.grid(row=1, column=3, sticky='n')


    root.mainloop()


