from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
from otree.api import safe_json

##############################################
class InformationPage(Page):
    def is_displayed(self):
        return (self.subsession.round_number == 1)

    def vars_for_template(self):
        # At the beginning of this first page, set the participant's URL so that he can stop and come back later
        parti = self.request.build_absolute_uri(self.player.participant._start_url())
        self.request.session["otree"] = parti
        self.request.session.set_expiry(18000) # ???
        return {
            'with_prime': {'NoPrime': 'NoPrime',
                           'WithPrime': 'WithPrime',
                           'NoPrime_NoEcoGeste': 'NoPrime'}[self.player.role()],
            'with_ecogeste': {'NoPrime': 'WithEcoGeste',
                              'WithPrime': 'WithEcoGeste',
                              'NoPrime_NoEcoGeste': 'NoEcoGeste'}[self.player.role()],
        }

    def before_next_page(self): #??? For tests, as the next WaitScreen is disabled for the tests
        self.subsession.start_session()


class InfoReadingWaitScreen(Page):
    def is_displayed(self):
        return ((self.subsession.round_number == 1)
                & (self.subsession.timer_elapsed() == False))

    def before_next_page(self):
        self.subsession.start_session()


##############################################
class TasksPage(Page):
    form_model = models.Player
    form_fields = ['nb_tasks_thisperiod']

    def vars_for_template(self):
        return {
            'endingPxWidth': Constants.c_endingPxWidth[self.session.config['treatment']],
            'timer_left_in_ms': safe_json((self.subsession.timer_time_left() + 1) * 1000),
        }

    def is_displayed(self):
        return ((self.participant.vars["stop_pressed"] == 0)
                &(self.subsession.timer_elapsed() == False))

    def before_next_page(self):
        self.player.compute_intermediate_results()


class RoundRecapPage(Page):
    def is_displayed(self):
        return ((self.round_number%Constants.c_feedback_modulo_per_period==0)
                &(self.participant.vars["stop_pressed"] == 0)
                &(self.subsession.timer_elapsed() == False))

    def vars_for_template(self):
        return {
            'with_prime': {'NoPrime': 'NoPrime',
                           'WithPrime': 'WithPrime',
                           'NoPrime_NoEcoGeste': 'NoPrime'}[self.player.role()],
            'with_ecogeste': {'NoPrime': 'WithEcoGeste',
                              'WithPrime': 'WithEcoGeste',
                              'NoPrime_NoEcoGeste': 'NoEcoGeste'}[self.player.role()],
            'timer_left_in_ms': safe_json((self.subsession.timer_time_left() + 1) * 1000),
        }


class ContinuePage(Page):
    form_model = models.Player
    form_fields = ['stop_pressed']

    def is_displayed(self):
        return ((self.participant.vars["stop_pressed"] == 0)
                &(self.subsession.timer_elapsed() == False))

    def vars_for_template(self):
        return {
            'timer_left_in_ms': safe_json((self.subsession.timer_time_left() + 1) * 1000),
        }

    def before_next_page(self):
        self.player.set_stop_flag()


##############################################
class FinalRecapPage(Page):
    def is_displayed(self):
        return(self.player.participant.vars["whole_XP_done"]==False)\
                  &((self.participant.vars["stop_pressed"] == 1)
                    |(self.subsession.timer_elapsed()))

    def vars_for_template(self):
        # Compute all the final results
        self.player.compute_final_results_payoff()
        return {
            'with_prime': {'NoPrime': 'NoPrime',
                           'WithPrime': 'WithPrime',
                           'NoPrime_NoEcoGeste': 'NoPrime'}[self.player.role()],
            'with_ecogeste': {'NoPrime': 'WithEcoGeste',
                              'WithPrime': 'WithEcoGeste',
                              'NoPrime_NoEcoGeste': 'NoEcoGeste'}[self.player.role()],
            'timer_elapsed': {False: 0, True: 1}[self.subsession.timer_elapsed()],
        }

    def before_next_page(self):
        # Once the player has seen this page he can leave onto the survey
        self.player.participant.vars["whole_XP_done"] = True


##############################################
class DrawingPage(Page):
    def is_displayed(self):
        # This page is to be displayed only for the live-tree treatment
        return(self.session.config['treatment'] == 10)\
              &(self.subsession.round_number==Constants.num_rounds)

    def vars_for_template(self):
        self.subsession.make_drawing()
        return {
            'lost_or_won': {True: 'won', False: 'lost'}[self.player.winning_player],
            'payoff_total_en_euros': self.participant.payoff_plus_participation_fee(),
        }


##############################################
page_sequence = [
    InformationPage,
    #??? Disabled For Tests: InfoReadingWaitScreen,
    TasksPage,
    RoundRecapPage,
    ContinuePage,
    FinalRecapPage,
    DrawingPage,
]
