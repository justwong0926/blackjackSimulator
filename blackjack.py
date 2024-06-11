import math
import random
from h17_counting import H17_HARD_TOTALS, H17_HARD_TOTAL_DEVIATIONS, H17_SOFT_TOTALS, H17_SOFT_TOTAL_DEVIATIONS, H17_SOFT_TOTAL_STAND_WHEN_CANT_DOUBLE, H17_SPLITS, H17_SPLIT_DEVIATIONS
from basic_strategy import BS_HARD_TOTALS, BS_SOFT_TOTALS, BS_SOFT_TOTAL_STAND_WHEN_CANT_DOUBLE, BS_SPLITS
from random import randrange
import sys, os

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
    def __init__(self, playstyle = "H17", decks = 2, cut = 26, betting_unit = 20, count_to_start_betting_unit = 2, max_bet_unit = 10, flat_bet = False):
        self.hard_totals = H17_HARD_TOTALS
        self.hard_total_deviations = H17_HARD_TOTAL_DEVIATIONS
        self.soft_totals = H17_SOFT_TOTALS
        self.soft_total_deviations = H17_SOFT_TOTAL_DEVIATIONS
        self.soft_total_stand_when_cant_double = H17_SOFT_TOTAL_STAND_WHEN_CANT_DOUBLE
        self.splits = H17_SPLITS
        self.split_deviations = H17_SPLIT_DEVIATIONS
        if playstyle != "H17":
            self.hard_totals = BS_HARD_TOTALS
            self.soft_totals = BS_SOFT_TOTALS
            self.soft_total_stand_when_cant_double = BS_SOFT_TOTAL_STAND_WHEN_CANT_DOUBLE
            self.splits = BS_SPLITS


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
        self.max_bet_unit = max_bet_unit
        self.flat_bet = flat_bet


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
        random.shuffle(stack)
        return stack
    
    def playShoe(self):
        while self.cards_in_play > self.cut:
            self.playHand()
        print("Profit: ", self.profit)
        print("Money bet: ", self.money_bet)
        self.resetShoe()

    def playMoney(self, dollars_to_play):
        while self.money_bet < dollars_to_play:
            self.playShoe()

    def playUntil(self, starting, lower_bound, upper_bound):
        while self.profit + starting > lower_bound and self.profit + starting < upper_bound:
            self.playShoe()
        if self.profit < 0:
            # false is lose
            return False
        else:
            return True

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
            count += 1
        elif dealer_cards[1] <= 6:
            count -= 1
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
        self.cards_in_play -= 1
        card = self.curr_stack.pop()
        if card == 'A' or card == 10:
            self.count -= 1
        elif card <= 6:
            self.count += 1

        return card

    def determineBet(self):
        if self.flat_bet:
            return MIN_BET
        true_count = math.floor(self.findTrueCount())
        print("True count: ", true_count, self.count)
        if true_count < self.count_to_start_betting_unit:
            return MIN_BET
        else:
            return (true_count - self.count_to_start_betting_unit + 1) * self.betting_unit

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
        dealer_second_card = self.drawCard()
        print("Dealer second card", str(dealer_second_card))

        if insurance:
            self.money_bet += player_bet * 0.5
            if self.isBlackjack(dealer_hand.cards[0], dealer_second_card):
                if self.isBlackjack(player_first_card, player_second_card):
                    # even money
                    self.rounds_played += 1
                    self.profit += player_bet
                    self.money_bet += player_bet
                    print("Dealer blackjack, won even money: $", player_bet)
                else:
                    # insurance won, bet lost, no net gain or loss
                    self.rounds_played += 1
                    self.money_bet += player_bet
                    print("Dealer blackjack, won insurance: $0")
                return True
            else:
                # lost insurance
                self.profit -= player_bet * 0.5
                dealer_hand.cards.append(dealer_second_card)
                dealer_hand.cardsum += self.determineValue(dealer_second_card)
                if dealer_second_card == 'A':
                    dealer_hand.soft = True
                return False
        elif self.isBlackjack(dealer_hand.cards[0], dealer_second_card):
            if self.isBlackjack(player_first_card, player_second_card):
                # both blackjack
                self.rounds_played += 1
                self.money_bet += player_bet
                print("Dealer blackjack, player blackjack: $0")
            else:
                # bet insta loss
                self.rounds_played += 1
                self.profit -= player_bet
                self.money_bet += player_bet
                print("Dealer blackjack, lost: $", player_bet)
            return True
        else:
            dealer_hand.cards.append(dealer_second_card)
            dealer_hand.cardsum += self.determineValue(dealer_second_card)
            if dealer_second_card == 'A':
                dealer_hand.soft = True
            return False

    def shouldSplit(self, num, dealer_hand):
        dealer_face_up = dealer_hand.cards[0]
        if (num, dealer_face_up) in self.splits:
            return self.splits[(num, dealer_face_up)]
        else:
            deviation = self.split_deviations[(num,dealer_face_up)]
            true_count = self.findTrueCount()
            if dealer_face_up == 'A' or dealer_face_up == 10:
                true_count = self.findTrueCountIgnoringDealerDown(dealer_hand.cards)
            if true_count >= deviation[0]:
                return deviation[1]
            else:
                return not deviation[1]
            

    def trySplits(self, player_hands, dealer_hand):
        dealer_face_up = dealer_hand.cards[0]
        length = len(player_hands)
        for i in range(length):
            player_hand = player_hands[i]
            if player_hand.cards[0] == player_hand.cards[1] and len(player_hand.cards) == 2 and self.shouldSplit(player_hand.cards[0], dealer_hand):
                card = player_hand.cards[0]
                under_limit = len(player_hands) < SPLIT_LIMIT
                if player_hand.cards[0] == 'A':
                    under_limit = len(player_hands) < ACES_SPLIT_LIMIT
                    print("Split aces", len(player_hands), under_limit, player_hand.cards)
                if under_limit:
                    print("Splitting ", card)
                    player_hands.append(Hand([card], self.determineValue(card), False, True))
                    player_hands[i] = Hand([card], self.determineValue(card), False, True)
                    return True
                else:
                    return False
        return False


    def dealToSplitHands(self, player_hands):
        for player_hand in player_hands:
            if len(player_hand.cards) == 1:
                dealt_card = self.drawCard()
                print("Dealing to split hand: ", dealt_card)
                player_hand.cards.append(dealt_card)
                player_hand.cardsum += self.determineValue(dealt_card)
                if dealt_card == 'A':
                    player_hand.soft = True

    def executeHardHandHit(self,player_hand, dealer_hand):
        new_card = self.drawCard()
        print("Hit, got ", str(new_card))
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
                self.executeSoftHand(player_hand, dealer_hand)
                return True
        else:
            if player_hand.cardsum > 21:
                return True
            else:
                return False




    def executeHardHand(self, player_hand, dealer_hand):
        decision = None
        dealer_num = dealer_hand.cards[0]
        while True:
            if (player_hand.cardsum, dealer_num) in self.hard_totals:
                decision = self.hard_totals[(player_hand.cardsum, dealer_num)]
            else:
                true_count = self.findTrueCount()
                if dealer_num == 'A' or dealer_num == 10:
                    true_count = self.findTrueCountIgnoringDealerDown(dealer_hand.cards)
                decisions = self.hard_total_deviations[(player_hand.cardsum, dealer_num)]
                if true_count >= decisions[0]:
                    decision = decisions[1]
                else:
                    decision = decisions[2]
            
            if decision == 'D':
                if len(player_hand.cards) > 2:
                    self.executeHardHandHit(player_hand, dealer_hand)
                else:
                    new_card = self.drawCard()
                    print("Doubled, drew a ", str(new_card))
                    player_hand.cards.append(new_card)
                    player_hand.cardsum += self.determineValue(new_card)
                    player_hand.doubled = True
                    if player_hand.cardsum > 21:
                        player_hand.cardsum -= 10
                    break
            elif decision == 'S':
                break
            else:
                should_break = self.executeHardHandHit(player_hand, dealer_hand)
                if should_break:
                    break


    def executeSoftHandHit(self, player_hand, dealer_hand):
        new_card = self.drawCard()
        print("Hit, got ", str(new_card))
        player_hand.cards.append(new_card)
        player_hand.cardsum += self.determineLowValue(new_card)
        if player_hand.cardsum > 21:
            player_hand.cardsum -= 10
            player_hand.soft = False
            self.executeHardHand(player_hand, dealer_hand)
            return True
        else:
            return False

    def executeSoftHand(self, player_hand, dealer_hand):
        if 'A' == player_hand.cards[0] and player_hand.split:
            return
        decision = None
        dealer_num = dealer_hand.cards[0]
        while True:
            if (player_hand.cardsum - 11, dealer_num) in self.soft_totals:
                decision = self.soft_totals[(player_hand.cardsum - 11, dealer_num)]
            else:
                true_count = self.findTrueCount()
                if dealer_num == 'A' or dealer_num == 10:
                    true_count = self.findTrueCountIgnoringDealerDown(dealer_hand.cards)
                decisions = self.soft_total_deviations[(player_hand.cardsum - 11, dealer_num)]
                if true_count >= decisions[0]:
                    decision = decisions[1]
                else:
                    decision = decisions[2]
            
            if decision == 'S':
                break
            elif decision == 'H':
                should_break = self.executeSoftHandHit(player_hand, dealer_hand)
                if should_break:
                    break
            # double
            else:
                if len(player_hand.cards) > 2:
                    if (player_hand.cardsum - 11, dealer_num) in self.soft_total_stand_when_cant_double:
                        break
                    # cant double

                    should_break = self.executeSoftHandHit(player_hand, dealer_hand)
                    if should_break:
                        break
                else:
                    new_card = self.drawCard()
                    print("Doubled, drew a ", str(new_card))
                    player_hand.cards.append(new_card)
                    player_hand.cardsum += self.determineLowValue(new_card)
                    player_hand.doubled = True
                    if player_hand.cardsum > 21:
                        player_hand.cardsum -= 10
                        player_hand.soft = False
                    break


    def makeDecision(self, player_hand, dealer_hand):
        # can't hit on split ace
        if player_hand.cards[0] == 'A' and player_hand.split == True:
            return
        if player_hand.soft:
            self.executeSoftHand(player_hand, dealer_hand)
        else:
            self.executeHardHand(player_hand, dealer_hand)

            
    def drawDealerCard(self, dealer_hand):
        new_card = self.drawCard()
        print("Dealer hits ", str(new_card))
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
            

    def createHand(self, card1, card2, split = False):
        cardsum = self.determineValue(card1) + self.determineValue(card2)
        soft = False
        if card1 == 'A' and card2 == 'A':
            cardsum -= 10
        if card1 == 'A' or card2 == 'A':
            soft = True
        return Hand([card1,card2], cardsum, soft, split)

    def playHand(self):
        player_bet = self.determineBet()
        # dealer first card
        dealer_face_up = self.drawCard()
        print("Dealer first card:", str(dealer_face_up))
        dealer_soft = dealer_face_up == 'A'
        dealer_curr_sum = dealer_face_up
        if dealer_face_up == 'A':
            dealer_curr_sum = 11
        dealer_hand = Hand([dealer_face_up], dealer_curr_sum, dealer_soft)

        # deal player cards
        player_hands = []
        player_first_card = self.drawCard()
        player_second_card = self.drawCard()
        print("Player first card:", str(player_first_card))
        print("Player second card:", str(player_second_card))
        player_hands.append(self.createHand(player_first_card, player_second_card))

        if dealer_hand.cardsum == 11 or dealer_hand.cardsum == 10:
            # dealt dealer cards
            if self.dealerCheckBlackjack(dealer_hand, player_first_card, player_second_card, player_bet):
                print("HAND OVER")
                print("")
                return

        # check if split before constructing hands
        while True:
            if self.trySplits(player_hands, dealer_hand):
                self.dealToSplitHands(player_hands)
            else:
                break

        # now all hands have 2 cards, time to make playing decisions
        self.rounds_played += 1
        for player_hand in player_hands:
            if self.isBlackjack(player_hand.cards[0], player_hand.cards[1]):
                if player_hand.split:
                    self.profit += player_bet
                    self.money_bet += player_bet
                    print("Player won: $", player_bet)
                else:
                    self.profit += player_bet * 1.5
                    self.money_bet += player_bet
                    print("Player won: $", player_bet * 1.5)
            else:
                self.makeDecision(player_hand, dealer_hand)

        player_busts = 0
        for player_hand in player_hands:
            if player_hand.cardsum > 21:
                player_busts += 1
        
        has_nonbust = player_busts < len(player_hands)

        # execute dealer logic if necessary
        if not has_nonbust:
            if len(dealer_hand.cards) == 1:
                new_card = self.drawCard()
                print("Player all hands busted, but dealer's face down card was", str(new_card))
            print("All hands busted, lost: $", player_bet * len(player_hands))
            
            self.profit -= player_bet * len(player_hands)
            self.money_bet += player_bet * len(player_hands)
            for player_hand in player_hands:
                if player_hand.doubled:
                    print("Lost more on bust because doubled: $", player_bet)
                    self.profit -= player_bet
                    self.money_bet += player_bet
            print("HAND OVER")
            print("")
            return
        else:
            while True:
                if dealer_hand.cardsum < 17:
                    self.drawDealerCard(dealer_hand)
                elif dealer_hand.cardsum > 17:
                    break
                elif HIT_SOFT_SEVENTEEN and dealer_hand.soft:
                    self.drawDealerCard(dealer_hand)
                else:
                    break

        # compare hands
        for player_hand in player_hands:
            if self.isBlackjack(player_hand.cards[0], player_hand.cards[1]):
                continue
            double_multiplier = 1
            self.money_bet += player_bet
            if player_hand.doubled:
                double_multiplier = 2
                self.money_bet += player_bet
            if player_hand.cardsum > 21:
                # player bust
                self.profit -= player_bet * double_multiplier
                print("Player lost: $", player_bet * double_multiplier)
            elif dealer_hand.cardsum > 21:
                # dealer bust
                self.profit += player_bet * double_multiplier
                print("Player won: $", player_bet * double_multiplier)
            elif dealer_hand.cardsum > player_hand.cardsum:
                self.profit -= player_bet * double_multiplier
                print("Player lost: $", player_bet * double_multiplier)
            elif dealer_hand.cardsum < player_hand.cardsum:
                self.profit += player_bet * double_multiplier
                print("Player won: $", player_bet * double_multiplier)
            # do nothing if push
        print("HAND OVER")
        print("")


