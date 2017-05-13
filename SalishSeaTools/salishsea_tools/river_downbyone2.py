# Copyright 2013-2016 The Salish Sea MEOPAR contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Salish Sea NEMO Model, dictionary of the proportion
that each river occupies in the watershed.

For Bathymetry DownbyOneGrid2
"""

prop_dict = {}
# dictionary of rivers in Howe watershed
prop_dict['howe'] = {
    'Squamish': {
        'prop': 0.9, 'i': 532, 'j': 385, 'di': 1, 'dj': 2, 'depth': 3,
            },
    'Burrard': {
        'prop': 0.1, 'i': 457, 'j': 343, 'di': 3, 'dj': 1, 'depth': 3,
            }}

# Assume that 50% of the area of the JdF watershed defined by Morrison
# et al (2011) is on north side of JdF (Canada side)
CAFlux = 0.50
# Assume that 50% of the area of the watershed defined by Morrison et
# al (2011) is on south side of JdF (US side)
USFlux = 0.50
# dictionary of rivers in Juan de Fuca watershed
prop_dict['jdf'] = {
    'SanJuan': {
        'prop': 0.33 * CAFlux, 'i': 402, 'j': 56, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Gordon': {
        'prop': 0.14 * CAFlux, 'i': 403, 'j': 56, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Loss': {
        'prop': 0.05 * CAFlux, 'i': 375, 'j': 71, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Jordan': {
        'prop': 0.05 * CAFlux, 'i': 348, 'j': 96, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Muir': {
        'prop': 0.05 * CAFlux, 'i': 326, 'j': 119, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Tugwell': {
        'prop': 0.05 * CAFlux, 'i': 325, 'j': 120, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Sooke': {
        'prop': 0.33 * CAFlux, 'i': 308, 'j': 137, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Elwha': {
        'prop': 0.60 * 0.50 * USFlux, 'i': 261, 'j': 134, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Tumwater': {
        'prop': 0.60 * 0.01 * USFlux, 'i': 248, 'j': 151, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Valley': {
        'prop': 0.60 * 0.01 * USFlux, 'i': 247, 'j': 152, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Ennis': {
        'prop': 0.60 * 0.02 * USFlux, 'i': 244, 'j': 156, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Morse': {
        'prop': 0.60 * 0.07 * USFlux, 'i': 240, 'j': 164, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Bagley': {
        'prop': 0.60 * 0.02 * USFlux, 'i': 239, 'j': 165, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Siebert': {
        'prop': 0.60 * 0.02 * USFlux, 'i': 235, 'j': 174, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'McDonald': {
        'prop': 0.60 * 0.03 * USFlux, 'i': 233, 'j': 183, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'DungenessMatriotti': {
        'prop': 0.60 * 0.30 * USFlux + 0.60 * 0.02 * USFlux, 'i': 231, 'j': 201, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Coville': {
        'prop': 0.40 * 0.05 * USFlux, 'i': 263, 'j': 128, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Salt': {
        'prop': 0.40 * 0.05 * USFlux, 'i': 275, 'j': 116, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Field': {
        'prop': 0.40 * 0.05 * USFlux, 'i': 281, 'j': 100, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Lyre': {
        'prop': 0.40 * 0.20 * USFlux, 'i': 283, 'j': 98, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'EastWestTwin': {
        'prop': 0.40 * 0.05 * USFlux, 'i': 293, 'j': 81, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Deep': {
        'prop': 0.40 * 0.05 * USFlux, 'i': 299, 'j': 72, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Pysht': {
        'prop': 0.40 * 0.10 * USFlux, 'i': 310, 'j': 65, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Clallom': {
        'prop': 0.40 * 0.10 * USFlux, 'i': 333, 'j': 45, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Hoko': {
        'prop': 0.40 * 0.20 * USFlux, 'i': 345, 'j': 35, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Sekiu': {
        'prop': 0.40 * 0.10 * USFlux, 'i': 348, 'j': 31, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Sail': {
        'prop': 0.40 * 0.05 * USFlux, 'i': 373, 'j': 17, 'di': 1, 'dj': 1, 'depth': 3,
            }}

# WRIA17 10% of Puget Sound Watershed
WRIA17 = 0.10
# WRIA16 10% of Puget Sound Watershed
WRIA16 = 0.10
# WRIA15 15% of Puget Sound Watershed
WRIA15 = 0.15
# WRIA14 5% of Puget Sound Watershed
WRIA14 = 0.05
# WRIA13 3% of Puget Sound Watershed
WRIA13 = 0.03
# WRIA12 2% of Puget Sound Watershed
WRIA12 = 0.02
# WRIA11 15% of Puget Sound Watershed
WRIA11 = 0.15
# WRIA10 20% of Puget Sound Watershed
WRIA10 = 0.20
# WRIA9 10% of Puget Sound Watershed
WRIA9 = 0.10
# WRIA8 10% of Puget Sound Watershed
WRIA8 = 0.10
prop_dict['puget'] = {
    'Johnson': {
        'prop': 0.05 * WRIA17, 'i': 207, 'j': 202, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Jimmycomelately': {
        'prop': 0.05 * WRIA17, 'i': 199, 'j': 202, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'SalmonSnow': {
        'prop': 0.25 * WRIA17, 'i': 182, 'j': 219, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Chimacum': {
        'prop': 0.20 * WRIA17, 'i': 185, 'j': 240, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Thorndike': {
        'prop': 0.05 * WRIA17, 'i': 137, 'j': 215, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Torboo': {
        'prop': 0.05 * WRIA17, 'i': 149, 'j': 208, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'LittleBigQuilcene': {
        'prop': 0.35 * WRIA17, 'i': 146, 'j': 199, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Dosewalips': {
        'prop': 0.20 * WRIA16, 'i': 124, 'j': 177, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Duckabush': {
        'prop': 0.14 * WRIA16, 'i': 119, 'j': 167, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Fulton': {
        'prop': 0.02 * WRIA16, 'i': 116, 'j': 156, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Waketick': {
        'prop': 0.02 * WRIA16, 'i': 108, 'j': 141, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'HammaHamma': {
        'prop': 0.14 * WRIA16, 'i': 107, 'j': 139, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Jorsted': {
        'prop': 0.02 * WRIA16, 'i': 104, 'j': 135, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Eagle': {
        'prop': 0.02 * WRIA16, 'i': 98, 'j': 127, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Lilliwaup': {
        'prop': 0.02 * WRIA16, 'i': 95, 'j': 118, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Finch': {
        'prop': 0.02 * WRIA16, 'i': 87, 'j': 108, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Skokomish': {
        'prop': 0.40 * WRIA16, 'i': 75, 'j': 103, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Rendsland': {
        'prop': 0.025 * WRIA15, 'i': 81, 'j': 107, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Tahuya': {
        'prop': 0.20 * WRIA15, 'i': 72, 'j': 114, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Mission': {
        'prop': 0.05 * WRIA15, 'i': 73, 'j': 149, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Union': {
        'prop': 0.10 * WRIA15, 'i': 74, 'j': 153, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Coulter': {
        'prop': 0.05 * WRIA15, 'i': 64, 'j': 153, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Minter': {
        'prop': 0.05 * WRIA15, 'i': 46, 'j': 168, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Butley': {
        'prop': 0.05 * WRIA15, 'i': 47, 'j': 178, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Olalla': {
        'prop': 0.05 * WRIA15, 'i': 48, 'j': 197, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'BlackjackClearBarkerBigValley1': {
        'prop': 0.1125 * WRIA15, 'i': 68, 'j': 210, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'BlackjackClearBarkerBigValley2': {
        'prop': 0.1125 * WRIA15, 'i': 108, 'j': 232, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'BigBear': {
        'prop': 0.05 * WRIA15, 'i': 112, 'j': 189, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Swaback': {
        'prop': 0.025 * WRIA15, 'i': 112, 'j': 185, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Stavis': {
        'prop': 0.025 * WRIA15, 'i': 113, 'j': 174, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Anderson': {
        'prop': 0.05 * WRIA15, 'i': 107, 'j': 150, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Dewatta': {
        'prop': 0.05 * WRIA15, 'i': 94, 'j': 122, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Sherwood': {
        'prop': 0.15 * WRIA14, 'i': 60, 'j': 149, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'DeerJohnsGoldboroughMillSkookumKennedySchneider': {
        'prop': 0.375 * WRIA14, 'i': 47, 'j': 130, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'DeerJohnsGoldboroughMillSkookumKennedySchneiderPerry': {
        'prop': 0.475 * WRIA14, 'i': 20, 'j': 120, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'McClaneDeschutesWoodwardWoodland': {
        'prop': 1.0 * WRIA13, 'i': 22, 'j': 121, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Chambers': {
        'prop': 1.0 * WRIA12, 'i': 6, 'j': 162, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'NisquallyMcAllister': {
        'prop': 1.0 * WRIA11, 'i': 0, 'j': 137, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Puyallup': {
        'prop': 0.995 * WRIA10, 'i': 10, 'j': 195, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Hylebas': {
        'prop': 0.005 * WRIA10, 'i': 13, 'j': 199, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Duwamish1': {
        'prop': 0.50 * WRIA9, 'i': 68, 'j': 243, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Duwamish2': {
        'prop': 0.50 * WRIA9, 'i': 68, 'j': 246, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'CedarSammamish': {
        'prop': 1.0 * WRIA8, 'i': 88, 'j': 246, 'di': 1, 'dj': 1, 'depth': 3,
            }}

WRIA4 = 0.33
WRIA3 = 0.17
WRIA5 = 0.17
WRIA7 = 0.33
prop_dict['skagit'] = {
    'Skagit1': {
        'prop': 0.5 * (WRIA4 * 1.0 + WRIA3 * 0.75), 'i': 207, 'j': 326, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Skagit2': {
        'prop': 0.5 * (WRIA4 * 1.0 + WRIA3 * 0.75), 'i': 229, 'j': 319, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Samish': {
        'prop': WRIA3 * 0.20, 'i': 265, 'j': 348, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'JoeLeary': {
        'prop': WRIA3 * 0.05, 'i': 257, 'j': 339, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Stillaguamish1': {
        'prop': 0.7 * WRIA5 * 1.0, 'i': 186, 'j': 316, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Stillaguamish2': {
        'prop': 0.1 * WRIA5 * 1.0, 'i': 192, 'j': 315, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Stillaguamish3': {
        'prop': 0.2 * WRIA5 * 1.0, 'i': 200, 'j': 318, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'SnohomishAllenQuilceda': {
        'prop': WRIA7 * 0.98, 'i': 143, 'j': 318, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Tulalip': {
        'prop': WRIA7 * 0.01, 'i': 154, 'j': 311, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Mission': {
    'prop': WRIA7 * 0.01, 'i': 152, 'j': 312, 'di': 1, 'dj': 1, 'depth': 3,
            }}

WRIA1 = 0.016
Fraser = 1 - WRIA1
prop_dict['fraser'] = {
    'Dakota': {
        'prop': WRIA1 * 0.06, 'i': 362, 'j': 357,
                'di': 1, 'dj': 1, 'depth': 3,
            },
    'Terrel': {
        'prop': WRIA1 * 0.04, 'i': 351, 'j': 345,
                'di': 1, 'dj': 1, 'depth': 3,
            },
    'Nooksack': {
        'prop': WRIA1 * 0.75, 'i': 321, 'j': 347,
                'di': 1, 'dj': 1, 'depth': 3,
            },
    'Squallum': {
        'prop': WRIA1 * 0.05, 'i': 305, 'j': 365,
                'di': 1, 'dj': 1, 'depth': 3,
            },
    'Lakethingo': {
        'prop': WRIA1 * 0.06, 'i': 302, 'j': 367,
                'di': 1, 'dj': 1, 'depth': 3,
            },
    'Chuckanut': {
        'prop': WRIA1 * 0.04, 'i': 298, 'j': 361,
                'di': 1, 'dj': 1, 'depth': 3,
            },
    'Fraser1': {
        'prop': Fraser * 0.75, 'i': 500, 'j': 395,
                'di': 1, 'dj': 1, 'depth': 3,
            },              # Fraser1 is main arm
    'Fraser2': {
        'prop': Fraser * 0.05, 'i': 409, 'j': 315,
                'di': 2, 'dj': 1, 'depth': 3,
            },   # Fraser2 was Deas, moved to Canoe Pass
    'Fraser3': {
        'prop': Fraser * 0.05, 'i': 434, 'j': 318,
                'di': 2, 'dj': 1, 'depth': 3,
            },              # Fraser3 is Middle arm
    'Fraser4': {
    'prop': Fraser * 0.15, 'i': 440, 'j': 323,
                'di': 1, 'dj': 2, 'depth': 3,
            }}              # Fraser4 is North arm


totalarea = 9709.0
prop_dict['evi_n'] = {
    'Oyster': {
        'prop': 363 / totalarea, 'i': 705, 'j': 122, 'di': 1, 'dj': 1, 'depth': 3},
    'Qunisam': {
        'prop': 1470 / totalarea, 'i': 749, 'j': 123, 'di': 2, 'dj': 1, 'depth': 3},
    'Snowden': {
        'prop': 139 / totalarea, 'i': 770, 'j': 117, 'di': 1, 'dj': 1, 'depth': 3},
    'Menzies': {
        'prop': 31 / totalarea, 'i': 773, 'j': 117, 'di': 1, 'dj': 1, 'depth': 3},
    'Creek1': {
        'prop': 23 / totalarea, 'i': 786, 'j': 123, 'di': 1, 'dj': 1, 'depth': 3},
    'Creek2': {
        'prop': 16 / totalarea, 'i': 795, 'j': 126, 'di': 1, 'dj': 1, 'depth': 3},
    'Creek3': {
        'prop': 23 / totalarea, 'i': 798, 'j': 127, 'di': 1, 'dj': 1, 'depth': 3},
    'Elk': {
        'prop': 23 / totalarea, 'i': 807, 'j': 127, 'di': 1, 'dj': 1, 'depth': 3},
    'Slab': {
        'prop': 12 / totalarea, 'i': 813, 'j': 129, 'di': 1, 'dj': 1, 'depth': 3},
    'Pye': {
        'prop': 109 / totalarea, 'i': 826, 'j': 121, 'di': 1, 'dj': 1, 'depth': 3},
    'BearPoint': {
        'prop': 12 / totalarea, 'i': 839, 'j': 107, 'di': 1, 'dj': 1, 'depth': 3},
    'AmordeCosmos': {
        'prop': 229 / totalarea, 'i': 843, 'j': 96, 'di': 1, 'dj': 1, 'depth': 3},
    'Humpback': {
        'prop': 10 / totalarea, 'i': 844, 'j': 93, 'di': 1, 'dj': 1, 'depth': 3},
    'Palmer': {
        'prop': 14 / totalarea, 'i': 845, 'j': 92, 'di': 1, 'dj': 1, 'depth': 3},
    'Hkusam': {
        'prop': 14 / totalarea, 'i': 848, 'j': 87, 'di': 1, 'dj': 1, 'depth': 3},
    'CampPoint': {
        'prop': 28 / totalarea, 'i': 858, 'j': 77, 'di': 1, 'dj': 1, 'depth': 3},
    'SalmonSayward': {
        'prop': (1210 + 14) / totalarea, 'i': 866, 'j': 64, 'di': 1, 'dj': 1, 'depth': 3},
    'Kelsey': {
        'prop': 7 / totalarea, 'i': 878, 'j': 59, 'di': 1, 'dj': 1, 'depth': 3},
    'unmarked': {
        'prop': 7 / totalarea, 'i': 884, 'j': 54, 'di': 1, 'dj': 1, 'depth': 3},
    'Newcastle': {
        'prop': 34 / totalarea,
                                   'i': 890, 'j': 47,
                                   'di': 1, 'dj': 1, 'depth': 3},
    'Windy': {
        'prop': 10 / totalarea, 'i': 891, 'j': 45,
                                  'di': 1, 'dj': 1, 'depth': 3}}


# Jervis Inlet only area = 1400km2 (Trites 1955) ==> 25% of Jervis
# watershed
Jervis = 0.25
prop_dict['jervis'] = {
    'SkwawkaLoquiltsPotatoDesertedStakawusCrabappleOsgood': {
        'prop': Jervis * 0.60, 'i': 650, 'j': 309, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Glacial': {
        'prop': Jervis * 0.05, 'i': 649, 'j': 310, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Seshal': {
        'prop': Jervis * 0.05, 'i': 651, 'j': 307, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Brittain': {
        'prop': Jervis * 0.10, 'i': 650, 'j': 301, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'VancouverHigh': {
        'prop': Jervis * 0.10, 'i': 626, 'j': 311, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Perketts': {
        'prop': Jervis * 0.05, 'i': 619, 'j': 307, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Treat': {
        'prop': Jervis * 0.05, 'i': 612, 'j': 301, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Sechelt': {
        'prop': 0.17, 'i': 604, 'j': 280, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Powell': {
        'prop': 0.32, 'i': 666, 'j': 202, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Lois': {
        'prop': 0.10, 'i': 629, 'j': 224, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Haslam': {
        'prop': 0.02, 'i': 632, 'j': 219, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Chapman': {
        'prop': 0.02, 'i': 522, 'j': 273, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Lapan': {
        'prop': 0.02, 'i': 619, 'j': 282, 'di': 1, 'dj': 1, 'depth': 3,
    },
    'Nelson': {
        'prop': 0.02, 'i': 599, 'j': 257, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Wakefield': {
        'prop': 0.02, 'i': 533, 'j': 263, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Halfmoon': {
        'prop': 0.02, 'i': 549, 'j': 253, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'MyersKleindaleAnderson': {
        'prop': 0.04, 'i': 571, 'j': 248, 'di': 1, 'dj': 1, 'depth': 3,
            }}

prop_dict['toba'] = {
    'Toba': {
        'prop': 1.0, 'i': 746, 'j': 240, 'di': 1, 'dj': 3, 'depth': 3,
            }}

prop_dict['bute'] = {
    'Homathko': {
        'prop': 0.58, 'i': 897, 'j': 294, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Southgate': {
        'prop': 0.35, 'i': 885, 'j': 296, 'di': 1, 'dj': 2, 'depth': 3,
            },
    'Orford': {
        'prop': 0.07, 'i': 831, 'j': 249, 'di': 1, 'dj': 1, 'depth': 3,
            }}

prop_dict['evi_s'] = {
    'Cowichan': {
        'prop': 0.22, 'i': 383, 'j': 201, 'di': 1, 'dj': 2, 'depth': 3,
            },
    'Chemanius1': {
        'prop': 0.5 * 0.13, 'i': 414, 'j': 211, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Chemanius2': {
        'prop': 0.5 * 0.13, 'i': 417, 'j': 212, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Nanaimo1': {
        'prop': 0.67 * 0.14, 'i': 478, 'j': 208, 'di': 1, 'dj': 2, 'depth': 3,
            },
    'Nanaimo2': {
        'prop': 0.33 * 0.14, 'i': 477, 'j': 210, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'NorNanaimo': {
        'prop': 0.02, 'i': 491, 'j': 213, 'di': 3, 'dj': 1, 'depth': 3,
            },
    'Goldstream': {
        'prop': 0.08, 'i': 334, 'j': 185, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Nanoose': {
        'prop': 0.02, 'i': 518, 'j': 185, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Englishman': {
        'prop': 0.05, 'i': 541, 'j': 175, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'FrenchCreek': {
        'prop': 0.01, 'i': 551, 'j': 168, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'LittleQualicum': {
        'prop': 0.05, 'i': 563, 'j': 150, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Qualicum': {
        'prop': 0.02, 'i': 578, 'j': 137, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'SouthDenman': {
        'prop': 0.05, 'i': 602, 'j': 120, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Tsable': {
        'prop': 0.03, 'i': 616, 'j': 120, 'di': 2, 'dj': 1, 'depth': 3,
            },
    'Trent': {
        'prop': 0.01, 'i': 648, 'j': 121, 'di': 1, 'dj': 1, 'depth': 3,
            },
    'Puntledge': {
        'prop': 0.14, 'i': 656, 'j': 119, 'di': 1, 'dj': 2, 'depth': 3,
            },
    'BlackCreek': {
        'prop': 0.03, 'i': 701, 'j': 123, 'di': 1, 'dj': 1, 'depth': 3,
            }}
