'''
TODO Add a proper introduction of the package.
'''
from pyPaSWAS.Core.Exceptions import InvalidOptionException
from pyPaSWAS import set_logger, _override_settings, _log_settings_to_file, normalize_file_path
from datetime import datetime
import configparser
import logging
import optparse
import os
import sys



def parse_cli(config_file):
    '''
    parseCLI()

    This function parses the command line using the optparse module from the python standard library.
    Though deprecated since python 2.7, optparse still is used in stead of argparse because the python
    version available at the development systems was 2.6.
    The options and arguments are stored in the global variables settings and arguments, respectively.
    '''
    # Read defaults
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
    except configparser.ParsingError:
        raise configparser.ParsingError("Unable to parse the defaults file ({})".format(config_file))

    parser = optparse.OptionParser()
    parser.description = ('This program performs a Smith-Waterman alignment of the sequences in FILE_1 against '
                          'the reverse-complement of the reads.\nWhen an alignment indicates the presence of '
                          'palindromes the read will be split at. ')
    usage = '%prog [options] FILE_1'
    parser.usage = usage
    # general options

    # TODO: Get final naming (convention) for all parameters!!
    general_options = optparse.OptionGroup(parser, 'Options that affect the general operation of the program')
    general_options.add_option('-L', '--logfile', help='log events to FILE', metavar="FILE", dest='logfile')
    general_options.add_option('--loglevel', help='log level. Valid options are DEBUG, INFO, WARNING, ERROR'
                               ' and CRITICAL', dest='loglevel', default=config.get('General', 'loglevel'))
    general_options.add_option('-o', '--out', help='The file in which the program stores the generated output.'
                               '\nDefaults to ./output', dest='out_file', default=config.get('General', 'out_file'))
    general_options.add_option('--outputformat', help='The format of the file in which the program stores the '
                               'generated output.\nAvailable options are TXT and SAM.\nDefaults to txt',
                               dest='out_format', default=config.get('General', 'out_format'))
    general_options.add_option('-p', '--program', help='The program to be executed. Valid options are "aligner"'
                               ', "trimmer", "mapper", "plotter" and palindrome (experimental)', dest='program',
                               default=config.get('General', 'program'))

    general_options.add_option('-1', '--filetype1', help='File type of the first file. See bioPython IO for'
                               ' available options', dest='filetype1', default=config.get('General', 'filetype1'))
    general_options.add_option('-O', '--override_output', help='When output file exists, override it (T/F)',
                               dest='override_output', default=config.get('General', 'override_output'))
    general_options.add_option('-c', '--configfile', help='Give settings using configuration file',
                               dest='config_file', default=False)

    parser.add_option_group(general_options)


    input_options = optparse.OptionGroup(parser, 'start & stop indices for processing files. Handy for cluster processing. Leave all to zero to process all.')
    input_options.add_option('--start_query', help='start index in the query file (1)', dest='start_query', default=config.get("Input", "start_query"))
    input_options.add_option('--end_query', help='end index in the query file (1)', dest='end_query', default=config.get("Input", "end_query"))

    input_options.add_option('--start_target', help='start index in the target file (2)', dest='start_target', default=config.get("Input", "start_target"))
    input_options.add_option('--end_target', help='end index in the target file (2)', dest='end_target', default=config.get("Input", "end_target"))
    input_options.add_option('--sequence_step', help='Number of sequences read from file 2 before processing. Handy when processing NGS files.',
                              dest='sequence_step', default=config.get('Input', 'sequence_step'))
    input_options.add_option('--query_step', help='Number of sequences read from file 1 before processing. Handy when processing NGS files.',
                              dest='query_step', default=config.get('Input', 'query_step'))

    parser.add_option_group(input_options)



    aligner_options = optparse.OptionGroup(parser, 'Options that affect the alignment.\nAligners include aligner'
                                           ' and mapper')
    aligner_options.add_option('--customMatrix', help='the custom matrix that should be used', dest='custom_matrix')
    aligner_options.add_option('-G', help='Float. Penalty for a gap', dest='gap_score',
                               default=config.get('Aligner', 'gap_score'))
    aligner_options.add_option('-g', '--gap_extension', help='Float. Penalty for a gap extension. Set to zero to ignore this (faster)', dest='gap_extension',
                           default=config.get('Aligner', 'gap_extension'))

    aligner_options.add_option('-M', '--matrixname', help='The scoring to be used. Valid options are '
                               '"DNA-RNA", "PALINDROME", "BASIC" and "CUSTOM"', dest='matrix_name',
                               default=config.get('Aligner', 'matrix_name'))
    aligner_options.add_option('-q', '--mismatch_score', help='Float. Penalty for mismatch', dest='mismatch_score',
                               default=config.get('Aligner', 'mismatch_score'))
    aligner_options.add_option('-r', '--match_score', help='Float. Reward for match', dest='match_score',
                               default=config.get('Aligner', 'match_score'))
    aligner_options.add_option('--any', help='Float. Score for a character which is neither in the nucleotide'
                               ' list ("ACGTU"), nor equal to the anyNucleotide character ("N").\nOnly relevant'
                               ' for use with the DNA-RNA scoring type.', dest='any_score',
                               default=config.get('Aligner', 'any_score'))
    aligner_options.add_option('--other', help='Float. Score if the anyNucleotide character ("N") is present in'
                               ' either query or subject.\nOnly relevant for use with the DNA-RNA scoring type.',
                               dest='other_score', default=config.get('Aligner', 'other_score'))
    aligner_options.add_option('--minimum', help='Float. Sets the minimal score that initiates a back trace.'
                               ' Do not set this very low: output may be flooded by hits.', dest='minimum_score',
                               default=config.get('Aligner', 'minimum_score'))

    aligner_options.add_option('--llimit', help='Float. Sets the lower limit for the maximum score '
                               'which will be used to report a hit. pyPaSWAS will then also report hits with '
                               'a score lowerLimitScore * highest hit score. Set to <= 1.0. ',
                               dest='lower_limit_score', default=config.get('Aligner', 'lower_limit_score'))
    parser.add_option_group(aligner_options)

    filter_options = optparse.OptionGroup(parser, 'Options for finding palindromes and splitting reads' )
    
    filter_options.add_option('--filter_factor', help='The filter factor to be used. Reports only hits within'
                              ' filterFactor * highest possible score * length shortest sequence (or: defines'
                              ' lowest value of the reported relative score). Set to <= 1.0',
                              dest='filter_factor', default=config.get('Filter', 'filter_factor'))

    filter_options.add_option('--query_coverage', help='Minimum query coverage. Set to <= 1.0',
                              dest='query_coverage', default=config.get('Filter', 'query_coverage'))

    filter_options.add_option('--query_identity', help='Minimum query identity. Set to <= 1.0',
                              dest='query_identity', default=config.get('Filter', 'query_identity'))

    filter_options.add_option('--relative_score', help='Minimum relative score, defined by the alignment score'
                              ' divided by the length of the shortest of the two sequences. Set to <= highest possible score'
                              ', for example 5.0 in case of DNA',
                              dest='relative_score', default=config.get('Filter', 'relative_score'))
    
    filter_options.add_option('--base_score', help='Minimum base score, defined by the alignment score'
                              ' divided by the length of the alignment (including gaps). Set to <= highest possible score'
                              ', for example 5.0 in case of DNA',
                              dest='base_score', default=config.get('Filter', 'base_score'))
    parser.add_option_group(filter_options)

    palindrome_options = optparse.OptionGroup(parser, 'Options related to the Palindrome detector.')
    palindrome_options.add_option('--query_coverage_slice', help='Minimum fraction of the read in the alignment needed to slice the read in half.', dest='query_coverage_slice',
                              default=config.get('Palindrome', 'query_coverage_slice'))

    palindrome_options.add_option('--minimum_read_length', help='Minimum length of the read in bp to the saved.', dest='minimum_read_length',
                              default=config.get('Palindrome', 'minimum_read_length'))
    parser.add_option_group(palindrome_options)

    
    device_options = optparse.OptionGroup(parser, 'Options that affect the usage and settings of the '
                                          'parallel devices')
    device_options.add_option('--device', help='the device on which the computations will be performed. '
                              'This should be an integer.', dest='device_number',
                              default=config.get('Device', 'device_number'))
    device_options.add_option('--number_of_compute_units', help='Number of compute units to use (openCL only). Will not work on every device, recommended for CPU only. Set this 1 to use a single core on the device for example.'
                              'This should be an integer, using 0 for full device.', dest='number_of_compute_units',
                              default=config.get('Device', 'number_of_compute_units'))
    device_options.add_option('--sub_device', help='the sub device on which the computations will be performed. Only used when number_of_compute_units > 0. '
                              'This should be an integer.', dest='sub_device',
                              default=config.get('Device', 'sub_device'))
    
    
    device_options.add_option('--limit_length', help='Length of the longest sequence  in characters to be read'
                              ' from file. Lower this when memory of GPU is low.', dest='limit_length',
                              default=config.get('Device', 'limit_length'))
    device_options.add_option('--maximum_memory_usage', help='Fraction (<= 1.0) of available GPU memory to use. Useful with --recompile=F and when several pyPaSWAS applications are running.', dest="maximum_memory_usage", default=config.get('Device', 'maximum_memory_usage'))
    device_options.add_option('--njobs', help='Sets the number of jobs run simultaneously on the grid. Will read'
                              ' only part of the sequence file. (not implemented yet)', dest='number_of_jobs')
    device_options.add_option('--process_id', help='Sets the processID of this job in the grid. ',
                              dest='process_id')
    device_options.add_option('--max_genome_length', help='Deprecated.\nDefaults to 200000',
                              dest='max_genome_length', default=config.get('Device', 'max_genome_length'))
    device_options.add_option('--recompile', help='Recompile CUDA code? Set to F(alse) when sequences are of similar length: much faster.',
                              dest='recompile', default=config.get('Device', 'recompile'))
    device_options.add_option('--short_sequences', help='Set to T(true) when aligning short sequences (trimming?) to maximize memory usage.',
                              dest='short_sequences', default=config.get('Device', 'short_sequences'))

    parser.add_option_group(device_options)
    
    
    framework_options = optparse.OptionGroup(parser, 'Determines which parallel computing framework to use for this program ')
    framework_options.add_option('--framework', help='Choose which parallel computing framework to use, can be either CUDA or OpenCL ', dest='framework',default=config.get('Framework','language'))
    parser.add_option_group(framework_options)
    
    ocl_options = optparse.OptionGroup(parser, 'Options for the usage of the OpenCL framework ')
    ocl_options.add_option('--device_type', help='Type of device to perform computations on (either CPU, GPU or ACCELARATOR)',
                           dest='device_type', default=config.get('OpenCL', 'device_type'))
    ocl_options.add_option('--platform_name', help='Platform to run computations on (either Intel, NVIDIA or AMD)',
                           dest='platform_name', default=config.get('OpenCL', 'platform_name'))
    parser.add_option_group(ocl_options)

    (settings, arguments) = parser.parse_args()

    # If an extra configuration file is given, override settings as given by this file
    if settings.config_file:
        (settings, arguments) = _override_settings(settings.config_file, settings, arguments)

    if len(arguments) < 1:
        raise InvalidOptionException('Missing input files. please use -h for available options')

    return (settings, arguments)


