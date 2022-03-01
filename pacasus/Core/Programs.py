''' This module contains the programs from the pyPaSWAS suite '''
from pyPaSWAS.Core.HitList import HitList
from operator import itemgetter,attrgetter

from pyPaSWAS.Core.SWSeqRecord import SWSeqRecord
from Bio.Seq import Seq
from pyPaSWAS.Core.Hit import Hit
from pyPaSWAS.Core.Programs import Aligner

class Palindrome(Aligner):
    
    def __init__(self, logger, score, settings):
        Aligner.__init__(self, logger, score, settings)

    def palindrome(self, hit, records_seq, targets, settings):
        if hit.query_coverage > float(settings.query_coverage_slice):
            snip = int(len(hit.sequence_info.seq)/2)
            records_seq.append(SWSeqRecord(hit.sequence_info.seq[:snip], hit.sequence_info.id + "_a1"))
            records_seq.append(SWSeqRecord(hit.sequence_info.seq[snip:], hit.sequence_info.id + "_a2"))

            targets.append(SWSeqRecord(hit.sequence_info.seq[:snip].reverse_complement(), hit.sequence_info.id + "_a1_RC"))
            targets.append(SWSeqRecord(hit.sequence_info.seq[snip:].reverse_complement(), hit.sequence_info.id + "_a2_RC"))
        else:
            snip = int((hit.seq_location[1]-hit.seq_location[0])/2)
            if snip - hit.seq_location[0] > int(settings.minimum_read_length):
                records_seq.append(SWSeqRecord(hit.sequence_info.seq[:snip], hit.sequence_info.id + "_b1"))
                targets.append(SWSeqRecord(hit.sequence_info.seq[:snip].reverse_complement(), hit.sequence_info.id + "_b1_RC"))
            if hit.seq_location[1] - snip > int(settings.minimum_read_length):
                records_seq.append(SWSeqRecord(hit.sequence_info.seq[snip:], hit.sequence_info.id + "_b2"))
                targets.append(SWSeqRecord(hit.sequence_info.seq[snip:].reverse_complement(), hit.sequence_info.id + "_b2_RC"))


    def process(self, records_seqs, targets, pypaswas):
        '''This methods sends the target- and query sequences to the SmithWaterman instance
        and receives the resulting hitlist.
        '''
        # Fix this target
        self.logger.debug('Fixing palindrome sequences...')

        cur_records_seq = records_seqs
        cur_targets = targets
        target_index = 0
        # handle it as a queue:    
        while len(cur_targets) >0 :
            self.smith_waterman.set_targets(cur_targets[:1], target_index)
            results = self.smith_waterman.align_sequences(cur_records_seq[:1], cur_targets, target_index)
            if len(results.real_hits) == 0 : # nothing more to do
                results = HitList(self.logger)
                hit = Hit(self.logger, cur_records_seq[0],
                          cur_targets[0],
                          (0, 1), (0, 1))
                results.append(hit)
                self.hitlist.extend(results)
            else:
                # process hit to get new targets
                # get hits and sort on highest score
                hit = sorted(results.real_hits.values(),key=attrgetter('score'), reverse=True)[0]
                # process this best hit
                if self.settings.remove == "T" or self.settings.remove == "t":
                    self.logger.info("Hit found, skipping read with ID {}".format(hit.sequence_info.id))
                else:
                    self.palindrome(hit, cur_records_seq, cur_targets,self.settings)
            # remove processed sequences: 
            cur_targets = cur_targets[1:]
            cur_records_seq = cur_records_seq[1:]
                
                 
                
            
        self.logger.debug('Fixing done.')
        return self.hitlist

        
