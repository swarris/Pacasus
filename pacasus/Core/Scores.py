''' Scores module '''
from pyPaSWAS.Core.Exceptions import InvalidOptionException
from pyPaSWAS.Core.Scores import DnaRnaScore

       
class PalindromeScore(DnaRnaScore):
    def __init__(self, logger, settings):
        DnaRnaScore.__init__(self, logger, settings)

    def _set_score_type(self):
        self.score_type = 'PALINDROME'
