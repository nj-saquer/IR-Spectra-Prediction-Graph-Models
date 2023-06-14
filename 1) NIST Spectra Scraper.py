#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download all IR spectra available from NIST Chemistry Webbook."""
import os
import re

import requests
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool
import tqdm


NIST_URL = 'http://webbook.nist.gov/cgi/cbook.cgi'
EXACT_RE = re.compile('/cgi/cbook.cgi\?GetInChI=(.*?)$')
ID_RE = re.compile('/cgi/cbook.cgi\?ID=(.*?)&')
#NOTE: Change these
JDX_PATH = 'jdx'
MOL_PATH = 'mol'

def search_nist_formula(formula, allow_other = False, allow_extra = False, match_isotopes = True, exclude_ions = False, has_ir = True):
    """Search NIST using the specified formula query and return the matching NIST IDs."""
    #print('Searching: %s' % formula)
    params = {'Formula': formula, 'Units': 'SI'}
    if allow_other:
        params['AllowOther'] = 'on'
    if allow_extra:
        params['AllowExtra'] = 'on'
    if match_isotopes:
        params['MatchIso'] = 'on'
    if exclude_ions:
        params['NoIon'] = 'on'
    if has_ir:
        params['cIR'] = 'on'
    response = requests.get(NIST_URL, params=params)
    soup = BeautifulSoup(response.text)
    ids = [re.match(ID_RE, link['href']).group(1) for link in soup('a', href = ID_RE)]
    #print('Result: %s' % ids)
    return ids


def get_jdx(nistid, stype = "IR"):
    """Download jdx file for the specified NIST ID, unless already downloaded."""
    filepath = os.path.join(JDX_PATH, '%s-%s.jdx' % (nistid, stype))
    if os.path.isfile(filepath):
        #print('%s %s: Already exists at %s' % (nistid, stype, filepath))
        return
    #print('%s %s: Downloading' % (nistid, stype))
    response = requests.get(NIST_URL, params={'JCAMP': nistid, 'Type': stype, 'Index': 0})
    if response.text == '##TITLE=Spectrum not found.\n##END=\n':
        #print('%s %s: Spectrum not found' % (nistid, stype))
        return
    #print('Saving %s' % filepath)
    with open(filepath, 'wb') as file:
        file.write(response.content)


def get_mol(nistid):
    """Download mol file for the specified NIST ID, unless already downloaded."""
    filepath = os.path.join(MOL_PATH, '%s.mol' % nistid)
    if os.path.isfile(filepath):
        #print('%s: Already exists at %s' % (nistid, filepath))
        return
    print('%s: Downloading mol' % nistid)
    response = requests.get(NIST_URL, params={'Str2File': nistid})
    if response.text == 'NIST    12121112142D 1   1.00000     0.00000\nCopyright by the U.S. Sec. Commerce on behalf of U.S.A. All rights reserved.\n0  0  0     0  0              1 V2000\nM  END\n':
        #print('%s: MOL not found' % nistid)
        return
    print('Saving %s' % filepath)
    with open(filepath, 'wb') as file:
        file.write(response.content)

def retreive_data_from_formula(formula):
    ids = search_nist_formula(formula, allow_other = True, exclude_ions = False, has_ir = True)
    for nistid in ids:
        get_mol(nistid)
        get_jdx(nistid)

def get_all_IR():
    """Search NIST for all structures with IR Spectra and download a JDX + Mol file for each."""
    formulae = []
    IDs = []
    with open("species.txt") as data_file:
        entries = data_file.readlines()
        for entry in entries:
            try:
                formulae.append(entry.split()[-2])
            except:
                IDs.append(entry.strip())
    """
    #NOTE: Change threadpool as you need
    with ThreadPool(8) as pool:
        list(tqdm.tqdm(pool.imap(retreive_data_from_formula, formulae)))
    print("Done with formulas!")
    """
    for nistid in IDs:
        get_mol(nistid)
        get_jdx(nistid)
    print("Done Scraping Data!")
if __name__ == '__main__':
    get_all_IR()