'''
BETTING_AMOUNT = 10000000

profit = 0
simulations_ran = 20
for i in range(simulations_ran):
    blackjack = Game(playstyle = "BS", decks = 2, cut=26, flat_bet = True)
    # comment this line out for prints
    sys.stdout = open(os.devnull, 'w')
    blackjack.playMoney(BETTING_AMOUNT)
    sys.stdout = sys.__stdout__
    profit += blackjack.profit
    print(blackjack.profit, blackjack.rounds_played)
print("In this simulation, the average casino edge is: ", (-profit / BETTING_AMOUNT / simulations_ran) * 100, "%")
'''

DOUBLE_OR_NOTHING_TRIES = 1000
wins = 0
rounds_played = 0
for i in range(DOUBLE_OR_NOTHING_TRIES):
    blackjack = Game(playstyle = "BS", decks = 2, cut = 26, flat_bet = True)
    # comment this line out for prints
    sys.stdout = open(os.devnull, 'w')
    result = blackjack.playUntil(2000, 0, 4000)
    sys.stdout = sys.__stdout__
    rounds_played += blackjack.rounds_played
    if result:
        wins += 1
    
print(wins, " wins out of ", DOUBLE_OR_NOTHING_TRIES)
print("Rounds played on average: ", rounds_played / DOUBLE_OR_NOTHING_TRIES)
