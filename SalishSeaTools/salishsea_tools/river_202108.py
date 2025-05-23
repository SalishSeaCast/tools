# Copyright 2013 – present by the SalishSeaCast contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Salish Sea NEMO Model, dictionary of the proportion
that each river occupies in the watershed.

For Bathymetry 201803
"""

prop_dict = {}
# dictionary of rivers in Howe watershed
# depth at First Narrows, Fig 4.5 Isachsen thesis
prop_dict["howe"] = {
    "Squamish": {
        "prop": 0.706947808647832,
        "i": 534,
        "j": 384,
        "di": 1,
        "dj": 2,
        "depth": 2,
    },
    "Jericho": {
        "prop": 0.002474317330267412,
        "i": 453,
        "j": 329,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "FalseCreek": {
        "prop": 0.005054676831831999,
        "i": 450,
        "j": 337,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "FirstNarrows": {
        "prop": 0.1294681892089998,
        "i": 457,
        "j": 343,
        "di": 1,
        "dj": 1,
        "depth": 8,
    },
    "Capilano": {
        "prop": 0.00918474034551144,
        "i": 458,
        "j": 343,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Lawson": {
        "prop": 0.0013338988915802515,
        "i": 461,
        "j": 341,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Marr": {
        "prop": 0.0011794866070598039,
        "i": 464,
        "j": 338,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Rodgers": {
        "prop": 0.0009074233240685963,
        "i": 465,
        "j": 337,
        "di": 2,
        "dj": 1,
        "depth": 1,
    },
    "Westmount": {
        "prop": 0.00044693984618303996,
        "i": 467,
        "j": 336,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Cypress": {
        "prop": 0.0029598788514702654,
        "i": 469,
        "j": 331,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Eagle": {
        "prop": 0.0018306227466038597,
        "i": 474,
        "j": 329,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Whyte": {
        "prop": 0.0010827463806132587,
        "i": 478,
        "j": 332,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Disbrow": {
        "prop": 0.0005525355241273846,
        "i": 481,
        "j": 337,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Sclufield": {
        "prop": 0.00044835374180033564,
        "i": 482,
        "j": 339,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Turpin": {
        "prop": 0.0014176163952359158,
        "i": 485,
        "j": 343,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Harvey": {
        "prop": 0.0038900733365332023,
        "i": 492,
        "j": 346,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Deeks": {
        "prop": 0.0032407975859592725,
        "i": 501,
        "j": 350,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Kallahn": {
        "prop": 0.0024854796640881673,
        "i": 510,
        "j": 358,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Furry": {
        "prop": 0.012349261983695549,
        "i": 515,
        "j": 364,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Britannia": {
        "prop": 0.006394156890322628,
        "i": 523,
        "j": 373,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Gonzalos": {
        "prop": 0.002790583455188811,
        "i": 527,
        "j": 381,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Shannon": {
        "prop": 0.0033375378124058178,
        "i": 529,
        "j": 386,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Stawanus": {
        "prop": 0.010745606691447047,
        "i": 530,
        "j": 387,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Woodfibre": {
        "prop": 0.013573397926038377,
        "i": 533,
        "j": 370,
        "di": 1,
        "dj": 2,
        "depth": 1,
    },
    "Foulger": {
        "prop": 0.0032147521403775104,
        "i": 530,
        "j": 367,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Ellesmere": {
        "prop": 0.0028538366801730904,
        "i": 521,
        "j": 361,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Potlatch": {
        "prop": 0.006500199061619803,
        "i": 522,
        "j": 350,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "McNab": {
        "prop": 0.013525027812815104,
        "i": 522,
        "j": 338,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Bain": {
        "prop": 0.0024817588861479156,
        "i": 522,
        "j": 326,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Rainy": {
        "prop": 0.013266433745967606,
        "i": 522,
        "j": 319,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "McNair": {
        "prop": 0.010051681605590097,
        "i": 520,
        "j": 316,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Twin": {
        "prop": 0.003638920825566209,
        "i": 513,
        "j": 313,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Langdale": {
        "prop": 0.005008167107578853,
        "i": 504,
        "j": 309,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Chester": {
        "prop": 0.004572836088569398,
        "i": 501,
        "j": 291,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Roberts": {
        "prop": 0.009084279341124641,
        "i": 512,
        "j": 282,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Rume": {
        "prop": 0.0017059766856054263,
        "i": 517,
        "j": 279,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
}

# Assume that 50% of the area of the JdF watershed defined by Morrison
# et al (2011) is on north side of JdF (Canada side)
CAFlux = 0.50
# Assume that 50% of the area of the watershed defined by Morrison et
# al (2011) is on south side of JdF (US side)
USFlux = 0.50
# dictionary of rivers in Juan de Fuca watershed
prop_dict["jdf"] = {
    "SanJuan": {
        "prop": 0.33 * CAFlux,
        "i": 401,
        "j": 62,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Gordon": {
        "prop": 0.14 * CAFlux,
        "i": 404,
        "j": 62,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Loss": {
        "prop": 0.05 * CAFlux,
        "i": 376,
        "j": 72,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Jordan": {
        "prop": 0.05 * CAFlux,
        "i": 349,
        "j": 96,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Muir": {
        "prop": 0.05 * CAFlux,
        "i": 326,
        "j": 120,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Tugwell": {
        "prop": 0.05 * CAFlux,
        "i": 325,
        "j": 121,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Sooke": {
        "prop": 0.33 * CAFlux,
        "i": 315,
        "j": 144,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Elwha": {
        "prop": 0.60 * 0.50 * USFlux,
        "i": 261,
        "j": 134,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Tumwater": {
        "prop": 0.60 * 0.01 * USFlux,
        "i": 248,
        "j": 151,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Valley": {
        "prop": 0.60 * 0.01 * USFlux,
        "i": 247,
        "j": 152,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Ennis": {
        "prop": 0.60 * 0.02 * USFlux,
        "i": 244,
        "j": 156,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Morse": {
        "prop": 0.60 * 0.07 * USFlux,
        "i": 240,
        "j": 164,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Bagley": {
        "prop": 0.60 * 0.02 * USFlux,
        "i": 239,
        "j": 165,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Siebert": {
        "prop": 0.60 * 0.02 * USFlux,
        "i": 235,
        "j": 174,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "McDonald": {
        "prop": 0.60 * 0.03 * USFlux,
        "i": 233,
        "j": 183,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "DungenessMatriotti": {
        "prop": 0.60 * 0.30 * USFlux + 0.60 * 0.02 * USFlux,
        "i": 233,
        "j": 202,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Coville": {
        "prop": 0.40 * 0.05 * USFlux,
        "i": 263,
        "j": 128,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Salt": {
        "prop": 0.40 * 0.05 * USFlux,
        "i": 275,
        "j": 116,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Field": {
        "prop": 0.40 * 0.05 * USFlux,
        "i": 281,
        "j": 101,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Lyre": {
        "prop": 0.40 * 0.20 * USFlux,
        "i": 283,
        "j": 99,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "EastWestTwin": {
        "prop": 0.40 * 0.05 * USFlux,
        "i": 293,
        "j": 82,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Deep": {
        "prop": 0.40 * 0.05 * USFlux,
        "i": 299,
        "j": 73,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Pysht": {
        "prop": 0.40 * 0.10 * USFlux,
        "i": 311,
        "j": 65,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Clallom": {
        "prop": 0.40 * 0.10 * USFlux,
        "i": 333,
        "j": 45,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Hoko": {
        "prop": 0.40 * 0.20 * USFlux,
        "i": 346,
        "j": 35,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Sekiu": {
        "prop": 0.40 * 0.10 * USFlux,
        "i": 350,
        "j": 31,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Sail": {
        "prop": 0.40 * 0.05 * USFlux,
        "i": 373,
        "j": 17,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
}

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
prop_dict["puget"] = {
    "Johnson": {
        "prop": 0.05 * WRIA17,
        "i": 208,
        "j": 202,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Jimmycomelately": {
        "prop": 0.05 * WRIA17,
        "i": 199,
        "j": 203,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "SalmonSnow": {
        "prop": 0.25 * WRIA17,
        "i": 182,
        "j": 220,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Chimacum": {
        "prop": 0.20 * WRIA17,
        "i": 184,
        "j": 240,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Thorndike": {
        "prop": 0.05 * WRIA17,
        "i": 136,
        "j": 214,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Torboo": {
        "prop": 0.05 * WRIA17,
        "i": 148,
        "j": 208,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "LittleBigQuilcene": {
        "prop": 0.35 * WRIA17,
        "i": 145,
        "j": 196,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Dosewalips": {
        "prop": 0.20 * WRIA16,
        "i": 123,
        "j": 177,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Duckabush": {
        "prop": 0.14 * WRIA16,
        "i": 118,
        "j": 167,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Fulton": {
        "prop": 0.02 * WRIA16,
        "i": 117,
        "j": 156,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Waketick": {
        "prop": 0.02 * WRIA16,
        "i": 108,
        "j": 141,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "HammaHamma": {
        "prop": 0.14 * WRIA16,
        "i": 107,
        "j": 139,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Jorsted": {
        "prop": 0.02 * WRIA16,
        "i": 104,
        "j": 135,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Eagle": {
        "prop": 0.02 * WRIA16,
        "i": 98,
        "j": 126,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Lilliwaup": {
        "prop": 0.02 * WRIA16,
        "i": 95,
        "j": 119,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Finch": {
        "prop": 0.02 * WRIA16,
        "i": 87,
        "j": 108,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Skokomish": {
        "prop": 0.40 * WRIA16,
        "i": 76,
        "j": 102,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Rendsland": {
        "prop": 0.025 * WRIA15,
        "i": 82,
        "j": 107,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Tahuya": {
        "prop": 0.20 * WRIA15,
        "i": 72,
        "j": 116,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Mission": {
        "prop": 0.05 * WRIA15,
        "i": 73,
        "j": 146,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Union": {
        "prop": 0.10 * WRIA15,
        "i": 72,
        "j": 147,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Coulter": {
        "prop": 0.05 * WRIA15,
        "i": 58,
        "j": 150,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Minter": {
        "prop": 0.05 * WRIA15,
        "i": 46,
        "j": 168,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Burley": {
        "prop": 0.05 * WRIA15,
        "i": 46,
        "j": 179,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Olalla": {
        "prop": 0.05 * WRIA15,
        "i": 48,
        "j": 198,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Blackjack": {
        "prop": 0.05 * WRIA15,
        "i": 79,
        "j": 198,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "ClearBarker": {
        "prop": 0.075 * WRIA15,
        "i": 82,
        "j": 203,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "BigValley": {
        "prop": 0.1 * WRIA15,
        "i": 109,
        "j": 220,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "BigBear": {
        "prop": 0.05 * WRIA15,
        "i": 112,
        "j": 189,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Swaback": {
        "prop": 0.025 * WRIA15,
        "i": 112,
        "j": 185,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Stavis": {
        "prop": 0.025 * WRIA15,
        "i": 113,
        "j": 175,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Anderson": {
        "prop": 0.05 * WRIA15,
        "i": 107,
        "j": 150,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Dewatta": {
        "prop": 0.05 * WRIA15,
        "i": 94,
        "j": 123,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Sherwood": {
        "prop": 0.15 * WRIA14,
        "i": 57,
        "j": 149,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "DeerJohnsGoldboroughMill": {
        "prop": 0.50 * WRIA14,
        "i": 34,
        "j": 113,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Skookum": {
        "prop": 0.10 * WRIA14,
        "i": 29,
        "j": 95,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "KennedySchneider": {
        "prop": 0.15 * WRIA14,
        "i": 23,
        "j": 89,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "PerryMcClane": {
        "prop": 0.10 * WRIA14 + 0.10 * WRIA13,
        "i": 13,
        "j": 91,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Deschutes": {
        "prop": 0.70 * WRIA13,
        "i": 4,
        "j": 100,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Woodward": {
        "prop": 0.10 * WRIA13,
        "i": 13,
        "j": 120,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Woodland": {
        "prop": 0.10 * WRIA13,
        "i": 14,
        "j": 119,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Chambers": {
        "prop": 1.0 * WRIA12,
        "i": 6,
        "j": 162,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "NisquallyMcAllister": {
        "prop": 1.0 * WRIA11,
        "i": 1,
        "j": 135,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Puyallup": {
        "prop": 0.995 * WRIA10,
        "i": 11,
        "j": 194,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Hylebas": {
        "prop": 0.005 * WRIA10,
        "i": 13,
        "j": 199,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Duwamish1": {
        "prop": 0.50 * WRIA9,
        "i": 67,
        "j": 243,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Duwamish2": {
        "prop": 0.50 * WRIA9,
        "i": 68,
        "j": 246,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "CedarSammamish": {
        "prop": 1.0 * WRIA8,
        "i": 89,
        "j": 246,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
}

WRIA4 = 0.33
WRIA3 = 0.17
WRIA5 = 0.17
WRIA7 = 0.33
prop_dict["skagit"] = {
    "Skagit1": {
        "prop": 0.5 * (WRIA4 * 1.0 + WRIA3 * 0.75),
        "i": 213,
        "j": 313,
        "di": 1,
        "dj": 1,
        "depth": 2,
    },
    "Skagit2": {
        "prop": 0.5 * (WRIA4 * 1.0 + WRIA3 * 0.75),
        "i": 229,
        "j": 310,
        "di": 1,
        "dj": 1,
        "depth": 2,
    },
    "Samish": {
        "prop": WRIA3 * 0.20,
        "i": 271,
        "j": 342,
        "di": 1,
        "dj": 1,
        "depth": 3,
    },
    "JoeLeary": {
        "prop": WRIA3 * 0.05,
        "i": 257,
        "j": 331,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Stillaguamish1": {
        "prop": 0.7 * WRIA5 * 1.0,
        "i": 183,
        "j": 308,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Stillaguamish2": {
        "prop": 0.1 * WRIA5 * 1.0,
        "i": 188,
        "j": 306,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Stillaguamish3": {
        "prop": 0.2 * WRIA5 * 1.0,
        "i": 205,
        "j": 307,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "SnohomishAllenQuilceda": {
        "prop": WRIA7 * 0.98,
        "i": 138,
        "j": 311,
        "di": 1,
        "dj": 1,
        "depth": 2,
    },
    "Tulalip": {
        "prop": WRIA7 * 0.01,
        "i": 155,
        "j": 310,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Mission": {
        "prop": WRIA7 * 0.01,
        "i": 154,
        "j": 311,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
}

WRIA1 = 0.016
Nooksack_cor = WRIA1 * 0.75 / 2040
Fraser = 1 - WRIA1 - Nooksack_cor * (116 + 149 + 60 + 31)
prop_dict["fraser"] = {
    "Serpentine": {
        "prop": 116 * Nooksack_cor,
        "i": 390,
        "j": 350,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Nicomekl": {
        "prop": 149 * Nooksack_cor,
        "i": 388,
        "j": 350,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "LittleCampbell": {
        "prop": 60 * Nooksack_cor,
        "i": 372,
        "j": 357,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Colebrook": {
        "prop": 31 * Nooksack_cor,
        "i": 390,
        "j": 346,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Dakota": {
        "prop": WRIA1 * 0.06,
        "i": 365,
        "j": 357,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Terrel": {
        "prop": WRIA1 * 0.04,
        "i": 353,
        "j": 349,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Nooksack": {
        "prop": WRIA1 * 0.75 / 2.0,
        "i": 308,
        "j": 356,
        "di": 1,
        "dj": 2,
        "depth": 1,
    },
    "NooksackW": {
        "prop": WRIA1 * 0.75 / 4.0,
        "i": 309,
        "j": 349,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "NooksackE": {
        "prop": WRIA1 * 0.75 / 4.0,
        "i": 308,
        "j": 361,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Squallum": {
        "prop": WRIA1 * 0.05,
        "i": 305,
        "j": 365,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Lakethingo": {
        "prop": WRIA1 * 0.06,
        "i": 303,
        "j": 367,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Chuckanut": {
        "prop": WRIA1 * 0.04,
        "i": 298,
        "j": 361,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Fraser": {
        "prop": Fraser,
        "i": 500,
        "j": 394,
        "di": 1,
        "dj": 1,
        "depth": 3,
    },
}

totalarea = 9709.0
prop_dict["evi_n"] = {
    "Oyster": {
        "prop": 363 / totalarea,
        "i": 705,
        "j": 123,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Qunisam": {
        "prop": 1470 / totalarea,
        "i": 750,
        "j": 123,
        "di": 2,
        "dj": 1,
        "depth": 1,
    },
    "Snowden": {
        "prop": 139 / totalarea,
        "i": 771,
        "j": 116,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Menzies": {
        "prop": 31 / totalarea,
        "i": 774,
        "j": 115,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Creek1": {
        "prop": 23 / totalarea,
        "i": 788,
        "j": 123,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Creek2": {
        "prop": 16 / totalarea,
        "i": 796,
        "j": 126,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Creek3": {
        "prop": 23 / totalarea,
        "i": 799,
        "j": 127,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Elk": {"prop": 23 / totalarea, "i": 808, "j": 126, "di": 1, "dj": 1, "depth": 1},
    "Slab": {"prop": 12 / totalarea, "i": 813, "j": 128, "di": 1, "dj": 1, "depth": 1},
    "Pye": {"prop": 109 / totalarea, "i": 826, "j": 121, "di": 1, "dj": 1, "depth": 1},
    "BearPoint": {
        "prop": 12 / totalarea,
        "i": 839,
        "j": 108,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "AmordeCosmos": {
        "prop": 229 / totalarea,
        "i": 843,
        "j": 96,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Humpback": {
        "prop": 10 / totalarea,
        "i": 844,
        "j": 94,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Palmer": {"prop": 14 / totalarea, "i": 845, "j": 92, "di": 1, "dj": 1, "depth": 1},
    "Hkusam": {"prop": 14 / totalarea, "i": 849, "j": 87, "di": 1, "dj": 1, "depth": 1},
    "CampPoint": {
        "prop": 28 / totalarea,
        "i": 857,
        "j": 78,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "SalmonSayward": {
        "prop": (1210 + 14) / totalarea,
        "i": 865,
        "j": 64,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Kelsey": {"prop": 7 / totalarea, "i": 878, "j": 58, "di": 1, "dj": 1, "depth": 1},
    "unmarked": {
        "prop": 7 / totalarea,
        "i": 884,
        "j": 53,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Newcastle": {
        "prop": 34 / totalarea,
        "i": 890,
        "j": 47,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Windy": {"prop": 10 / totalarea, "i": 891, "j": 46, "di": 1, "dj": 1, "depth": 1},
}


# Jervis Inlet only area = 1400km2 (Trites 1955) ==> 25% of Jervis
# watershed
Jervis = 0.25
prop_dict["jervis"] = {
    "SkwawkaHunaechin": {
        "prop": Jervis * 0.20,
        "i": 692,
        "j": 332,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Loquilts": {
        "prop": Jervis * 0.04,
        "i": 674,
        "j": 346,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Potato": {
        "prop": Jervis * 0.04,
        "i": 666,
        "j": 349,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Deserted": {
        "prop": Jervis * 0.10,
        "i": 653,
        "j": 353,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Stakawus": {
        "prop": Jervis * 0.04,
        "i": 651,
        "j": 346,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Crabapple": {
        "prop": Jervis * 0.04,
        "i": 665,
        "j": 342,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Osgood": {
        "prop": Jervis * 0.04,
        "i": 652,
        "j": 323,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Lausmann": {
        "prop": Jervis * 0.03,
        "i": 690,
        "j": 332,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Slane": {
        "prop": Jervis * 0.03,
        "i": 687,
        "j": 331,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Smanit": {
        "prop": Jervis * 0.04,
        "i": 681,
        "j": 334,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Glacial": {
        "prop": Jervis * 0.05,
        "i": 649,
        "j": 310,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Seshal": {
        "prop": Jervis * 0.05,
        "i": 652,
        "j": 318,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Brittain": {
        "prop": Jervis * 0.10,
        "i": 652,
        "j": 301,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "VancouverHigh": {
        "prop": Jervis * 0.10,
        "i": 628,
        "j": 312,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Perketts": {
        "prop": Jervis * 0.05,
        "i": 619,
        "j": 307,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Treat": {
        "prop": Jervis * 0.05,
        "i": 612,
        "j": 302,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Sechelt": {
        "prop": 0.17,
        "i": 593,
        "j": 285,
        "di": 1,
        "dj": 1,
        "depth": 3,
    },
    "Powell": {
        "prop": 0.32,
        "i": 667,
        "j": 203,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Lois": {
        "prop": 0.10,
        "i": 629,
        "j": 227,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Haslam": {
        "prop": 0.02,
        "i": 633,
        "j": 219,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Chapman": {
        "prop": 0.016,
        "i": 522,
        "j": 273,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Lapan": {
        "prop": 0.02,
        "i": 620,
        "j": 283,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Nelson": {
        "prop": 0.02,
        "i": 604,
        "j": 262,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Wakefield": {
        "prop": 0.02,
        "i": 534,
        "j": 264,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Halfmoon": {
        "prop": 0.02,
        "i": 549,
        "j": 254,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "MyersKleindaleAnderson": {
        "prop": 0.04,
        "i": 571,
        "j": 248,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Wilson": {
        "prop": 0.004,
        "i": 521,
        "j": 274,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
}
# Wilson area = 24.58 km2, Jervis ws is 5785 km2 so 0.004 (take out of Chapman)


prop_dict["toba"] = {
    "Toba": {
        "prop": 0.50,
        "i": 775,
        "j": 311,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Theodosia": {
        "prop": 0.12,
        "i": 713,
        "j": 197,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Quatam": {
        "prop": 0.09,
        "i": 794,
        "j": 211,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Brem": {
        "prop": 0.09,
        "i": 785,
        "j": 260,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Tahumming": {
        "prop": 0.08,
        "i": 777,
        "j": 309,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Racine": {
        "prop": 0.04,
        "i": 770,
        "j": 272,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Homfray": {
        "prop": 0.03,
        "i": 754,
        "j": 245,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Forbes": {
        "prop": 0.03,
        "i": 742,
        "j": 247,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Chusan": {
        "prop": 0.02,
        "i": 773,
        "j": 307,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
}

prop_dict["bute"] = {
    "Homathko": {
        "prop": 0.58,
        "i": 896,
        "j": 293,
        "di": 1,
        "dj": 3,
        "depth": 2,
    },
    "Southgate": {
        "prop": 0.35,
        "i": 885,
        "j": 297,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Orford": {
        "prop": 0.07,
        "i": 830,
        "j": 250,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
}

prop_dict["evi_s"] = {
    "Cowichan1": {
        "prop": 0.5 * 0.22,
        "i": 383,
        "j": 201,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Cowichan2": {
        "prop": 0.5 * 0.22,
        "i": 382,
        "j": 200,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Chemanius1": {
        "prop": 0.5 * 0.13,
        "i": 415,
        "j": 213,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Chemanius2": {
        "prop": 0.5 * 0.13,
        "i": 418,
        "j": 212,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Nanaimo1": {
        "prop": 0.67 * 0.14,
        "i": 479,
        "j": 210,
        "di": 1,
        "dj": 2,
        "depth": 1,
    },
    "Nanaimo2": {
        "prop": 0.33 * 0.14,
        "i": 478,
        "j": 211,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "NorNanaimo": {
        "prop": 0.02,
        "i": 486,
        "j": 208,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Goldstream": {
        "prop": 0.08,
        "i": 329,
        "j": 182,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Nanoose": {
        "prop": 0.02,
        "i": 520,
        "j": 183,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Englishman": {
        "prop": 0.05,
        "i": 542,
        "j": 175,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "FrenchCreek": {
        "prop": 0.01,
        "i": 551,
        "j": 168,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "LittleQualicum": {
        "prop": 0.05,
        "i": 564,
        "j": 149,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Qualicum": {
        "prop": 0.02,
        "i": 578,
        "j": 138,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "SouthDenman": {
        "prop": 0.05,
        "i": 602,
        "j": 122,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Tsable": {
        "prop": 0.03,
        "i": 616,
        "j": 120,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Trent": {
        "prop": 0.01,
        "i": 649,
        "j": 121,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "Puntledge": {
        "prop": 0.14,
        "i": 654,
        "j": 120,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
    "BlackCreek": {
        "prop": 0.03,
        "i": 701,
        "j": 123,
        "di": 1,
        "dj": 1,
        "depth": 1,
    },
}
