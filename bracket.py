import math
import random

class Tree:
    def __init__(self, l, r, v, a, d):
        self.left = l
        self.right = r
        self.player = v
        self.agent_str = a
        self.depth = d
        self.time = None
        
    def get_level_nodes(self, level):
        if self.depth > level + 1:
            return []
        if self.depth == level + 1:
            return [(self.player, self.time)]
                
        return [n for n in self.left.get_level_nodes(level)] + [n for n in self.right.get_level_nodes(level)]
    
    def display(self):
        lines, _, _, _ = self._display_aux()
        return lines

    def _display_aux(self):
        """Returns list of strings, width, height, and horizontal coordinate of the root."""
        # No child.
        if self.right is None and self.left is None:
            line = '%s' % ((self.player if self.player else 'Bye') + '/' + (str(self.time) if self.time else 'NA'))
            width = len(line)
            height = 1
            middle = width // 2
            return [line], width, height, middle

        # Only left child.
        if self.right is None:
            lines, n, p, x = self.left._display_aux()
            s = '%s' % ((self.player if self.player else 'Bye') + '/' + (str(self.time) if self.time else 'NA'))
            u = len(s)
            first_line = (x + 1) * ' ' + (n - x - 1) * '_' + s
            second_line = x * ' ' + '/' + (n - x - 1 + u) * ' '
            shifted_lines = [line + u * ' ' for line in lines]
            return [first_line, second_line] + shifted_lines, n + u, p + 2, n + u // 2

        # Only right child.
        if self.left is None:
            lines, n, p, x = self.right._display_aux()
            s = '%s' % ((self.player if self.player else 'Bye') + '/' + (str(self.time) if self.time else 'NA'))
            u = len(s)
            first_line = s + x * '_' + (n - x) * ' '
            second_line = (u + x) * ' ' + '\\' + (n - x - 1) * ' '
            shifted_lines = [u * ' ' + line for line in lines]
            return [first_line, second_line] + shifted_lines, n + u, p + 2, u // 2

        # Two children.
        left, n, p, x = self.left._display_aux()
        right, m, q, y = self.right._display_aux()
        s = '%s' % ((self.player if self.player else 'Bye') + '/' + (str(self.time) if self.time else 'NA'))
        u = len(s)
        first_line = (x + 1) * ' ' + (n - x - 1) * '_' + s + y * '_' + (m - y) * ' '
        second_line = x * ' ' + '/' + (n - x - 1 + u + y) * ' ' + '\\' + (m - y - 1) * ' '
        if p < q:
            left += [n * ' '] * (q - p)
        elif q < p:
            right += [m * ' '] * (p - q)
        zipped_lines = zip(left, right)
        lines = [first_line, second_line] + [a + u * ' ' + b for a, b in zipped_lines]
        return lines, n + m + u, max(p, q) + 2, n + u // 2
        
    

class Bracket:
    def __init__(self, teams, time):
        self.timeout = time
        self.numTeams = len(teams)
        self.numRounds = int(math.ceil(math.log(self.numTeams,2)))
        self.totalNumTeams = int(2**math.ceil(math.log(self.numTeams,2)))
        self.numByes = self.totalNumTeams - self.numTeams
        print('numbyes:', self.numByes)
        self.byeEveryN = 0 if self.numByes == 0 else math.floor((2**(self.numRounds - 1)) / self.numByes)
        self.tree = Tree(None, None, None, None, 1)
        self.generateBracket(teams)
        
    def generateBracket(self, playerlist):
        r = [self.tree]
        games_assigned = 0
        for i in range(self.numRounds):
            r, games_assigned = self.generateRound(r, playerlist, games_assigned)
            
    def generateRound(self, trees, players, games_assigned):
        next_round = []
        for tree in trees:
            if tree.depth == self.numRounds:
                if self.numByes > 0 and games_assigned % self.byeEveryN == 0:
                    player = players.pop(0)
                    tree.left = Tree(None, None, player[0], player[1], tree.depth + 1)
                    tree.right = Tree(None, None, None, None, tree.depth + 1)
                    self.numByes -= 1
                else:
                    player = players.pop(self.numByes)
                    tree.left = Tree(None, None, player[0], player[1], tree.depth + 1)
                    player = players.pop()
                    tree.right = Tree(None, None, player[0], player[1], tree.depth + 1)
                games_assigned += 1
            else:
                tree.left = Tree(None, None, None, None, tree.depth + 1)
                tree.right = Tree(None, None, None, None, tree.depth + 1)
            next_round.append(tree.left)
            next_round.append(tree.right)
        return next_round, games_assigned

    
    def _evalBracket(self, root, level, game): 
        if root is None: 
            return 

        if level > 1: 
            self._evalBracket(root.left, level-1, game) 
            self._evalBracket(root.right, level-1, game)

        elif level == 1 : 
            print(root.left.player, root.right.player)
            win_index, time1, time2 = game(root.left.agent_str, root.right.agent_str, self.timeout)
            if win_index == 1:
                root.player = root.left.player
                root.agent_str = root.left.agent_str
#                 root.time = time1
            elif win_index == 2:
                root.player = root.right.player
                root.agent_str = root.right.agent_str
#                 root.time = time2
            else:
                raise ValueError('Winner was neither 1 or 2')
            root.left.time = time1
            root.right.time = time2

    def evalBracket(self, game): 
        h = self.numRounds
        for i in reversed(range(1, h+1)): 
            self._evalBracket(self.tree, i, game)
            
    def getPlacings(self):
        current_place = 1
        placings = []
        for i in range(self.numRounds + 1):
            sorted_level = sorted(self.tree.get_level_nodes(i), key=lambda x: x[1])
            for player in sorted_level:
                if player[0] not in placings and player[0] is not None:
                    placings.append(player[0])
        return placings
              
    
        
        
    