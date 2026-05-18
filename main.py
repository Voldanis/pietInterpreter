import piet
from dop_funcs import *
from normalizer import Normalizer

'''
piet.PietInterpreter("Gallery/three.png").run()
print()
piet.PietInterpreter("Gallery/hw1-11.gif").run()
piet.PietInterpreter("Gallery/hw3-5.gif").run()
piet.PietInterpreter("Gallery/pc.png").run()
piet.PietInterpreter("Gallery/helloworld-pietbig.gif", 4).run()
piet.PietInterpreter("Gallery/helloworld-pietbig.gif", 8).run()
piet.PietInterpreter("Gallery/alpha_filled_big.png").run()
print()
piet.PietInterpreter("Gallery/one-zigzag.png").run()
print()
piet.PietInterpreter("Gallery/hw2-11.gif").run()  # endless
piet.PietInterpreter("Gallery/cowsay.png").run()
piet.PietInterpreter("Gallery/euclid_clint_big.png").run()
piet.PietInterpreter("Gallery/GameOfLife.png").run()
piet.PietInterpreter("Gallery/tetris_big.png").run()
piet.PietInterpreter("Gallery/hw6_big.png").run()
piet.PietInterpreter("Gallery/ILoveYouLaura.png").run()
piet.PietInterpreter("Gallery/two_bmp.bmp").run()
'''





'''
wrong:
Gallery/erat2_big.png
Gallery/GetTogetherPiet.png
Gallery/Piet-4.gif  # судя по всему да
Gallery/fibbig.gif
Gallery/helloworld-cmb-sm.png
'''
# for picture in get_all_filenames("Gallery"):
#     print(picture)
#     print(check_colors(picture))
#print(check_pixels_in_allowed_colors("Gallery/one_bright.png"))

'''
    def get_border_axis(self):
        if self.state.dp == DirPointerState.RIGHT or self.state.dp == DirPointerState.LEFT:
            return 0
        return 1
        
    def find_block_border(self, axis, block):
        if self.state.dp == DirPointerState.RIGHT:
            border_coord = max(codel[axis] for codel in block)
        elif self.state.dp == DirPointerState.DOWN:
            border_coord = max(codel[axis] for codel in block)
        elif self.state.dp == DirPointerState.LEFT:
            border_coord = min(codel[axis] for codel in block)
        else:  # Up
            border_coord = min(codel[axis] for codel in block)
        border = [codel for codel in block if codel[axis] == border_coord]
        return border
    
    def find_exit_codel_by_cc(self, border):
        return 
        
        
    

bottom = []
for i in range(shift):
bottom.append(roll.pop())
        
        
    

'''
