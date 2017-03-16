from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

from otree.api import Currency as c, currency_range
from otree.api import SubmissionMustFail
from . import views
from ._builtin import Bot
from .models import Constants
from random import randint
import time

class PlayerBot(Bot):

    def play_round(self):
        assert self.player.treatment == self.player.role()

        # Page InformationPage
        if self.subsession.round_number == 1:
            if self.player.treatment == 'WithPrime':
                assert 'Vous pouvez aussi obtenir une prime (quatre niveaux de prime)' in self.html
            elif self.player.treatment == 'NoPrime':
                assert 'une rémunération de 100 Ecus. Une fraction de 5' in self.html
            if self.player.role() == 'WithPrime':
                assert 'Vous pouvez aussi obtenir une prime (quatre niveaux de prime)' in self.html
            elif self.player.role() == 'NoPrime':
                assert 'une rémunération de 100 Ecus. Une fraction de 5' in self.html
            yield (views.InformationPage)

        # Page TasksPage
        if((self.participant.vars["stop_pressed"] == 0)
               &(self.subsession.timer_elapsed()==False)):
            yield (views.TasksPage, {'nb_tasks_thisperiod': Constants.c_max_nb_tasks})

        # Page RoundRecapPage
        if ((self.subsession.round_number%Constants.c_feedback_modulo_per_period==0)
                &(self.participant.vars["stop_pressed"] == 0)
                &(self.subsession.timer_elapsed()==False)):
            yield (views.RoundRecapPage)

        # Page ContinuePage
        if ((self.participant.vars["stop_pressed"] == 0)
                &(self.subsession.timer_elapsed()==False)):
            if (((self.subsession.round_number == 7)
                    &(self.player.id_in_group==3))
                    |((self.subsession.round_number == 7)
                          &(self.player.id_in_group==7))
                    |((self.subsession.round_number == 15)
                          & (self.player.id_in_group == 12))):
                yield (views.ContinuePage, {'stop_pressed': 1})
            else:
                yield (views.ContinuePage, {'stop_pressed': randint(0,1)})

        # Page FinalRecapPage
        if (self.player.participant.vars["whole_XP_done"]==False)\
                &((self.participant.vars["stop_pressed"] == 1)
                      |(self.subsession.timer_elapsed())):
            if self.player.treatment == 'WithPrime':
                assert 'ajoute un bonus de' in self.html
            elif self.player.treatment == 'NoPrime':
                assert 'ajoute un bonus de' not in self.html
            if self.player.role() == 'WithPrime':
                assert 'ajoute un bonus de' in self.html
            elif self.player.role() == 'NoPrime':
                assert 'ajoute un bonus de' not in self.html
            yield (views.FinalRecapPage)

        # Page DrawingPage
        if (self.session.config['treatment'] == 10)\
                &(self.player.participant.vars["whole_XP_done"]==False)\
                &((self.participant.vars["stop_pressed"] == 1)
                      |(self.subsession.timer_elapsed())):
            yield (views.DrawingPage)
