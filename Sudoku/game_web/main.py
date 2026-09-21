import asyncio
import copy
import random
import pygame

pygame.font.init()

# Window Setup
WIDTH, HEIGHT = 670, 650
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultimate Sudoku Suite")
font = pygame.font.SysFont("comicsans", 35)
title_font = pygame.font.SysFont("comicsans", 45)
small_font = pygame.font.SysFont("comicsans", 25)

# Initial fallback board
DEFAULT_BOARD = [
    [0, 0, 3, 0, 0, 0, 6, 8, 0],
    [6, 0, 0, 0, 0, 8, 0, 0, 0],
    [0, 7, 0, 0, 3, 0, 5, 0, 2],
    [0, 0, 0, 5, 0, 6, 3, 0, 0],
    [0, 0, 0, 7, 0, 0, 0, 0, 0],
    [4, 0, 0, 1, 8, 0, 0, 9, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 4, 0, 8, 0, 0],
    [0, 5, 2, 0, 0, 0, 0, 0, 0],
]

custom_board = copy.deepcopy(DEFAULT_BOARD)
active_board = copy.deepcopy(DEFAULT_BOARD)


# --- Sudoku Logic Helpers ---
def find_empty(bo):
    for i in range(len(bo)):
        for j in range(len(bo[0])):
            if bo[i][j] == 0:
                return i, j
    return None


def valid(bo, num, pos):
    # Check row
    for i in range(len(bo[0])):
        if bo[pos[0]][i] == num and pos[1] != i:
            return False

    # Check column
    for i in range(len(bo)):
        if bo[i][pos[1]] == num and pos[0] != i:
            return False

    # Check 3x3 box
    box_x, box_y = pos[1] // 3, pos[0] // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if bo[i][j] == num and (i, j) != pos:
                return False

    return True


def solve_board(bo):
    """Solves a board completely using backtracking."""
    empty = find_empty(bo)
    if not empty:
        return True
    row, col = empty
    numbers = list(range(1, 10))
    random.shuffle(numbers)

    for num in numbers:
        if valid(bo, num, (row, col)):
            bo[row][col] = num
            if solve_board(bo):
                return True
            bo[row][col] = 0
    return False


def generate_random_sudoku():
    """Generates a playable random Sudoku board by solving an empty board and removing cells."""
    board = [[0 for _ in range(9)] for _ in range(9)]
    solve_board(board)

    # Remove cells to create the puzzle (e.g., remove 45 cells for a good challenge)
    cells_to_remove = 45
    while cells_to_remove > 0:
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        if board[row][col] != 0:
            board[row][col] = 0
            cells_to_remove -= 1

    return board


# Backtracking step generator for bot & race mode
def get_bot_generator(board_ref):
    stack_empty = []
    stack_av = []

    def generator_step():
        empty = find_empty(board_ref)
        if not empty:
            return True  # Done
        y, x = empty

        available = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        available = [n for n in available if valid(board_ref, n, (y, x))]

        if available:
            board_ref[y][x] = available[0]
            stack_empty.append((y, x))
            next_c = list(available)
            next_c.pop(0)
            stack_av.append(next_c)
        else:
            board_ref[y][x] = 0
            if stack_empty:
                p_y, p_x = stack_empty.pop()
                p_av = stack_av.pop()
                while not p_av and stack_empty:
                    board_ref[p_y][p_x] = 0
                    p_y, p_x = stack_empty.pop()
                    p_av = stack_av.pop()
                if p_av:
                    board_ref[p_y][p_x] = p_av[0]
                    stack_empty.append((p_y, p_x))
                    new_av = list(p_av)
                    new_av.pop(0)
                    stack_av.append(new_av)
                else:
                    board_ref[p_y][p_x] = 0
            else:
                return False  # Unsolvable
        return False

    return generator_step


