import piet
from dop_funcs import *
from normalizer import Normalizer
#print(max_square_size("hw1-11.gif"))
#print(max_square_size("Gallery/one.png"))
#print(piet.PietInterpreter.max_square_size("Gallery/pc.png"))
#piet.PietInterpreter("Gallery/hw1-11.gif").run()
#piet.PietInterpreter("Gallery/pc.png").run()
#piet.PietInterpreter("Gallery/one.png").run()

#print(piet.PietInterpreter.max_square_size("Gallery/helloworld-pietbig.gif"))
#piet.PietInterpreter("Gallery/helloworld-pietbig.gif", 4).run()

'''
wrong:
Gallery/cowsay.png
Gallery/erat2_big.png
Gallery/euclid_clint_big.png
Gallery/GameOfLife.png
Gallery/GetTogetherPiet.png
Gallery/hw2-11.gif  # белое пространство обрабатывается некоректно... Или нет?
Gallery/Piet-4.gif  # судя по всему да
Gallery/fibbig.gif
'''
# for picture in get_all_filenames("Gallery"):
#     print(picture)
#     print(check_colors(picture))
#print(check_pixels_in_allowed_colors("Gallery/one_bright.png"))

#piet.PietInterpreter("Gallery/one-zigzag.png").run()
#piet.PietInterpreter("Gallery/one.png").run()
a = Normalizer.convet_image_to_pixels("Gallery/one.png")
print(1)
