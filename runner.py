# system libs
import argparse
import multiprocessing as mp
import time
import os
import shutil
import json
import boto3
from copy import deepcopy

# 3rd party libs
import numpy as np

# Local libs
import canvasapi
from bracket import Bracket

#https://stackoverflow.com/a/37737985
def turn_worker(board, send_end, p_func, returnqueue):
    try:
        start = time.perf_counter()
        send_end.send(p_func(board))
        end = time.perf_counter()
        returnqueue.put(end - start)
    except:
        returnqueue.put(-1)
        


class Game:
    def __init__(self, player1, player2, timeout):
        self.players = [player1, player2]
        self.colors = ['yellow', 'red']
        self.current_turn = 0
        self.board = np.zeros([6,7]).astype(np.uint8)
        self.gui_board = []
        self.game_over = False
        self.ai_turn_limit = timeout
        self.winner = 0
        self.totaltimes = [0, 0]

    def make_move(self):
        if not self.game_over:
            current_player = self.players[self.current_turn]
            if current_player.type == 'ai':
                
                if self.players[int(not self.current_turn)].type == 'random':
                    p_func = current_player.get_expectimax_move
                else:
                    p_func = current_player.get_alpha_beta_move
                
                try:
                    recv_end, send_end = mp.Pipe(False)
                    queue = mp.Queue()
                    p = mp.Process(target=turn_worker, args=(deepcopy(self.board), send_end, p_func, queue))
                    p.start()
                    if p.join(self.ai_turn_limit) is None and p.is_alive():
                        p.terminate()
                        raise Exception('Player Exceeded time limit')
                    turntime = queue.get(timeout=self.ai_turn_limit)
                    if (turntime < 0):
                        raise Exception()
                    print(current_player.player_number, turntime)
                    self.totaltimes[self.current_turn] += turntime
                    # print('Turn time:', end - start)
                except Exception as e:
                    uh_oh = 'Uh oh.... something is wrong with Player {}'
                    print(uh_oh.format(current_player.player_number))
                    print(e)
                    
                    self.winner = 3 - current_player.player_number
                    self.game_over = True
                    return
                    # raise Exception('Game Over')

                move = recv_end.recv()
            else:
                move = current_player.get_move(self.board)

            if move is not None:
                try:
                    self.update_board(int(move), current_player.player_number)
                except Exception as e:
                    print ('Error updating board. Most likely move is invalid. Player ', current_player.player_number)
                    print (e)
                    self.winner = 3 - current_player.player_number
                    self.game_over = True
                    return

            if self.game_completed(current_player.player_number):
                self.winner = current_player.player_number
                self.game_over = True
                # self.player_string.configure(text=self.players[self.current_turn].player_string + ' wins!')
            else:
                self.current_turn = int(not self.current_turn)
                # self.player_string.configure(text=self.players[self.current_turn].player_string)

    def update_board(self, move, player_num):
        if 0 in self.board[:,move]:
            update_row = -1
            for row in range(1, self.board.shape[0]):
                update_row = -1
                if self.board[row, move] > 0 and self.board[row-1, move] == 0:
                    update_row = row-1
                elif row==self.board.shape[0]-1 and self.board[row, move] == 0:
                    update_row = row

                if update_row >= 0:
                    self.board[update_row, move] = player_num
                    # self.c.itemconfig(self.gui_board[move][update_row],
                    #                   fill=self.colors[self.current_turn])
                    break
        else:
            err = 'Invalid move by player {}. Column {}'.format(player_num, move)
            raise Exception(err)


    def game_completed(self, player_num):
        player_win_str = '{0}{0}{0}{0}'.format(player_num)
        board = self.board
        to_str = lambda a: ''.join(a.astype(str))

        def check_horizontal(b):
            for row in b:
                if player_win_str in to_str(row):
                    return True
            return False

        def check_verticle(b):
            return check_horizontal(b.T)

        def check_diagonal(b):
            for op in [None, np.fliplr]:
                op_board = op(b) if op else b
                
                root_diag = np.diagonal(op_board, offset=0).astype(np.int)
                if player_win_str in to_str(root_diag):
                    return True

                for i in range(1, b.shape[1]-3):
                    for offset in [i, -i]:
                        diag = np.diagonal(op_board, offset=offset)
                        diag = to_str(diag.astype(np.int))
                        if player_win_str in diag:
                            return True

            return False

        return (check_horizontal(board) or
                check_verticle(board) or
                check_diagonal(board))

def get_json(coursenum, timeout):
    try:
        with open('3/aws-secret-access-key', 'r') as asak, open('2/aws-access-key-id', 'r') as aaki:
            session = boto3.Session(aws_secret_access_key=asak.read().strip(), aws_access_key_id = aaki.read().strip())
            s3 = session.resource('s3')
            client = session.client('s3', endpoint_url='https://s3.nautilus.optiputer.net')

            
            val = client.get_object(Bucket='connect4', Key='cse'+str(coursenum)+'_'+str(timeout)+'sec')
            if val['ResponseMetadata']['HTTPStatusCode'] == 200:
                return eval(val['Body'].read().decode('utf-8'))
            else:
                return None
    except Exception as e:
        print ('Error getting json:')
        print (e)
        print ('Response:')
        print (val)
        return None

