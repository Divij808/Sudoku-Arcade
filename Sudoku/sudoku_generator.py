import random


def print_board(board):
    for row in board:
        print(" ".join(str(num) if num != 0 else "." for num in row))


def is_valid(board, row, col, num):
    # Check if num exists in the current row
    if num in board[row]:
        return False

    # Check if num exists in the current column
    if num in [board[r][col] for r in range(9)]:
        return False

    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if board[r][c] == num:
                return False

    return True


def fill_board(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                # Try numbers 1-9 in random order for variety
                numbers = list(range(1, 10))
                random.shuffle(numbers)

                for num in numbers:
                    if is_valid(board, row, col, num):
                        board[row][col] = num

                        if fill_board(board):
                            return True

                        board[row][col] = 0
                return False
    return True


# Initialize an empty 9x9 board
sudoku_board = [[0] * 9 for _ in range(9)]
fill_board(sudoku_board)

print("Generated Solved Sudoku Board:")
print_board(sudoku_board)