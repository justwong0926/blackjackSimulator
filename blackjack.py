import math
from splits import SPLITS, SPLIT_DEVIATIONS
from aces import ACE_NUM, STAND_IF_CANT_DOUBLE, ACE_DEVIATIONS
from hard_hands import HARD_HANDS, HARD_DEVIATIONS
from random import randrange

MIN_BET = 10
ACES_SPLIT_LIMIT = 2
SPLIT_LIMIT = 4
HIT_SOFT_SEVENTEEN = True

class Hand:
    def __init__(self, cards, cardsum, soft, split = False, doubled = False):
        self.cards = cards
        self.cardsum = cardsum
        self.soft = soft
        self.split = split
        self.doubled = doubled

class Game:
    def __init__(self, decks = 2, cut = 26, betting_unit = 20, count_to_start_betting_unit = 2):
        self.decks = decks
        self.curr_stack = self.generateStack(decks)
        self.cut = cut
        self.betting_unit = betting_unit
        self.count_to_start_betting_unit = count_to_start_betting_unit
        self.cards_in_play = decks * 52
        self.rounds_played = 0
        self.money_bet = 0
        self.profit = 0
        self.count = 0

    def generateStack(self, decks):
        stack = []
        for _ in range(decks):
            for i in range(2,10):
                for j in range(4):
                    stack.append(i)
            for i in range(16):
                stack.append(10)
            for i in range(4):
                stack.append("A")
    
    def playShoe(self):
        while self.cards_in_play > self.cut:
            self.playHand()
        self.resetShoe()

    def playMoney(self, dollars_to_play):
        while self.money_bet < dollars_to_play:
            self.playShoe()

    def findTrueCount(self):
        # return absolute count for deviations, use rounded for bet sizing
        decks_left = self.cards_in_play // 52
        if self.cards_in_play / 52 >= 0.5:
            decks_left += 1
        else:
            decks_left += 0.5
        return self.count / decks_left

    def findTrueCountIgnoringDealerDown(self, dealer_cards):
        cards_in_play = self.cards_in_play - 1
        count = self.count
        if dealer_cards[1] == 'A' or dealer_cards[1] == 10:
            count -= 1
        elif dealer_cards[1] <= 6:
            count += 1
        decks_left = cards_in_play // 52
        if cards_in_play / 52 >= 0.5:
            decks_left += 1
        else:
            decks_left += 0.5
        return count / decks_left

    def resetShoe(self):
        self.curr_stack = self.generateStack(self.decks)
        self.cards_in_play = self.decks * 52
        self.count = 0
    
    def drawCard(self):
        ind = randrange(len(self.curr_stack))
        self.cards_in_play -= 1
        card = self.cards_in_play.pop(ind)
        if card == 'A' or card == 10:
            self.count -= 1
        elif card <= 6:
            self.count -= 1

        return card

    def determineBet(self):
        true_count = math.floor(self.findTrueCount())
        if true_count < self.count_to_start_betting_unit:
            return MIN_BET
        else:
            return (true_count - count_to_start_betting_unit + 1) * betting_unit

    def determineValue(self, card):
        if card == 'A':
            return 11
        else:
            return card

    def determineLowValue(self,card):
        if card == 'A':
            return 1
        else:
            return card

    def isBlackjack(self, card1, card2):
        if card1 == 'A' and card2 == 10:
            return True
        elif card1 == 10 and card2 == 'A':
            return True
        return False

    def dealerCheckBlackjack(self, dealer_hand, player_first_card, player_second_card, player_bet):
        insurance = self.findTrueCount() >= 3 and dealer_hand.cards[0] == 'A'
        dealer_second_card = drawCard()

        if insurance:
            if self.isBlackjack(dealer_hand.cards[0], dealer_second_card):
                if self.isBlackjack(player_first_card, player_second_card):
                    # even money
                    self.rounds_played += 1
                    self.profit += player_bet
                    self.money_bet += player_bet
                else:
                    # insurance won, bet lost, no net gain or loss
                    self.rounds_played += 1
                    self.money_bet += player_bet
                return True
            else:
                dealer_hand.cards.append(dealer_second_card)
                dealer_hand.cardsum += self.determineValue(dealer_second_card)
                if dealer_second_card == 'A':
                    dealer_hand.soft = True
                return False
        if self.isBlackjack(dealer_hand.cards[0], dealer_second_card):
            if self.isBlackjack(player_first_card, player_second_card):
                # both blackjack
                self.rounds_played += 1
                self.money_bet += player_bet
            else:
                # bet insta loss
                self.rounds_played += 1
                self.profit -= player_bet
                self.money_bet += player_bet
            return True
        else:
            dealer_hand.cards.append(dealer_second_card)
            dealer_hand.cardsum += self.determineValue(dealer_second_card)
            if dealer_second_card == 'A':
                dealer_hand.soft = True
            return False

    def shouldSplit(self, num, dealer_num):
        if (num, dealer_num) in SPLITS:
            return SPLITS[(num, dealer_num)]
        else:
            deviation = SPLIT_DEVIATIONS[(num,dealer_num)]
            true_count = self.findTrueCount()
            if dealer_num == 'A' or dealer_num == 10:
                true_count = self.findTrueCountIgnoringDealerDown()
            if true_count >= deviation[0]:
                return deviation[1]
            else:
                return not deviation[1]
            

    def trySplits(self, player_hands, dealer_num):
        for player_hand in player_hands:
            if player_hand.cards[0] == player_hand.cards[1] and len(player_hand.cards) == 2 and shouldSplit(player_hand.cards[0], dealer_num):
                card = player_hand.cards[0]
                under_limit = len(player_hands) < SPLIT_LIMIT
                if player_hand[0] == 'A':
                    under_limit = len(player_hands) < ACES_SPLIT_LIMIT
                if under_limit:
                    player_hands.append(Hand([card], self.determineValue(card), False, True))
                    player_hand = Hand([card], self.determineValue(card), False, True)
                return True
        return False


    def dealToSplitHands(self, player_hands):
        for player_hand in player_hands:
            if len(player_hand.cards) == 1:
                dealt_card = drawCard()
                player_hand.cards.append(dealt_card)
                player_hand.cardsum += determineValue(dealt_card)
                if dealt_card == 'A':
                    player_hand.soft = True

    def executeHardHandHit(self,player_hand,dealer_num):
        new_card = self.drawCard()
        player_hand.cards.append(new_card)
        player_hand.cardsum += self.determineValue(new_card)
        if new_card == 'A':
            if player_hand.cardsum > 21:
                # eg 12 and hit an ace
                player_hand.cardsum -= 10
                return False
            else:
                # eg (2,3) and hit an ace, becomes A, 5
                player_hand.soft = True
                self.executeSoftHand(player_hand,dealer_num)
                return True




    def executeHardHand(self, player_hand, dealer_num):
        decision = None
        while True:
            if (player_hand.cardsum, dealer_num) in HARD_HANDS:
                decision = HARD_HANDS[(player_hand.cardsum, dealer_num)]
            else:
                true_count = self.findTrueCount()
                if dealer_num == 'A' or dealer_num == 10:
                    true_count = self.findTrueCountIgnoringDealerDown()
                decisions = HARD_DEVIATIONS[(player_hand.cardsum, dealer_num)]
                if true_count >= decisions[0]:
                    decision = decisions[1]
                else:
                    decision = decisions[2]
            
            if decision == 'D':
                if len(player_hand) > 2:
                    self.executeHardHandHit(player_hand, dealer_num)
                else:
                    new_card = self.drawCard()
                    player_hand.cards.append(new_card)
                    player_hand.cardsum += self.determineValue(new_card)
                    player_hand.doubled = True
                    if player_hand.cardsum > 21:
                        player_hand.cardsum -= 10
                    break
            elif decision == 'S':
                break
            else:
                should_break = self.executeHardHandHit(player_hand, dealer_num)
                if should_break:
                    break


    def executeSoftHandHit(self, player_hand, dealer_num):
        new_card = self.drawCard()
        player_hand.cards.append(new_card)
        player_hand.cardsum += self.determineLowValue(new_card)
        if player_hand.cardsum > 21:
            player_hand.cardsum -= 10
            player_hand.soft = False
            self.executeHardHand(player_hand, dealer_num)
            return True
        else:
            return False

    def executeSoftHand(self, player_hand, dealer_num):
        decision = None
        while True:
            if (player_hand.cardsum - 11, dealer_num) in ACE_NUM:
                decision = ACE_NUM[(player_hand.cardsum - 11, dealer_num)]
            else:
                true_count = self.findTrueCount()
                if dealer_num == 'A' or dealer_num == 10:
                    true_count = self.findTrueCountIgnoringDealerDown()
                decisions = ACE_DEVIATIONS[(player_hand.cardsum - 11, dealer_num)]
                if true_count >= decisions[0]:
                    decision = decisions[1]
                else:
                    decision = decisions[2]
            
            if decision == 'S':
                break
            elif decision == 'H':
                should_break = self.executeSoftHandHit(player_hand, dealer_num)
                if should_break:
                    break
            # double
            else:
                if len(player_hand) > 2:
                    # cant double
                    self.executeSoftHandHit(player_hand, dealer_num)
                else:
                    new_card = self.drawCard()
                    player_hand.cards.append(new_card)
                    player_hand.cardsum += self.determineLowValue(new_card)
                    player_hand.doubled = True
                    if player_hand.cardsum > 21:
                        player_hand.cardsum -= 10
                        player_hand.soft = False
                    break


    def makeDecision(self, player_hand, dealer_num):
        # can't hit on split ace
        if player_hand.cards[0] == 'A' and player_hand.split == True:
            return
        if player_hand.soft:
            self.executeSoftHand(player_hand, dealer_num)
        else:
            self.executeHardHand(player_hand, dealer_num)

            
    def drawDealerCard(self, dealer_hand):
        new_card = self.drawCard()
        dealer_hand.cards.append(new_card)
        dealer_hand.cardsum += self.determineValue(new_card)
        if dealer_hand.soft:
            # ace 3

            if dealer_hand.cardsum > 21:
                dealer_hand.cardsum -= 10
                if new_card != 'A':
                    dealer_hand.soft = False
        else:
            if new_card == 'A':
                # 13 then hits ace
                if dealer_hand.cardsum > 21:
                    dealer_hand.cardsum -= 10
                else:
                    # 7 then hits ace
                    dealer_hand.soft = True
            



    def playHand(self):
        player_bet = self.determineBet()
        # dealer first card
        dealer_face_up = self.drawCard()
        dealer_soft = dealer_face_up == 'A'
        dealer_curr_sum = dealer_face_up
        if dealer_face_up == 'A':
            dealer_curr_sum = 11
        dealer_hand = Hand([dealer_face_up], dealer_curr_sum, dealer_soft)

        # deal player cards
        player_hands = []
        player_first_card = self.drawCard()
        player_second_card = self.drawCard()
        player_hands.append(Hand([player_first_card, player_second_card]))

        if dealer_hand.cardsum == 11 or dealer_hand.cardsum == 10:
            # dealt dealer cards
            if self.dealerCheckBlackjack(dealer_hand, player_first_card, player_second_car, player_bet):
                return

        # check if split before constructing hands
        while True:
            if trySplits(player_hands, dealer_face_up):
                dealToSplitHands()
            else:
                break

        # now all hands have 2 cards, time to make playing decisions
        self.rounds_played += 1
        for player_hand in player_hands:
            if self.isBlackjack(player_hand.cards[0], player_hand.cards[1]):
                if player_hand.split:
                    self.profit += player_bet
                    self.money_bet += player_bet
                else:
                    self.profit += player_bet * 1.5
                    self.money_bet += player_bet
            else:
                self.makeDecision(player_hand, dealer_face_up)

        player_busts = 0
        for player_hand in player_hands:
            if player_hand.cardsum > 21:
                player_busts += 1
        
        has_nonbust = player_busts < len(player_hands)

        # execute dealer logic if necessary
        if not has_nonbust:
            if len(dealer_hand) == 1:
                drawCard()
            return
        else:
            while True:
                if dealer_hand.cardsum < 17:
                    self.drawDealerCard(dealer_hand)
                elif dealer_hand.cardsum > 17:
                    break
                elif HIT_SOFT_SEVENTEEN:
                    self.drawDealerCard(dealer_hand)
                else:
                    break

        
blackjack = Game()
blackjack.playShoe()