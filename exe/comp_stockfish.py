import csv
import sys
import re


path_stockfish = '../stockfish/stockfish-5-linux/Linux/stockfish_14053109_x64_modern'
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
import pexpect
import time
import json

command = 'position startpos moves'


def compute_stockfish(position):
    p = subprocess.Popen(path_stockfish, bufsize=1, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write('setoption name MultiPV value 10\n')
    p.stdin.write(command + position + '\n')
    print command + position + '\n'
    p.stdin.write('go depth 15\n')

    o = []
    for i in range(15):
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

while True:
    try:
        n = int(subprocess.check_output(['wget','-O','-','tfjgeorge.com/kaggle/get']))
    except:
        continue
    f_name = 'output_stockfish_%.5d.txt' % (n,)
    f_output = open(f_name ,'w')

    start = time.time()
    game = games[n]

    f_output.write('Game %d\n' % n)
    f_output.write('Current date: %d\n' % int(time.time()))

    game_s = ''
    print game
    for move in game['game_uci']:
        game_s += ' ' + move

        f_output.write(json.dumps(compute_stockfish(game_s)))
        f_output.flush()

    t_total = int(time.time() - start)
    f_output.write('- Computing time: %d\n' % int(time.time() - start))
    f_output.write('---\n')

    try:
        ssh = pexpect.spawn('scp %s kaggle@tfjgeorge.com:~' % f_name)
        ssh.expect('.*password:')
        ssh.sendline('elo')
        ssh.expect(pexpect.EOF)
    except:
        pass

    print 'Game', n
    print 'Time', t_total

