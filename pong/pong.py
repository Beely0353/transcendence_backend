import random

async def pong_game(game_id):
    from .models import Game
    game = await Game.objects.aget(id=game_id)
    ball_position = game.ball_position
    paddle_l_position = game.paddle_position.get('paddle_l')
    paddle_r_position = game.paddle_position.get('paddle_r')

    ball_x = ball_position['x']
    ball_y = ball_position['y']
    ball_dx = game.ball_dx
    ball_dy = game.ball_dy 
    ball_speed = 1

    ball_x += ball_dx * ball_speed
    ball_y += ball_dy * ball_speed

    if ball_y <= 0 or ball_y >= 400:
        ball_dy = -ball_dy

    if ball_x <= 10 and paddle_l_position <= ball_y <= paddle_l_position + 80:
        ball_dx = -ball_dx

    if ball_x >= 790 and paddle_r_position <= ball_y <= paddle_r_position + 80:
        ball_dx = -ball_dx

    if ball_x > 800 or ball_x < 0:
        if ball_x > 800:
            game.score_player_1 += 1
        elif ball_x < 0:
            game.score_player_2 += 1
        ball_x = 400
        ball_y = 200

    game.ball_position = {'x': ball_x, 'y': ball_y}
    game.ball_dx = ball_dx
    game.ball_dy = ball_dy
    await game.asave()

    return ball_x, ball_y
