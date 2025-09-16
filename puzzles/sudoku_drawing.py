"""
This module is used to draw Sudoku puzzles populated with values passed
as a single string. It was used for early debugging of Sudoku solving 
and filling algorithms but will probably be deprecated. The drawing
is painfully slow and logging the puzzles to file works well. Keeping 
it around for now just in case.
"""
import turtle

my_pen = turtle.Turtle()
cell_size = 50 #50's a good size
pen_size = 3   #3 is good for main grid lines
corner_offset = 0
grid_major_color = "#000000"    #black
grid_minor_color = "#D3D3D3"    #grey
numeral_color = "#FF0000"
fill_color = "#FFFFFF"          #white
draw_speed = 0    # 1..10, 0 = no animation
grid_previously_filled = False
font_size = 15
FONT = ('Arial', font_size, 'normal')
backup_step_size = 5
undo_count = backup_step_size * 81
screen = turtle.Screen()
pause_drawing = False


def toggle_pause():
    global pause_drawing
    pause_drawing ^= pause_drawing
#
def draw_grid(): 
    my_pen.speed(draw_speed)
    my_pen.hideturtle()
 
    global corner_offset
    corner_offset = (cell_size * 9 + pen_size) // 2

    draw_internal_dividers()   #do this first so main lines drawn over
 
    my_pen.color(grid_major_color)
    my_pen.pensize(pen_size)
    my_pen.penup()
 
    #draw grid outline
    my_pen.goto(-1 * corner_offset, corner_offset)
    my_pen.pendown()
    my_pen.goto(corner_offset, corner_offset)
    my_pen.goto(corner_offset, -1 * corner_offset)
    my_pen.goto(-1 * corner_offset, -1 * corner_offset)
    my_pen.goto(-1 * corner_offset, corner_offset)
    my_pen.penup()
  
    #box dividers
    dividers_offset = (cell_size * 3 + pen_size) // 2

    #vertical dividers
    my_pen.goto(-1 * dividers_offset,  corner_offset)
    my_pen.pendown()
    my_pen.goto(-1 * dividers_offset,  -1 * corner_offset)
    my_pen.penup()

    my_pen.goto(dividers_offset, corner_offset)
    my_pen.pendown()
    my_pen.goto(dividers_offset, -1 * corner_offset)
    my_pen.penup()

   #horizontal dividers
    my_pen.goto(-1 * corner_offset, dividers_offset)
    my_pen.pendown()
    my_pen.goto(corner_offset, dividers_offset)
    my_pen.penup()

    my_pen.goto(-1 * corner_offset, -1 * dividers_offset)
    my_pen.pendown()
    my_pen.goto(corner_offset, -1 * dividers_offset)
    my_pen.penup()

    # screen.listen()
    # screen.onkeypress(toggle_pause, "space")

#take numerals from flat list and write them into grid
def fill_drawn_grid(flat_grid):

    try: 
        global grid_previously_filled

        if grid_previously_filled is True:
            for itr in range(undo_count):
                my_pen.undo()
        else:
            grid_previously_filled = True

        cell_left  = -1 * (corner_offset - pen_size)  #move right
        cell_top = corner_offset - pen_size    #move down
    
        column = cell_left
        my_pen.color(numeral_color)
        my_pen.pensize(10)

        #NOTE: if this loop changes will need to update
        for itr in range(len(flat_grid)):
            display_number(flat_grid[itr], column, cell_top)
        
            #set up for next number
            if ((itr + 1) % 9 == 0):
                cell_top -= cell_size    #step down to next row
                column =  cell_left
            else:
                column += cell_size
    except Exception as ex:
        raise Exception(f"Exception occured in soduku_drawing.fill_drawn_grid(): {ex}")

#
def wait_on_drawing():
    turtle.mainloop() #required to keep puzzle open

#numeral's bottom-left corner ends up at whatever coord we give it here
def display_number(numeral, col, row):

    #Calculate offset to place numeral in center of cell
    #attempting to adjust for font size but no guarantee it's xy proportional
    col_offset = cell_size // 2 - (font_size // 2)
    row_offset = cell_size // 2 + (font_size // 2 + 3)
    
    # If the number of pen operations change below the global variable backup_step_size must be updated
    my_pen.penup()  # not counting this step in backup_step_size
    my_pen.color(numeral_color)
    my_pen.goto(col + col_offset, row - row_offset)    		  
    my_pen.pendown()
    my_pen.write(numeral, align="left", font=FONT)
    my_pen.penup()

#
def draw_internal_dividers():
    #column (vertical) dividers
    my_pen.color(grid_minor_color)
    my_pen.pensize(1)
    my_pen.penup()

    for cell_col in range(1,9):
        if(cell_col %3 == 0):
           continue
        vert_cell_offset = (corner_offset - pen_size) - cell_col * cell_size
        my_pen.goto(vert_cell_offset, -1 * corner_offset)
        my_pen.pendown()
        my_pen.goto(vert_cell_offset, corner_offset)
        my_pen.penup()

    #row cell dividers
    for cell_row in range(1,9):
        if(cell_row %3 == 0):
           continue
        horiz_cell_offset = (corner_offset - pen_size) - cell_row * cell_size
        my_pen.goto(-1 * corner_offset, horiz_cell_offset)
        my_pen.pendown()
        my_pen.goto(corner_offset, horiz_cell_offset)
        my_pen.penup()


