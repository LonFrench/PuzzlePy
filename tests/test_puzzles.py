"""
Unit tests for Sudoku related puzzle building and validation.
"""
import unittest
import test_data
from sudoku import *

#TODO: look into redirecting to output file?
class SudokuTest(unittest.TestCase):

    # Tests for Sudoku parameter validation at initialization:
    def test_build_exception_invalid_dimension(self):
        with self.assertRaises(SudokuBuildError):   #using exception test within context 
            SudokuPuzzleBuilder(dimension = 7)
        
    def test_build_exception_all_values_dimension_size_mismatch(self):
        with self.assertRaises(SudokuBuildError):
            SudokuPuzzleBuilder(dimension = 9, all_possible_values = ['1','2','3','4','5'])
        
    def test_build_exception_invalid_all_values_size(self):
        with self.assertRaises(SudokuBuildError):
            SudokuPuzzleBuilder(all_possible_values = ['1','2','3','4','5'])
        
    def test_build_exception_invalid_placeholder(self):
        with self.assertRaises(SudokuBuildError):
            SudokuPuzzleBuilder(all_possible_values = ['1','2','3','4','5','6','7','8','9'], placeholder = '5')
        
    def test_build_exception_invalid_all_values_container(self):
        with self.assertRaises(SudokuBuildError):
            SudokuPuzzleBuilder(starting_values = [['1','2','3'],['4','5','6'],['7','8','9']])
        
    def test_cell_creation_no_indices(self):
        with self.assertRaises(CellExcept):
            cell = SudokuCell('9')

    def test_cell_creation_bad_index(self):
        with self.assertRaises(CellExcept):
            cell = SudokuCell('7', row_index = 5, column_index = -2)  

    def test_cell_creation_val_too_large(self):
        with self.assertRaises(CellExcept):
            cell = SudokuCell('12', placeholder = "x")

    # Tests for Sudoku puzzle creation:
        #__init__(self, starting_values = None, dimension = 9, all_possible_values = default_value_options, placeholder = default_placeholder)
    def test_fill_empty_9x9_puzzle(self):
        builder = SudokuPuzzleBuilder()
        sudoku_puzzle = builder.get_puzzle()
        sudoku_puzzle.fill()
        self.assertEqual(sudoku_puzzle.unsolved_cell_count(),0)

    def test_fill_empty_16x16_puzzle(self):
        builder = SudokuPuzzleBuilder(dimension = 16, all_possible_values = ['1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g'], placeholder = ' ')
        sudoku_puzzle = builder.get_puzzle()
        sudoku_puzzle.fill()
        self.assertEqual(sudoku_puzzle.unsolved_cell_count(),0)

    def test_alternate_placeholder(self):
        builder = SudokuPuzzleBuilder(test_data.hard_puzzle_189x, placeholder = "x")
        sudoku_puzzle = builder.get_puzzle()
        sudoku_solver = SudokuSolver(sudoku_puzzle)
        sudoku_solver.solve_puzzle()
        solved_puzzle = sudoku_solver.get_puzzle()
        self.assertEqual(solved_puzzle.unsolved_cell_count(),0)

    # Tests for Sudoku puzzle solution:
    def test_solve_easy(self):
        builder = SudokuPuzzleBuilder(test_data.easy_puzzle_21, placeholder = " ")
        sudoku_puzzle = builder.get_puzzle()
        sudoku_solver = SudokuSolver(sudoku_puzzle)
        sudoku_solver.solve_puzzle()
        solved_puzzle = sudoku_solver.get_puzzle()
        self.assertEqual(solved_puzzle.unsolved_cell_count(),0)

    def test_solve_difficult(self):
        builder = SudokuPuzzleBuilder(test_data.hard_puzzle_189, placeholder = " ")
        sudoku_puzzle = builder.get_puzzle()
        sudoku_solver = SudokuSolver(sudoku_puzzle)
        sudoku_solver.solve_puzzle()
        solved_puzzle = sudoku_solver.get_puzzle()
        self.assertEqual(solved_puzzle.unsolved_cell_count(),0)

    def test_solve_challenging(self):
        builder = SudokuPuzzleBuilder(test_data.chal_puzzle_262, placeholder = " ")
        sudoku_puzzle = builder.get_puzzle()
        sudoku_solver = SudokuSolver(sudoku_puzzle)
        sudoku_solver.solve_puzzle()
        solved_puzzle = sudoku_solver.get_puzzle()
        self.assertEqual(solved_puzzle.unsolved_cell_count(),0)

    def test_fill_partial(self):
        builder = SudokuPuzzleBuilder(test_data.chal_puzzle_262, placeholder = " ")
        sudoku_puzzle = builder.get_puzzle()
        sudoku_puzzle.fill()
        self.assertEqual(sudoku_puzzle.unsolved_cell_count(),0)

    def test_verify_difficult_solution(self):
        builder = SudokuPuzzleBuilder(test_data.hard_puzzle, placeholder = ' ')
        puzzle = builder.get_puzzle()
        solver = SudokuSolver(puzzle)
        solver.solve_puzzle()
        solved_puzzle = solver.get_puzzle()

        builder = SudokuPuzzleBuilder(test_data.hard_puzzle_solved, placeholder = ' ')
        solution = builder.get_puzzle()
        self.assertEqual(solved_puzzle, solution)

#TODO: add solution verification tests for easy and challenging puzzles
# TODO: add unit test(s) to populate puzzle with multi-char strings
# class PuzzleTest(unittest.TestCase):


if __name__ == "__main__":
    unittest.main()

    # To debug a specific unit test comment out above statement and make call below
    # test_debug = SudokuTest()
    # test_debug.test_cell_creation_bad_index()