def put_json(seedinglist, coursenum, timeout):
    try:
        with open('3/aws-secret-access-key', 'r') as asak, open('2/aws-access-key-id', 'r') as aaki:
            session = boto3.Session(aws_secret_access_key=asak.read().strip(), aws_access_key_id = aaki.read().strip())
            s3 = session.resource('s3')
            client = session.client('s3', endpoint_url='https://s3.nautilus.optiputer.net')

            jsondata = json.dumps(seedinglist)

            val = client.put_object(Body=jsondata, Bucket='connect4', Key='cse'+str(coursenum)+'_'+str(timeout)+'sec')
    except Exception as e:
        print ('Error putting json:')
        print (e)
        print ('Response:')
        print (val)
        return None

def generate_bracket(time, seeding):
    submission_folders = os.listdir('./submissions')
    if len(submission_folders) == 0:
        return None
    elif len(submission_folders) == 1:
        return submission_folders
    # Assumption: Each submission folder has a single submission file in it
    submission_agents = []
    submission_import_strings = []
    for folder in submission_folders:
        files = os.listdir('./submissions/' + folder)
        if len(files) > 1 or len(files) == 0:
            print(folder, ' has no or more than 1 files in submission')
            submission_import_strings.append(None)
        else:
            if files[0].split('.')[-1] == 'py':
                submission_import_strings.append('submissions/' + folder + '/' + files[0])
                print('submissions/' + folder + '/' + files[0])
    
    submission_pairs = list(zip(submission_folders, submission_import_strings))
    submission_pairs_cleaned = [x for x in submission_pairs if x[1] is not None]

    print('Submission name/file pairs:')
    print(submission_pairs_cleaned)

    if seeding is not None:
        seeded_pairs = []
        nonseeded_pairs = []
        submission_dict = dict(submission_pairs_cleaned)
        
        submission_keys = list(submission_dict.keys())
        for seed in seeding:
            if seed in submission_keys:
                seeded_pairs.append((seed, (submission_dict[seed])))

        seed_dict = dict(seeded_pairs)
        seed_keys = list(seed_dict.keys())
        for nonseed in submission_keys:
            if nonseed not in seed_keys:
                nonseeded_pairs.append((nonseed, submission_dict[nonseed]))

        submission_pairs_cleaned = seeded_pairs + nonseeded_pairs
    print('players:', submission_pairs_cleaned)
    return Bracket(submission_pairs_cleaned, time)

def run_game(player1, player2, timeout):
    if (player1 is None):
        return 2, float('inf'), 0
    elif (player2 is None):
        return 1, 0, float('inf')
    try:
        p1 = canvasapi.import_agent(player1, 1)
    except Exception as e:
        print (e, player1)
        return 2, float('inf'), 0
    try:    
        p2 = canvasapi.import_agent(player2, 2)
    except Exception as e:
        print (e, player2)
        return 1, 0, float('inf')
    game = Game(p1, p2, timeout)
    while (not game.game_over):
        # Check for and handle tie
        if np.count_nonzero(game.board) == (game.board.shape[0] * game.board.shape[1]) and game.winner == 0:
            game.winner = 2 if game.totaltimes[0] > game.totaltimes[1] else 1
            break
            
        game.make_move()
    
    print(game.totaltimes[0], game.totaltimes[1])
    return game.winner, game.totaltimes[0], game.totaltimes[1]

def main(coursenum, timeout, putnone):
    """
    Creates player objects based on the string paramters that are passed
    to it and calls play_game()

    INPUTS:
    player1 - a string ['ai', 'random', 'human']
    player2 - a string ['ai', 'random', 'human']
    """

    seeding = get_json(coursenum, timeout)
    print('seeding:', seeding)
    
    b = generate_bracket(timeout, seeding)
    if b is not None and type(b) is Bracket:
        b.evalBracket(run_game)
        placings = b.getPlacings()
        print(placings)
        if not putnone:
            put_json(placings, coursenum, timeout)
    elif b is not None and type(b) is list:
        # print('Only 1 entrant.')
        print(b)
        if not putnone:
            put_json(b, coursenum, timeout)
    else:
        print('Less than two entrants, no bracket run')

if __name__=='__main__':
    coursemap = {'140' : 29782, '240' : 29857}
    assignmentmap = {'140' : 120497, '240' : 112762}
    courses = ['140', '240']
    parser = argparse.ArgumentParser()
    parser.add_argument('course', choices=courses)
    parser.add_argument('--time',
                        type=int,
                        default=5,
                        help='Time to wait for a move in seconds (int)')
    parser.add_argument('--delsubs', dest='delsubs', action='store_true')
    parser.add_argument('--getnone', dest='getnone', action='store_true')
    parser.add_argument('--putnone', dest='putnone', action='store_true')
    parser.set_defaults(delsubs=False)
    args = parser.parse_args()
    coursenumber = coursemap[args.course]
    assignmentnumber = assignmentmap[args.course]

    # Get all submissions from given course
    if not args.getnone:
        with open('1/apikey') as token:
            if args.delsubs and os.path.exists('./submissions') and os.path.isdir('./submissions'):
                shutil.rmtree('./submissions')
            canvasapi.get_submissions(coursenumber, assignmentnumber, token.read().strip())#, dest_path='./' + str(args.course) + 'submissions')
        
    main(args.course, args.time, args.putnone)
