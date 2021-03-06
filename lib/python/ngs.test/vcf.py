#!/usr/bin/env python

import os
import unittest
from ngs import vcf

RESOURCE_DIR = 'resources'
EXAMPLE_VCF = 'example.vcf'
EXAMPLE_VARSCAN_SNPEFF_VCF = 'example.varscan.snpeff.vcf'
EXAMPLE2_VARSCAN_SNPEFF_VCF = 'example2.varscan.snpeff.vcf'

class TestVcfFileFunctions(unittest.TestCase):
    
    def setUp(self):
        self.example_vcf = os.path.join(RESOURCE_DIR, EXAMPLE_VCF)
        self.example_vcf_column_names = ['CHROM',
                                         'POS',
                                         'ID',
                                         'REF',
                                         'ALT',
                                         'QUAL',
                                         'FILTER',
                                         'INFO',
                                         'FORMAT',
                                         'NA00001',
                                         'NA00002',
                                         'NA00003']
        self.example_vcf_column_names_str = '#' + '\t'.join(self.example_vcf_column_names)

#    def test_readline(self):
#        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
#            # Test that the object remembers the last line that was read in
#            vcffile.readline()
#            self.assertEqual(vcffile.last_line, '##fileformat=VCFv4.1\n')
#            vcffile.readline()
#            self.assertEqual(vcffile.last_line, '##fileDate=20090805\n')

    def test_is_meta(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            self.assertTrue(vcffile.is_meta('##fileDate=20120818'))
            self.assertFalse(vcffile.is_meta('# blahblah'))
            self.assertFalse(vcffile.is_meta('foo'))

    def test_is_header(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            self.assertTrue(vcffile.is_header(self.example_vcf_column_names_str))
            self.assertFalse(vcffile.is_header('#' + self.example_vcf_column_names_str))

    def test_set_column_names(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            # Test that error is raised when trying to input non-header line
            self.assertRaises(ValueError, vcffile.set_column_names, (vcffile.readline()))

            # Check that the header line is correctly parsed
            vcffile.set_column_names(self.example_vcf_column_names_str)
            self.assertEqual(vcffile.column_names[0], 'CHROM')
            self.assertEqual(vcffile.column_names[1], 'POS')
            self.assertEqual(vcffile.column_names[7], 'INFO')

    def test_jump2variants(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            vcffile.jump2variants()
            # Test that column names are set
            self.assertEqual(vcffile.column_names,
                             self.example_vcf_column_names)
            # Test that the next line is the first variant
            self.assertEqual('20     14370   rs6054257 G      A       29   PASS   NS=3;DP=14;AF=0.5;DB;H2           GT:GQ:DP:HQ 0|0:48:1:51,51 1|0:48:8:51,51 1/1:43:5:.,.\n',
                             vcffile.readline())

    def test_is_variant_line(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            self.assertFalse(vcffile.is_variant_line(vcffile.readline()))
            self.assertFalse(vcffile.is_variant_line(vcffile.readline()))
            vcffile.jump2variants()
            self.assertTrue(vcffile.is_variant_line(vcffile.readline()))
            self.assertTrue(vcffile.is_variant_line('20     14370   rs6054257 G      A       29   PASS   NS=3;DP=14;AF=0.5;DB;H2           GT:GQ:DP:HQ 0|0:48:1:51,51 1|0:48:8:51,51 1/1:43:5:.,.\n'))

    def test_read_variant(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            # Check that error is raised when reading non-variant line
            self.assertRaises(ValueError, vcffile.read_variant)

            # Check that the variant row is read in correctly
            vcffile.jump2variants()
            variant = vcffile.read_variant()
            self.assertEqual(variant['CHROM'], '20')
            self.assertEqual(variant['ID'], 'rs6054257')
            self.assertEqual(variant['NA00003'] , '1/1:43:5:.,.')

            variant =  vcffile.read_variant()
            self.assertEqual(variant['INFO'], 'NS=3;DP=11;AF=0.017')
            self.assertEqual(variant['FORMAT'], 'GT:GQ:DP:HQ')
            self.assertEqual(variant['NA00003'], '0/0:41:3')

    def test_parse_line(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            vcffile.jump2variants()
            i = 0
            for line in vcffile:
                variant = vcffile.parse_line(line)
                if i == 0:
                    self.assertEqual(variant['CHROM'], '20')
                    self.assertEqual(variant['ID'], 'rs6054257')
                    self.assertEqual(variant['NA00003'] , '1/1:43:5:.,.')
                elif i == 1:
                    self.assertEqual(variant['INFO'], 'NS=3;DP=11;AF=0.017')
                    self.assertEqual(variant['FORMAT'], 'GT:GQ:DP:HQ')
                    self.assertEqual(variant['NA00003'], '0/0:41:3')
                    break # exit loop after 2 iterations
                i += 1
                    
            

    def test_parse_info(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            # Check that the variant row is read in correctly
            vcffile.jump2variants()
            variant = vcffile.read_variant()
            info_map, info_single = vcffile.parse_info(variant)
            self.assertEqual(info_map['AF'], '0.5')
            self.assertEqual(info_map['DP'], '14')
            self.assertEqual(len(info_single), 2)
            self.assertTrue('DB' in info_single)
            self.assertTrue('H2' in info_single)

            variant =  vcffile.read_variant()
            info_map, info_single = vcffile.parse_info(variant)
            self.assertEqual(info_map['NS'], '3')
            self.assertEqual(info_map['AF'], '0.017')

    def test_get_sample_names(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            vcffile.jump2variants()
            sample_names = vcffile.get_sample_names()
            self.assertEqual(len(sample_names), 3)
            self.assertTrue('NA00001' in sample_names)
            self.assertTrue('NA00002' in sample_names)
            self.assertTrue('NA00003' in sample_names)

    def test_parse_samples(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            vcffile.jump2variants()
            variant = vcffile.read_variant()
            sample2field2val = vcffile.parse_samples(variant)
            self.assertEqual(len(sample2field2val), 3)
            self.assertTrue('NA00001' in sample2field2val)
            self.assertTrue('NA00002' in sample2field2val)
            self.assertTrue('NA00003' in sample2field2val)
            self.assertEqual(sample2field2val['NA00001']['GT'], '0|0')
            self.assertEqual(sample2field2val['NA00002']['GQ'], '48')
            self.assertEqual(sample2field2val['NA00003']['HQ'], '.,.')

            variant = vcffile.read_variant()
            sample2field2val = vcffile.parse_samples(variant)
            self.assertEqual(sample2field2val['NA00001']['HQ'], '58,50')
            self.assertEqual(sample2field2val['NA00002']['GT'], '0|1')
            self.assertEqual(sample2field2val['NA00003']['GQ'], '41')

    def test_get_sample_gt(self):
        with vcf.VcfFile(self.example_vcf, 'r') as vcffile:
            vcffile.jump2variants()
            variant = vcffile.read_variant()
            gt = vcffile.get_sample_gt(variant, 'NA00001', phased=True)
            self.assertEqual(gt, 'G|G')

            variant = vcffile.read_variant()
            gt = vcffile.get_sample_gt(variant, 'NA00002', phased=True)
            self.assertEqual(gt, 'T|A')

            variant = vcffile.read_variant()
            gt = vcffile.get_sample_gt(variant, 'NA00003', phased=False)
            self.assertEqual(gt, 'T/T')

            variant = vcffile.read_variant()
            variant = vcffile.read_variant()
            gt = vcffile.get_sample_gt(variant, 'NA00001', phased=False)
            self.assertEqual(gt, 'G/GTC')


class TestVascanVcfFileFunctions(unittest.TestCase):
    
    def setUp(self):
        pass


class TestSnpEffVcfFileFunctions(unittest.TestCase):
    
    def setUp(self):
        self.example_vcf = os.path.join(RESOURCE_DIR, EXAMPLE_VARSCAN_SNPEFF_VCF)

    def test_set_effect2priority(self):
        with vcf.SnpEffVcfFile(self.example_vcf, 'r') as vcffile:
            # Ensure that the effect2priority attribute is not set yet
            self.assertTrue(vcffile.effect2priority is None)
            vcffile._set_effect2priority()
            # Ensure that the effect2priority attribute is set correctly
            self.assertTrue(vcffile.effect2priority is not None)
            self.assertEqual(vcffile.effect2priority['SPLICE_SITE_ACCEPTOR'], 1)
            self.assertEqual(vcffile.effect2priority['STOP_GAINED'], 6)
            self.assertEqual(vcffile.effect2priority['CODON_CHANGE_PLUS_CODON_INSERTION'], 11)

    def test_set_prioritized_effects(self):
        with vcf.SnpEffVcfFile(self.example_vcf, 'r') as vcffile:
            self.assertEqual(vcffile.effects_prioritized[-1], 'CDS')
            vcffile.set_prioritized_effects(['foo','bar'])
            self.assertEqual(vcffile.effects_prioritized[0], 'foo')
            self.assertEqual(len(vcffile.effects_prioritized), 2)
            self.assertEqual(vcffile.effect2priority['foo'], 0)
            self.assertEqual(vcffile.effect2priority['bar'], 1)

    def test_parse_effects(self):
        '''
        DOWNSTREAM(
          MODIFIER|
          |
          |
          |
          MMP23B|
          protein_coding|
          CODING|
          ENST00000356026|),
        TRANSCRIPT(
          MODIFIER|
          |
          |
          |
          AL691432.2|
          unprocessed_pseudogene|
          NON_CODING|
          ENST00000317673|),
        SPLICE_SITE_ACCEPTOR(
          HIGH|
          |
          |
          |
          WASH2P|
          unprocessed_pseudogene|
          NON_CODING|
          ENST00000542901|),
        UTR_5_PRIME(
          MODIFIER|
          |
          |
          |
          ARHGEF16|
          protein_coding|
          CODING|
          ENST00000378371|
          exon_1_3383535_3383901)
        NON_SYNONYMOUS_CODING(
          MODERATE|
          MISSENSE|
          Cgg/Tgg|
          R10W|
          CYP4B1|
          processed_transcript|
          CODING|
          ENST00000468637|
          exon_1_47279154_47279278)
        '''
        
        with vcf.SnpEffVcfFile(self.example_vcf, 'r') as vcffile:
            vcffile.jump2variants()
            variant = vcffile.read_variant()
            effects = vcffile.parse_effects(variant)
            self.assertEqual(len(effects), 5)
            self.assertEqual([effects[0].effect,
                              effects[1].effect,
                              effects[2].effect,
                              effects[3].effect,
                              effects[4].effect],
                             ['SPLICE_SITE_ACCEPTOR',
                              'NON_SYNONYMOUS_CODING',
                              'UTR_5_PRIME',
                              'DOWNSTREAM',
                              'TRANSCRIPT'])
            self.assertEqual(effects[0].impact, 'HIGH')
            self.assertEqual(effects[0].functional_class, '')
            self.assertEqual(effects[1].impact, 'MODERATE')
            self.assertEqual(effects[1].functional_class, 'MISSENSE')
            self.assertEqual(effects[1].codon_change, 'Cgg/Tgg')
            self.assertEqual(effects[1].aa_change, 'R10W')
            self.assertEqual(effects[1].gene, 'CYP4B1')
            self.assertEqual(effects[1].gene_biotype, 'processed_transcript')
            self.assertEqual(effects[1].exon, 'exon_1_47279154_47279278')

    def test_select_highest_priority_effect(self):
        with vcf.SnpEffVcfFile(self.example_vcf, 'r') as vcffile:
            vcffile.jump2variants()
            variant = vcffile.read_variant()
            effects = vcffile.parse_effects(variant)
            self.assertEqual(str(effects[0]), str(vcffile.select_highest_priority_effect(variant)))

    def test_find_selected_trancript_effects(self):
        with vcf.SnpEffVcfFile(self.example_vcf, 'r') as vcffile:
            vcffile.jump2variants()
            variant = vcffile.read_variant()

            effects = vcffile.find_selected_transcript_effects(variant, {})
            self.assertEqual(len(effects), 0)

            effects = vcffile.find_selected_transcript_effects(variant, {'hello':'world'})
            self.assertEqual(len(effects), 0)

            effects = vcffile.find_selected_transcript_effects(variant, {'CYP4B1':'ENST00000468637'})
            self.assertEqual(len(effects), 1)
            self.assertEqual(effects[0].gene, 'CYP4B1')
            self.assertEqual(effects[0].transcript, 'ENST00000468637')

            effects = vcffile.find_selected_transcript_effects(variant, {'WASH2P':'ENST00000542901'})
            self.assertEqual(len(effects), 1)
            self.assertEqual(effects[0].gene, 'WASH2P')
            self.assertEqual(effects[0].transcript, 'ENST00000542901')

            effects = vcffile.find_selected_transcript_effects(variant, {'ARHGEF16':'ENST00000378371',
                                                                         'WASH2P':'ENST00000542901'})
            self.assertEqual(len(effects), 2)
            self.assertEqual(effects[0].gene, 'WASH2P')
            self.assertEqual(effects[0].transcript, 'ENST00000542901')
            self.assertEqual(effects[1].gene, 'ARHGEF16')
            self.assertEqual(effects[1].transcript, 'ENST00000378371')
            
    
#class TestVcfFilesFunctions(unittest.TestCase):
#    
#    def setUp(self):
#        self.vcffiles = vcf.VcfFiles()

class TestSnpEffVcfFiles(unittest.TestCase):

    def setUp(self):
        self.example_vcf = os.path.join(RESOURCE_DIR, EXAMPLE_VARSCAN_SNPEFF_VCF)
        self.example2_vcf = os.path.join(RESOURCE_DIR, EXAMPLE2_VARSCAN_SNPEFF_VCF)
        self.vcffiles = vcf.SnpEffVcfFiles()

    def test_count_transcript_effects_single(self):

        # Test high priority = True
        vcffile = vcf.SnpEffVcfFile(self.example_vcf, 'r')
        g2t2e2c = {}
        effect2impact = {}
        self.vcffiles.count_transcript_effects_single(vcffile, g2t2e2c, effect2impact, highest_priority=True)
        self.assertEqual(len(g2t2e2c.keys()), 2)
        self.assertTrue('WASH2P' in g2t2e2c)
        self.assertEqual(g2t2e2c['WASH2P']['ENST00000542901']['SPLICE_SITE_ACCEPTOR'], 1)
        vcffile.close()
        
        # Test high priority = False
        vcffile = vcf.SnpEffVcfFile(self.example_vcf, 'r')
        g2t2e2c = {}
        effect2impact = {}
        self.vcffiles.count_transcript_effects_single(vcffile, g2t2e2c, effect2impact, highest_priority=False)
        self.assertTrue(len(g2t2e2c.keys()), 5)
        vcffile.close()

    def test_count_transcript_effects_all(self):
        # Test 2 vcf files, priority = False
        vcffile1 = vcf.SnpEffVcfFile(self.example_vcf, 'r')
        vcffile2 = vcf.SnpEffVcfFile(self.example_vcf, 'r')
        self.vcffiles.append(vcffile1)
        self.vcffiles.append(vcffile2)
        g2t2e2c, effect2impact = self.vcffiles.count_transcript_effects_all(False)
        self.assertEqual(g2t2e2c['WASH2P']['ENST00000542901']['SPLICE_SITE_ACCEPTOR'], 2)
        self.assertEqual(effect2impact['DOWNSTREAM'], 'MODIFIER')
        self.assertEqual(effect2impact['TRANSCRIPT'], 'MODIFIER')
        self.assertEqual(effect2impact['SPLICE_SITE_ACCEPTOR'], 'HIGH')
        self.assertEqual(effect2impact['UTR_5_PRIME'], 'MODIFIER')
        self.assertEqual(effect2impact['NON_SYNONYMOUS_CODING'], 'MODERATE')

        self.vcffiles = vcf.SnpEffVcfFiles()
        vcffile1 = vcf.SnpEffVcfFile(self.example_vcf, 'r')
        vcffile2 = vcf.SnpEffVcfFile(self.example2_vcf, 'r')
        self.vcffiles.append(vcffile1)
        self.vcffiles.append(vcffile2)
        g2t2e2c, effect2impact = self.vcffiles.count_transcript_effects_all(False)
        self.assertEqual(g2t2e2c['WASH2P']['ENST00000542901']['SPLICE_SITE_ACCEPTOR'], 4)
        self.assertEqual(g2t2e2c['MMP23B']['ENST00000356026']['DOWNSTREAM'], 5)
        self.assertEqual(g2t2e2c['CYP4B1']['ENST00000468637']['NON_SYNONYMOUS_CODING'], 4)
        self.assertEqual(g2t2e2c['AL691432.2']['ENST00000340677']['TRANSCRIPT'], 2)

    def test_select_transcript_for_gene(self):
        # g1 tests for most high impact count
        # g2 tests for tied high impact counts but longest transcript
        # g3 tests for same as g2
        # g4 tests for random selection for transcripts that have tied the above 2
        # g5 tests for the same thing
        # g6 tests for transcript w/o existing length
        # g7 tests for all transcripts w/o existing length
        g2t2e2c = {'g1': {'g1t1': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'START_LOST': 2,
                                  'EXON_DELETED': 5,
                                  'TRANSCRIPT': 1,},
                         'g1t2': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 20,
                                  'TRANSCRIPT': 20,},
                         'g1t3': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 200,
                                  'TRANSCRIPT': 1,}},
                  'g2': {'g2t1': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g2t2': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g2t3': {'SPLICE_SITE_ACCEPTOR': 2,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,}},
                  'g3': {'g3t1': {'SPLICE_SITE_ACCEPTOR': 2,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g3t2': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g3t3': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,}},
                  'g4': {'g4t1': {'SPLICE_SITE_ACCEPTOR': 4,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g4t2': {'SPLICE_SITE_ACCEPTOR': 4,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g4t3': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,}},
                  'g5': {'g5t1': {'SPLICE_SITE_ACCEPTOR': 4,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g5t2': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g5t3': {'SPLICE_SITE_ACCEPTOR': 4,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,}},
                  'g6': {'g6t1': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g6t2': {'SPLICE_SITE_ACCEPTOR': 4,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g6t3': {'SPLICE_SITE_ACCEPTOR': 5,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,}},
                  'g7': {'g7t1': {'SPLICE_SITE_ACCEPTOR': 4,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g7t2': {'SPLICE_SITE_ACCEPTOR': 3,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,},
                         'g7t3': {'SPLICE_SITE_ACCEPTOR': 4,
                                  'DOWNSTREAM': 2,
                                  'TRANSCRIPT': 1,}},
                  }
                  
        e2i = {'SPLICE_SITE_ACCEPTOR': 'HIGH',
               'DOWNSTREAM': 'MODIFIER',
               'TRANSCRIPT': 'MODIFIER',
               'START_LOST': 'HIGH',
               'EXON_DELETED': 'HIGH',}
        t2l = {'g1t1': 10,
               'g1t2': 10,
               'g1t3': 10,
               'g2t1': 11,
               'g2t2': 10,
               'g2t3': 10,
               'g3t1': 10,
               'g3t2': 10,
               'g3t3': 11,
               'g4t1': 10,
               'g4t2': 10,
               'g4t3': 10,
               'g5t1': 10,
               'g5t2': 10,
               'g5t3': 10,
               'g6t1': 10,
               'g6t2': 10,
               }
        snpeffvcffiles = vcf.SnpEffVcfFiles()
        g2t = snpeffvcffiles.select_transcript_for_gene(g2t2e2c, e2i, t2l)
        self.assertEqual(len(g2t), 6)
        self.assertEqual(g2t['g1'], 'g1t1')
        self.assertEqual(g2t['g2'], 'g2t1')
        self.assertEqual(g2t['g3'], 'g3t3')
        self.assertEqual(g2t['g4'], 'g4t1')
        self.assertEqual(g2t['g5'], 'g5t1')
        self.assertEqual(g2t['g6'], 'g6t2')
        self.assertTrue('g7' not in g2t)

#     def test_register_transcript_counts(self):
#         self.vcffiles.register_transcript_counts('hello', 'foo', 'bar')
#         self.assertEqual(self.vcffiles.g2t2e2c, 'hello')
#         self.assertEqual(self.vcffiles.eff2imp, 'foo')
#         self.assertEqual(self.vcffiles.transcript2len, 'bar')


if __name__ == '__main__':
    unittest.main()
