from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import time
from random import randint


author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'elithis'
    players_per_group = None
    num_rounds = 70

    c_max_nb_tasks = 50
    c_startingPxWidth = 30
    c_startingPxWidth_ForCSS = str(c_startingPxWidth) + "px"
    c_endingPxWidth = {1: 5,
                       2: 5,
                       10: c_startingPxWidth}

    c_feedback_modulo_per_period = 1

    c_gain_per_period = 50
    c_bonus_tabl = [(0, 0),
                    (20, 146),
                    (25, 292),
                    (30, 438),
                    (35, 580),
                    (num_rounds+1, 580)]
    c_ecogeste_factor = {1: 0.05,
                         2: 0.05,
                         10: 1}


class Subsession(BaseSubsession):
    winning_playerID = models.PositiveIntegerField(initial=9999)

    def make_drawing(self):
        if self.winning_playerID == 9999:
            # Make the drawing only once
            self.winning_playerID = 2 * randint(1, int(len(self.get_players())/2) ) - 1
            self.get_players()[self.winning_playerID - 1].winning_player = True

    def start_session(self):
        # To start only 1 timer, check the status of the session
        if self.session.vars["sessionState"] == "pending":
            self.session.vars["start_time"] = time.time()
            self.session.vars["sessionState"] = "running"

    def before_session_starts(self):
        # Set the state of the session. Normal flow = "waiting", "running", "stopped"
        ofi = open("./redirect/sessionState.txt", "w")
        ofi.write("running")
        ofi.close()
        for p in self.get_players():
            p.treatment = {'NoPrime': 'NoPrime', 'WithPrime': 'WithPrime', 'NoPrime_NoEcoGeste': 'NoPrime_NoEcoGeste'}[p.role()]
            p.participant.vars["stop_pressed"] = 0
            p.participant.vars["whole_XP_done"] = False
        if self.round_number == 1 :
            self.session.vars["sessionState"] = "pending"

    def timer_elapsed(self):
        if time.time() > (self.session.vars["start_time"] + self.session.config['session_time_in_sec']):
            self.session.vars["sessionState"] = "finished"
            return(True)
        else:
            return (False)

    def timer_time_left(self):
        return (self.session.vars["start_time"] + self.session.config['session_time_in_sec']) - time.time()


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    treatment = models.CharField(initial="Not initialised")
    winning_player = models.BooleanField(doc="Winning player for the live-tree treatment",
                                         initial=False)
    stop_pressed = models.PositiveIntegerField(initial=0)
    period_played = models.BooleanField(doc="Last period reached by the player",
                                        initial=False)
    last_period = models.BooleanField(doc="Last period reached by the player",
                                      initial=False)

    nb_tasks_thisperiod = models.PositiveIntegerField(doc="Number of tasks achieved by the player during this round",
                                                      initial=0,
                                                      max=Constants.c_max_nb_tasks)
    period_completed = models.PositiveIntegerField(choices=[0,1],
                                                   initial=0)
    total_tasks_done = models.PositiveIntegerField(doc="Number of tasks achieved by the player during all rounds",
                                                   initial=9999)
    total_periodcompleted = models.PositiveIntegerField(initial=9999)
    total_gain = models.PositiveIntegerField(doc="Total gain during all rounds",
                                             initial=0)
    total_bonus = models.FloatField(doc="Total of bonus during all rounds",
                                    initial=0)
    total_gain_bonus = models.FloatField(doc="Total gain+bonus during all rounds",
                                         initial=0)
    payoff_euros = models.FloatField(doc="Gain in euros for this player",
                                     initial=0)
    total_ecogeste = models.FloatField(doc="Gain for EcoGeste thanks to this player",
                                       initial=0)
    total_ecogeste_euros = models.FloatField(doc="Gain for EcoGeste thanks to this player",
                                             initial=0)

    def compute_total_bonus(self):
        if self.role()=='WithPrime':
            i = 0
            while self.total_periodcompleted >= Constants.c_bonus_tabl[i + 1][0]:
                i += 1
            self.total_bonus = Constants.c_bonus_tabl[i][1]
        elif (self.role()=='NoPrime') | (self.role()=='NoPrime_NoEcoGeste'):
            self.total_bonus = 0

    def compute_total_ecogeste(self):
        if self.role() == 'NoPrime_NoEcoGeste':
            self.total_ecogeste = 0
        else:
            self.total_ecogeste = self.total_gain_bonus * Constants.c_ecogeste_factor[self.session.config['treatment']]

    def compute_intermediate_results(self):
        ###############################
        # Set this period as "played"
        self.period_played = True
        ###############################
        # Compute the results for this period
        # The nb_tasks_thisperiod is already set by the TasksPage itself. Start from there.
        if self.nb_tasks_thisperiod == Constants.c_max_nb_tasks: self.period_completed = True
        ###############################
        # Compute the intermediate results since the beginning
        self.total_tasks_done = sum([p.nb_tasks_thisperiod for p in self.in_all_rounds()])
        self.total_periodcompleted = sum([p.period_completed for p in self.in_all_rounds()])
        self.total_gain = self.total_periodcompleted * Constants.c_gain_per_period
        self.compute_total_bonus()
        self.total_gain_bonus = self.total_gain + self.total_bonus
        self.compute_total_ecogeste()

    def set_stop_flag(self):
        ###############################
        #  Set the "stop" flag
        if self.participant.vars["stop_pressed"] == 0:
            self.participant.vars["stop_pressed"] = self.stop_pressed

    def compute_final_results_payoff(self):
        ###############################
        #  Set this period as the "last period"
        self.last_period = True
        ###############################
        # Set the payoffs in euros
        self.payoff = self.total_gain_bonus
        self.payoff_euros = self.total_gain_bonus * float(self.session.config['real_world_currency_per_point'])\
                      + self.session.config['participation_fee']
        self.total_ecogeste_euros = self.payoff_euros * Constants.c_ecogeste_factor[self.session.config['treatment']]

    def role(self):
        try:
            if self.session.config['treatment'] == 1:
                return('NoPrime')
            elif self.session.config['treatment'] == 2:
                return('WithPrime')
            elif self.session.config['treatment'] == 10:
                return {0: 'NoPrime_NoEcoGeste', 1: 'NoPrime'}[(self.id_in_group)%2]
        except ValueError:
            print("Unknown treatment, can't determine role of the player")
