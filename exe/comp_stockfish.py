import csv
import re

file_stockfish = open('../data/stockfish.csv', 'r')
csv_file_games = open('../data/data_uci.pgn', 'r')
games = []
game = dict()

re_field = re.compile('\[(?P<tag>\w*) "(?P<val>[^"]*)"\]')

file_stockfish.readline()
l = csv_file_games.readline()
while l:

    if len(l.strip()) > 0 and l[0] != '[':
        str_game = l.strip()

        l = csv_file_games.readline()
        while l.strip():
            str_game += ' ' + l.strip()
            l = csv_file_games.readline()

        moves = str_game.strip().split(' ')

        if moves[-1] == '1-0' or moves[-1] == '0-1' or moves[-1] == '1/2-1/2':
            moves.pop()

        game['game_uci'] = moves

        d, s, stockfish_s = file_stockfish.readline().partition(',')
        stockfish = []
        for i in stockfish_s.split():
            if i != 'NA':
                stockfish.append(int(i))
            else:
                stockfish.append(None)

        game['stockfish'] = stockfish

        games.append(game)
        game = dict()

        l = csv_file_games.readline()
        continue

    info = re_field.match(l)
    if info:
        game[info.group('tag')] = info.group('val')


    l = csv_file_games.readline()

games_training = games[0:25000]
games_test = games[25000:]

import subprocess
import time
import json

command = 'position startpos moves '

path_stockfish = '/home/tfjgeorge/kaggle/chess/stockfish/stockfish-5-linux/Linux/stockfish_14053109_x64'

def compute_stockfish(position):
    p = subprocess.Popen(path_stockfish, bufsize=1, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write('setoption name MultiPV value 10\n')
    p.stdin.write(command + position + '\n')
    p.stdin.write('go depth 15\n')

    o = []
    for i in range(20):
        o.append([{},{},{},{},{},{},{},{},{},{}])

    start = time.time()
    while True:
        l = p.stdout.readline()
        if l[0:4] == 'info':
            splitd = l.split()
            if len(splitd) >= 17:
                if splitd[14] == 'multipv':
                    depth = int(splitd[2])
                    move_ranking = int(splitd[15])
                    o[depth-1][move_ranking-1]['bestmove'] = splitd[17]
                    o[depth-1][move_ranking-1]['score'] = splitd[7]

        if l[0:8] == 'bestmove':
            break

    p.terminate()

    return o


f_output = open('output_stockfish.txt','w')
for i in range(25000):
    start = time.time()
    game = games_training[i]

    f_output.write('Game %d\n')
    f_output.write('Current date: %d' % int(time.time()))

    game_s = command
    for move in game:
        game_s += ' ' + move

        f_output.write(json.dumps(compute_stockfish(game_s)))
        f_output.flush()

    t_total = int(time.time() - start)
    f_output.write('- Computing time: %d\n' % int(time.time() - start))
    f_output.write('---\n')

    print 'Game', i
    print 'Time', t_total

