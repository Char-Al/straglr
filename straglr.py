#!/usr/bin/env python
import argparse
from src.ins import INSFinder
from src.tre import TREFinder
from src.version import __version__
import sys
import tempfile

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("bam", type=str, help="bam file")
    parser.add_argument("genome_fasta", type=str, help="genome_fasta")
    parser.add_argument("out_prefix", type=str, help="output prefix")
    parser.add_argument("--reads_fasta", type=str, help="read indexed fasta file")
    parser.add_argument("--min_ins_size", type=int, default=100, help="minimum insertion size. Default:100")
    parser.add_argument("--exclude", type=str, help="bed file to exclude regions")
    parser.add_argument("--regions", type=str, help="bed file for scanning only specific regions")
    parser.add_argument("--nprocs", type=int, help="number of processes", default=1)
    parser.add_argument("--chroms", type=str, nargs="+", help="chromosomes")
    parser.add_argument("--loci", type=str, help="bed file of loci for genotyping")
    parser.add_argument("--min_support", type=int, help="minimum number of supporting reads for detecting expansion", default=2)
    parser.add_argument("--min_cluster_size", type=int, help="minimum number of supporting reads for allele clustering", default=2)
    parser.add_argument("--genotype_in_size", action="store_true", help="report genotype in size instead of copy numbers")
    parser.add_argument("--max_str_len", type=int, help="maximum STR length. Default:50", default=50)
    parser.add_argument("--min_str_len", type=int, help="minimum STR length. Default:2", default=2)
    parser.add_argument("--max_num_clusters", type=int, help="maximum number of clusters to try. Default:2", default=2)
    parser.add_argument("--max_cov", type=int, help="maximum allowed coverage for ins inspection. Default:100", default=100)
    parser.add_argument("--tmpdir", type=str, help="directory to use for generating tmp files instead of system TEMP")
    parser.add_argument("--debug", action='store_true', help="debug mode i.e. keep trf output")
    parser.add_argument("--version", action='version', version=__version__)
    return parser.parse_args()

def main():
    args = parse_args()

    if args.tmpdir:
        tempfile.tempdir = args.tmpdir

    min_cluster_size = args.min_cluster_size if args.min_cluster_size < args.min_support else args.min_support

    tre_finder = TREFinder(args.bam,
                           args.genome_fasta,
                           nprocs=args.nprocs,
                           reads_fasta=args.reads_fasta,
                           max_str_len=args.max_str_len,
                           min_str_len=args.min_str_len,
                           min_support=args.min_support,
                           min_cluster_size=min_cluster_size,
                           genotype_in_size=args.genotype_in_size,
                           max_num_clusters=args.max_num_clusters,
                           debug=args.debug)

    variants = []
    if not args.loci:
        ins_finder = INSFinder(args.bam,
                               args.genome_fasta,
                               args.min_ins_size,
                               reads_fasta=args.reads_fasta,
                               exclude=args.exclude,
                               chroms=args.chroms,
                               nprocs=args.nprocs,
                               min_support=args.min_support,
                               max_cov=args.max_cov,
                               debug=args.debug,
                               )
        if ins := ins_finder.find_ins(regions_bed_file=args.regions):
            variants = tre_finder.examine_ins(ins, min_expansion=args.min_ins_size)

    else:
        tre_finder.min_cluster_size = args.min_cluster_size
        variants = tre_finder.genotype(args.loci)

    # output both bed and tsv
    tre_finder.output_bed(variants, f'{args.out_prefix}.bed')
    tre_finder.output_tsv(
        variants, f'{args.out_prefix}.tsv', cmd=' '.join(sys.argv)
    )

if __name__ == '__main__':
    main()
