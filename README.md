Pacasus
========
Tool from detecting and cleaning PacBio / Nanopore long reads after whole genome amplification.

It uses the pyPaSWAS framework for sequence alignment (https://github.com/swarris/pyPaSWAS)

Platforms supported:
- NVIDIA GPU using CUDA (compute capability 1.3 and higher) 
- NVIDIA GPU using OpenCL
- Intel CPU using OpenCL
- Intel Xeon Phi accelerator using OpenCL
- Other systems supporting OpenCL (AMD, Intel GPUs, etc) should be able to run the software, but are untested.

Installation
------------
In most cases it is enough to clone the repository. 
git clone https://github.com/swarris/Pacasus.git

After that, please install:
- pip (https://docs.python.org/2.7/installing/)
- numpy: sudo pip install numpy (or pip install --user numpy)
- BioPython: sudo pip install Biopython (or pip install --user Biopython)
- In some cases, the python development packages are required (Ubuntu: sudo apt-get install python-dev) 

Making use of the CUDA version (also recommended when using the OpenCL version on a NVIDIA GPU):
- Download CUDA sdk: https://developer.nvidia.com/cuda-downloads
- sudo pip install pyCuda (http://mathema.tician.de/software/pycuda/)

Making use of the OpenCL version:
- check dependencies or downloads for your system. See this wiki for some great pointers: http://wiki.tiker.net/OpenCLHowTo
- sudo pip install pyOpenCL

Getting pyPaSWAS:
- Clone the repository: git clone https://github.com/swarris/pyPaSWAS.git
- Or download a pre-packaged release: https://github.com/swarris/pyPaSWAS/releases

Getting pyPaSWAS:
pyPaSWAS is required as a module. Run in the following two commands in the ComBaR root folder:
git submodule init
git submodule update

Running the software
-------------------- 

The two input files are mandatory. Through the options the user can specify the file types of the input files (default: fasta), an output file and a log file. When requested, Pacasus will terminate if the output file already exists.

Run it by calling:
- *python pacasus.py |options| file1 file2*

Help file:
- *python pacasus.py --help*

Selection your device
---------------------
By default, pypaswas will use the first CPU device. This can be changed by using:
- *--device_type=[CPU|GPU]*
- *--platform_name=[Intel|NVIDIA]*
- *--framework=[opencl|CUDA]*
- *--device=[int]*

For example, this will select the CPU: --device_type=CPU --platform_name=Intel --framework=opencl

This will select the second NVIDIA GPU: --device_type=GPU --platform_name=NVIDIA --framework=CUDA --device=1


Examples
--------

Use a fasta-file:
- *python pacasus.py reads.fasta -o cleaned.fasta --loglevel=DEBUG*


Table 1. Key command line options

| Option	| Long version	| Description|
| --------- | ------------- | ---------- |
| -h| --help| This help|  
|-L	| --logfile	| Path to the log file| 
|	| --loglevel	| Specify the log level for log file output. Valid options are DEBUG, INFO, WARNING, ERROR and CRITICAL| 
|-o	| --output	| Path to the output file. Default ./output| 
|-O	| --overrideOutput	| When output file exists, override it (T/F). Default T (true) | 
|-1	| --filetype1	| File type of the first input file. See bioPython IO for available options. Default fasta| 
|-G	| 	| Float value for the gap penalty. Default -5| 
|-q	| 	| Float value for a mismatch. Default -3| 
|-r	| 	| Float value for a match. Default 1| 
|	| --any	| Float value for an ambiguous nucleotide. Default 1| 
|	| --other	| Float value for an ambiguous nucleotide. Default 1| 
|	| --device	| Integer value indicating the device to use. Default 0 for the first device. | 
|-c	| 	| Option followed by the name of a configuration file. This option allows for short command line calls and administration of used settings. | 

For questions, e-mail s.warris@gmail.com
