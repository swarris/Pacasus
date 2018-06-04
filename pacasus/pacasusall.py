'''
This module contains the main class of Pacasus.

'''

from pyPaSWAS.Core import resource_filename
from pyPaSWAS.Core.Exceptions import InvalidOptionException, ReaderException
from pyPaSWAS.Core.Formatters import DefaultFormatter, FASTA
from Core.Programs import Palindrome
from pyPaSWAS.Core.Readers import BioPythonReader
from pyPaSWAS.Core.Scores import BasicScore, CustomScore, DnaRnaScore
from pyPaSWAS.Core.HitList import HitList
from pyPaSWAS import set_logger, normalize_file_path 
import logging
import os.path

from pacasus.Core.Scores import PalindromeScore
from pacasus import parse_cli
from pyPaSWAS.pypaswasall import Pypaswas

class Pacasus(Pypaswas):
    def __init__(self, config=None):
        Pypaswas.__init__(self, config = resource_filename(__name__, '/Core/cfg/defaults.cfg'))
        
    def _get_formatter(self, results):
        '''Sets the format of the output file.'''
        formatter = ''
        if self.output_format == "FASTA":
            formatter = FASTA(self.logger, results, self.outputfile)
        else:
            formatter = DefaultFormatter(self.logger, results, self.outputfile)
        return formatter


    def _get_target_sequences(self, databasefile, start =0, end=None):
        '''Gets the target (database) sequences from the database file. '''
        databasefile = normalize_file_path(databasefile)
        if not os.path.exists(databasefile):
            raise InvalidOptionException('File {0} does not exist.'.format(databasefile))
        else:
            reader = BioPythonReader(self.logger, databasefile, self.settings.filetype1, self.settings.limit_length)
            reader.read_records(start, end)

            if self.score.score_type == 'DNA_RNA':
                reader.complement_records()
            elif self.score.score_type == 'PALINDROME':
                reader.complement_records_only()
            elif self.score.score_type == "IRYS":
                reader.reverse_records()
            reader.sort_records()
            return reader.get_records()

    def _set_scoring_matrix(self):
        ''' Instantiate the scoring matrix. For more information refer to the
            documentation of the different score types. '''
        matrix_name = self.settings.matrix_name.upper()
        score = None
        if matrix_name == 'DNA-RNA':
            score = DnaRnaScore(self.logger, self.settings)
        elif matrix_name == 'PALINDROME':
            score = PalindromeScore(self.logger, self.settings)
        elif matrix_name == 'BASIC':
            score = BasicScore(self.logger, self.settings)
        elif matrix_name == 'CUSTOM':
            score = CustomScore(self.logger, self.settings)
        else:
            raise InvalidOptionException(matrix_name + ' is not a valid substitution matrix')
        self.score = score

    def _set_output_format(self):
        '''Determines the output format.
            Currently only TXT for text and SAM for SAM are supported.
        '''
        if self.settings.out_format.upper() == 'FASTA':
            self.output_format = 'FASTA'
        else:
            raise InvalidOptionException('Invalid output format {0}.'.format(self.settings.out_format))

    def _set_program(self):
        '''Determines what program from the suite should be used and instantiates it'''
        if self.settings.program == "palindrome":
            self.program = Palindrome(self.logger, self.score, self.settings)
            self.logger.warning("Forcing output to FASTA")
            self.output_format = "FASTA"
            self.logger.warning("Forcing query step to 1")
            self.settings.query_step = "1"
            self.logger.warning("Forcing sequence step to 1")
            self.settings.sequence_step = "1"
            self.logger.warning("Forcing Matrix to PALINDROME")
            self.settings.matrix_name = "PALINDROME"
            self.score = PalindromeScore(self.logger, self.settings)
        else:
            raise InvalidOptionException('Invalid program selected {0}'.format(self.settings.program))

    def run(self):
        '''The main program of pyPaSWAS.'''
        # Read command-line arguments
        self.settings, self.arguments = parse_cli(self.config_file)
        self.logger = set_logger(self.settings)
        self.logger.info("Initializing application...")
        self._set_outfile()
        self._set_scoring_matrix()
        self.logger.info('Application initialized.')
        self.logger.info('Setting program...')
        self._set_output_format()
        self._set_program()
        self.logger.info('Program set.')
        
        queriesToProcess = True
        
        query_start = int(self.settings.start_query)
        query_end = int(self.settings.start_query) + int(self.settings.query_step)
        if query_end > int(self.settings.end_query) and int(self.settings.start_query) != int(self.settings.end_query):
            query_end = int(self.settings.end_query)
        
        start_index = int(self.settings.start_target)

        end_index = int(self.settings.start_target) + int(self.settings.sequence_step) 
        if end_index > int(self.settings.end_target) and int(self.settings.start_target) != int(self.settings.end_target):
            end_index = int(self.settings.end_target)
        
        results = HitList(self.logger)
        
        while queriesToProcess:
            self.logger.info('Reading query sequences {} {}...'.format(query_start, query_end))
            try:
                query_sequences = self._get_query_sequences(self.arguments[0], start=query_start, end=query_end)
                self.logger.info('Query sequences OK.')
            except ReaderException:
                queriesToProcess = False

            sequencesToProcess = True
            if not self.settings.program == "palindrome":
                start_index = int(self.settings.start_target)
                end_index = int(self.settings.start_target) + int(self.settings.sequence_step) 
                if end_index > int(self.settings.end_target) and int(self.settings.start_target) != int(self.settings.end_target):
                    end_index = int(self.settings.end_target)
            
            while queriesToProcess and sequencesToProcess:
                
                self.logger.info('Reading target sequences {}, {}...'.format(start_index,end_index))
                try:
                    target_sequences = self._get_target_sequences(self.arguments[0], start=start_index, end=end_index)
                    self.logger.info('Target sequences OK.')
                except ReaderException:
                    sequencesToProcess = False
                    
    
                if not sequencesToProcess or not queriesToProcess or len(query_sequences) == 0 or len(target_sequences) == 0:
                    sequencesToProcess = False
                    self.logger.info('Processing done')
                else:
                    self.logger.info('Processing {0}- vs {1}-sequences'.format(len(query_sequences),
                                                                            len(target_sequences)))
                    results.extend(self.program.process(query_sequences, target_sequences, self))
                
                if sequencesToProcess and len(target_sequences) <= end_index:
                    # for palindrome program, skip directly to next
                    sequencesToProcess = False
                    self.logger.info('Processing done')

                start_index = start_index + int(self.settings.sequence_step)
                end_index = end_index + int(self.settings.sequence_step)
                if  self.settings.program == "palindrome" or (int(self.settings.end_target) > 0 and int(self.settings.end_target) < end_index):
                    sequencesToProcess = False

            if int(self.settings.end_query) > 0 and int(self.settings.end_query) < query_end:
                queriesToProcess = False
            query_start = query_start + int(self.settings.query_step)
            query_end = query_end + int(self.settings.query_step)


        nhits = len(results.hits)
        # retrieve and print results!
        self.logger.info('Processing OK ({} hits found).'.format(nhits))
        if nhits > 0:
            self.logger.info('Formatting output...')
            formatter = self._get_formatter(results)
            self.logger.info('Formatting OK.')

            self.logger.info('Writing output...')
            formatter.print_results()
            self.logger.info('Writing OK.')
            self.logger.info('Finished')
        else:
            self.logger.warning('No suitable hits produced, exiting...')