# --- UI Screens ---
async def main_menu():
    global active_board, custom_board
    run = True
    while run:
        win.fill((240, 248, 255))

        # Draw Title
        title = title_font.render("SUDOKU ARCADE", 1, (20, 40, 80))
        win.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

        # Menu Buttons
        buttons = [
            ("1. Play Yourself (New Random Board)", 150),
            ("2. Watch Bot Solver (Custom/Default)", 230),
            ("3. Race Against Bot (New Random Board)", 310),
            ("4. Custom Board Editor (For Bots)", 390),
            ("Quit", 470),
        ]

        mouse_pos = pygame.mouse.get_pos()
        rects = []
        for text, y in buttons:
            rect = pygame.Rect(WIDTH // 2 - 200, y, 400, 50)
            rects.append((rect, text))
            pygame.draw.rect(win, (70, 130, 180), rect, border_radius=8)
            label = small_font.render(text, 1, (255, 255, 255))
            win.blit(
                label,
                (
                    rect.x + (rect.width - label.get_width()) // 2,
                    rect.y + (rect.height - label.get_height()) // 2,
                ),
            )

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, text in rects:
                    if rect.collidepoint(mouse_pos):
                        if "1." in text:
                            active_board = generate_random_sudoku()
                            await play_manual_mode()
                        elif "2." in text:
                            active_board = copy.deepcopy(custom_board)
                            await watch_bot_mode()
                        elif "3." in text:
                            await race_mode()
                        elif "4." in text:
                            await custom_editor_mode()
                        elif "Quit" in text:
                            return "QUIT"

        await asyncio.sleep(0.01)


# Mode 1: Play Manually
async def play_manual_mode():
    selected = None
    run = True
    orig = [[cell != 0 for cell in row] for row in active_board]

    while run:
        win.fill((255, 255, 255))
        for i in range(10):
            thick = 4 if i % 3 == 0 else 1
            pygame.draw.line(win, (0, 0, 0), (0, i * 60), (540, i * 60), thick)
            pygame.draw.line(win, (0, 0, 0), (i * 60, 0), (i * 60, 540), thick)

        if selected:
            pygame.draw.rect(
                win,
                (173, 216, 230),
                (selected[1] * 60 + 1, selected[0] * 60 + 1, 58, 58),
            )

        for i in range(9):
            for j in range(9):
                if active_board[i][j] != 0:
                    color = (0, 0, 255) if orig[i][j] else (0, 0, 0)
                    text = font.render(str(active_board[i][j]), 1, color)
                    win.blit(text, (j * 60 + 20, i * 60 + 10))

        back_rect = pygame.Rect(20, 570, 120, 40)
        pygame.draw.rect(win, (200, 50, 50), back_rect, border_radius=5)
        b_text = small_font.render("<- Menu", 1, (255, 255, 255))
        win.blit(b_text, (back_rect.x + 20, back_rect.y + 8))

        if find_empty(active_board) is None:
            won_text = font.render("PUZZLE SOLVED!", 1, (0, 150, 0))
            win.blit(won_text, (180, 575))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if back_rect.collidepoint(pos):
                    return
                if pos[1] < 540:
                    selected = (pos[1] // 60, pos[0] // 60)
            if event.type == pygame.KEYDOWN and selected:
                if not orig[selected[0]][selected[1]]:
                    if event.key in [
                        pygame.K_1,
                        pygame.K_2,
                        pygame.K_3,
                        pygame.K_4,
                        pygame.K_5,
                        pygame.K_6,
                        pygame.K_7,
                        pygame.K_8,
                        pygame.K_9,
                    ]:
                        val = int(event.unicode)
                        if valid(active_board, val, selected):
                            active_board[selected[0]][selected[1]] = val
                    elif event.key in [
                        pygame.K_BACKSPACE,
                        pygame.K_DELETE,
                        pygame.K_0,
                    ]:
                        active_board[selected[0]][selected[1]] = 0

        await asyncio.sleep(0.01)


# Mode 2: Watch Bot Solver
async def watch_bot_mode():
    run = True
    started = False
    step_func = get_bot_generator(active_board)
    orig = [[cell != 0 for cell in row] for row in active_board]

    while run:
        win.fill((255, 255, 255))
        for i in range(10):
            thick = 4 if i % 3 == 0 else 1
            pygame.draw.line(win, (0, 0, 0), (0, i * 60), (540, i * 60), thick)
            pygame.draw.line(win, (0, 0, 0), (i * 60, 0), (i * 60, 540), thick)

        for i in range(9):
            for j in range(9):
                if active_board[i][j] != 0:
                    color = (0, 0, 255) if orig[i][j] else (0, 120, 0)
                    text = font.render(str(active_board[i][j]), 1, color)
                    win.blit(text, (j * 60 + 20, i * 60 + 10))

        back_rect = pygame.Rect(20, 570, 120, 40)
        pygame.draw.rect(win, (200, 50, 50), back_rect, border_radius=5)
        b_text = small_font.render("<- Menu", 1, (255, 255, 255))
        win.blit(b_text, (back_rect.x + 20, back_rect.y + 8))

        if not started:
            info = small_font.render("Press SPACE to Start Bot", 1, (100, 100, 100))
            win.blit(info, (160, 580))
        elif find_empty(active_board) is None:
            info = font.render("SOLVED!", 1, (0, 200, 0))
            win.blit(info, (180, 575))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(pygame.mouse.get_pos()):
                    return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                started = True

        if started and find_empty(active_board) is not None:
            step_func()
            await asyncio.sleep(0.02)
        else:
            await asyncio.sleep(0.01)


# Mode 3: Race Against Bot
async def race_mode():
    shared_base = generate_random_sudoku()
    player_board = copy.deepcopy(shared_base)
    bot_board = copy.deepcopy(shared_base)

    bot_step = get_bot_generator(bot_board)
    selected = None
    started = False
    winner = None
    orig = [[cell != 0 for cell in row] for row in shared_base]

    run = True
    while run:
        win.fill((250, 250, 250))

        banner = small_font.render(
            "RACE! Fill your board (Left) before the Bot (Right) finishes!",
            1,
            (0, 0, 0),
        )
        win.blit(banner, (20, 10))

        # Draw Player Board (405x405 grid)
        for i in range(10):
            thick = 3 if i % 3 == 0 else 1
            pygame.draw.line(win, (0, 0, 0), (0, i * 45 + 40), (405, i * 45 + 40), thick)
            pygame.draw.line(win, (0, 0, 0), (i * 45, 40), (i * 45, 445), thick)

        if selected:
            pygame.draw.rect(
                win,
                (173, 216, 230),
                (selected[1] * 45 + 1, selected[0] * 45 + 41, 43, 43),
            )

        for i in range(9):
            for j in range(9):
                if player_board[i][j] != 0:
                    col = (0, 0, 255) if orig[i][j] else (0, 0, 0)
                    txt = small_font.render(str(player_board[i][j]), 1, col)
                    win.blit(txt, (j * 45 + 15, i * 45 + 50))

        # Draw Bot Board Preview on Right
        bot_label = small_font.render("Bot Progress:", 1, (100, 100, 100))
        win.blit(bot_label, (430, 40))
        for i in range(10):
            thick = 2 if i % 3 == 0 else 1
            pygame.draw.line(
                win, (100, 100, 100), (430, i * 25 + 70), (655, i * 25 + 70), thick
            )
            pygame.draw.line(
                win, (100, 100, 100), (i * 25 + 430, 70), (i * 25 + 430, 295), thick
            )

        for i in range(9):
            for j in range(9):
                if bot_board[i][j] != 0:
                    txt = pygame.font.SysFont("comicsans", 18).render(
                        str(bot_board[i][j]), 1, (0, 120, 0)
                    )
                    win.blit(txt, (j * 25 + 436, i * 25 + 73))

        back_rect = pygame.Rect(20, 600, 100, 35)
        pygame.draw.rect(win, (200, 50, 50), back_rect, border_radius=5)
        win.blit(small_font.render("<- Menu", 1, (255, 255, 255)), (28, 606))

        if not started:
            st_msg = small_font.render("Press SPACE to Begin Race!", 1, (200, 0, 0))
            win.blit(st_msg, (140, 606))
        elif not winner:
            if find_empty(player_board) is None:
                winner = "YOU WIN!"
            elif find_empty(bot_board) is None:
                winner = "BOT WINS!"
        else:
            win_msg = font.render(winner, 1, (200, 0, 0))
            win.blit(win_msg, (430, 320))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if back_rect.collidepoint(pos):
                    return
                if 40 <= pos[1] <= 445 and pos[0] <= 405:
                    selected = ((pos[1] - 40) // 45, pos[0] // 45)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not started:
                    started = True
                elif selected and started and not winner:
                    if not orig[selected[0]][selected[1]]:
                        if event.key in [
                            pygame.K_1,
                            pygame.K_2,
                            pygame.K_3,
                            pygame.K_4,
                            pygame.K_5,
                            pygame.K_6,
                            pygame.K_7,
                            pygame.K_8,
                            pygame.K_9,
                        ]:
                            val = int(event.unicode)
                            if valid(player_board, val, selected):
                                player_board[selected[0]][selected[1]] = val
                        elif event.key in [
                            pygame.K_BACKSPACE,
                            pygame.K_DELETE,
                            pygame.K_0,
                        ]:
                            player_board[selected[0]][selected[1]] = 0

        if started and not winner:
            for _ in range(3):
                if find_empty(bot_board) is not None:
                    bot_step()
            await asyncio.sleep(0.02)
        else:
            await asyncio.sleep(0.01)


# Mode 4: Custom Board Builder (For Bot Modes)
async def custom_editor_mode():
    global custom_board
    selected = None
    run = True

    while run:
        win.fill((255, 255, 255))
        for i in range(10):
            thick = 4 if i % 3 == 0 else 1
            pygame.draw.line(win, (0, 0, 0), (0, i * 60), (540, i * 60), thick)
            pygame.draw.line(win, (0, 0, 0), (i * 60, 0), (i * 60, 540), thick)

        if selected:
            pygame.draw.rect(
                win,
                (173, 216, 230),
                (selected[1] * 60 + 1, selected[0] * 60 + 1, 58, 58),
            )

        for i in range(9):
            for j in range(9):
                if custom_board[i][j] != 0:
                    text = font.render(str(custom_board[i][j]), 1, (0, 0, 0))
                    win.blit(text, (j * 60 + 20, i * 60 + 10))

        back_rect = pygame.Rect(20, 570, 100, 40)
        pygame.draw.rect(win, (200, 50, 50), back_rect, border_radius=5)
        win.blit(small_font.render("<- Menu", 1, (255, 255, 255)), (28, 578))

        inst = small_font.render(
            "Build custom board for Bot Solver mode", 1, (100, 100, 100)
        )
        win.blit(inst, (135, 580))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if back_rect.collidepoint(pos):
                    return
                if pos[1] < 540:
                    selected = (pos[1] // 60, pos[0] // 60)
            if event.type == pygame.KEYDOWN and selected:
                if event.key in [
                    pygame.K_1,
                    pygame.K_2,
                    pygame.K_3,
                    pygame.K_4,
                    pygame.K_5,
                    pygame.K_6,
                    pygame.K_7,
                    pygame.K_8,
                    pygame.K_9,
                ]:
                    custom_board[selected[0]][selected[1]] = int(event.unicode)
                elif event.key in [pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_0]:
                    custom_board[selected[0]][selected[1]] = 0

        await asyncio.sleep(0.01)


async def main():
    while True:
        res = await main_menu()
        if res == "QUIT":
            break
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())