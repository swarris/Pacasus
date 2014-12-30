''' This module contains the programs from the pyPaSWAS suite '''
from pyPaSWAS.Core.SmithWaterman import SmithWaterman
from pyPaSWAS.Core.HitList import HitList
from pyPaSWAS.Core.Indexer import Indexer
from operator import itemgetter


class Aligner(object):
    '''
    Common functionality shared by all aligning programs from the pyPaSWAS suite is encapsulated in this class.
    '''
    # TODO: expand - and update - docstrings!!

    def __init__(self, logger, score, settings):
        '''
        Constructor.

        @param logger: an instance of logging.logger
        @param score: a score object. None by default
        @param settings: an instance of a settings object as returned by optparse. These settings should include:
            filterFactor: Defaults to 0.7
            device: Defaults to 0 i.e. the first card in the array
            #limitLength. Defaults to 5000. Sets a limit to the maximal length of items to be be compared at one time
            maxGenomeLength. Sets the maximum length of (the part of) the sequence that will be processed at one time.
                Should the length of the sequence exceed this setting, the sequence will be divided and the resulting parts
                will be processed separately. Defaults to 200000.
        @raise InvalidOptionException: If either verifySettings of verifyArguments fail.
        '''
        logger.debug('Initializing aligner...')
        self.logger = logger
        self.score = score
        self.hitlist = HitList(self.logger)
        logger.debug('Setting SW...')
        self.settings = settings
        self.smith_waterman = SmithWaterman(self.logger, self.score, settings)
        self.logger.debug('Aligner initialized.')

    def process(self, records_seqs, targets):
        '''This methods sends the target- and query sequences to the SmithWaterman instance
        and receives the resulting hitlist.
        '''
        # step through the targets
        self.logger.debug('Aligner processing...')
        target_index = 0

        while target_index < len(targets):
            self.logger.debug('At target: {0} of {1}'.format(target_index, len(targets)))


            last_target_index = self.smith_waterman.set_targets(targets, target_index)
            # results should be a Hitlist()
            results = self.smith_waterman.align_sequences(records_seqs, targets, target_index)
            self.hitlist.extend(results)
            target_index = last_target_index
        self.logger.debug('Aligner processing OK, returning hitlist.')
        return self.hitlist
    
        

class Trimmer(Aligner):
    
    def __init__(self, logger, score, settings):
        Aligner.__init__(self, logger, score, settings)

    def process(self, records_seqs, targets):
        '''This methods sends the target- and query sequences to the SmithWaterman instance
        and receives the resulting hitlist.
        '''
        # step through the targets
        self.logger.debug('Aligner processing...')
        target_index = 0
        if len(targets) > 0 and self.settings.recompile == "F":
            max_length = len(targets[0])
        else:
            max_length = None
            
        while target_index < len(targets):
            self.logger.debug('At target: {0} of {1}'.format(target_index, len(targets)))

            last_target_index = self.smith_waterman.set_targets(targets, target_index, max_length, records_seqs)
            # results should be a Hitlist()
            results = self.smith_waterman.align_sequences(records_seqs, targets, target_index)
            self.hitlist.extend(results)
            target_index = last_target_index
        self.logger.debug('Aligner processing OK, returning hitlist.')
        return self.hitlist

class ComBaRIndexer(Aligner):
    
    def __init__(self, logger, score, settings, arguments):
        Aligner.__init__(self, logger, score, settings)
        self.arguments = arguments

    def process(self, records_seqs, targets):
        '''This methods creates index files for targets based on the length of the records.
        '''
        # step through the targets
        self.logger.debug('ComBaR indexing...')
        indexer = Indexer(self.settings, self.logger, 0.1, records_seqs)
        indexer.createIndexAndStore(targets, self.arguments[1])
        

        self.logger.debug('ComBaR indexing finished.')
        return self.hitlist

class ComBaRMapper(Aligner):
    
    def __init__(self, logger, score, settings, arguments):
        Aligner.__init__(self, logger, score, settings)
        self.arguments = arguments

    def process(self, records_seqs, targets):
        '''This methods creates index files for targets based on the length of the records.
        '''
        # step through the targets
        self.logger.debug('ComBaR mapping...')
        indexer = Indexer(self.settings, self.logger, 0.1, records_seqs)

        # does index exists?
        if not indexer.unpickle(self.arguments[1]):
            indexer.createIndexAndStore(targets, self.arguments[1])


        keepRecords = []

        while len(records_seqs) > 0:
            firstRead = records_seqs[0]
            keepRecords.append(records_seqs[0])
            filteredRecordsSeqs = records_seqs[0:1]

            self.logger.info("Processing seq: " + records_seqs[0].id)
            del records_seqs[0]

            locations = indexer.findIndices(firstRead.seq)
            
            splittedTargets = []
            locs = []
            if (len(locations) > 0):
                for value in locations.itervalues():
                    locs.extend(value)
                
                for loc in locs:
                    swSeqRecord = indexer.getSWSeqRecord(loc, targets)
                    swSeqRecord.distance = loc[2]
                    swSeqRecord.id = targets[loc[0][1]].id
                    swSeqRecord.refID = loc[0][1]
                    splittedTargets.append(swSeqRecord)
            
            if (len(splittedTargets) > 0 and len(filteredRecordsSeqs) > 0):
                splittedTargets.sort(key=lambda seqIO : len(seqIO.seq), reverse=True)
                target_index = 0
                # process of the seeds:
                while target_index < len(splittedTargets):
                    last_target_index = self.smith_waterman.set_targets(splittedTargets, target_index, None, filteredRecordsSeqs) 
                    self.logger.debug('At target: {0} of {1}, processing up to {2}'.format(target_index, len(splittedTargets), str(last_target_index)))
                    results = self.smith_waterman.align_sequences(filteredRecordsSeqs, splittedTargets, target_index)
                    self.hitlist.extend(results)
                    target_index = last_target_index

        self.logger.debug('ComBaR mapping finished.')
        return self.hitlist

        
        