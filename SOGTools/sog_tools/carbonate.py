# Copyright 2015-2016 Ben Moore-Maley and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Carbonate system calculations for post-processing SOG bloomcast results.

All calculations adapted from CO2SYS v1.1
Lewis, E., and D. W. R. Wallace. 1998. Program Developed for
CO2 System Calculations. ORNL/CDIAC-105. Carbon Dioxide Information
Analysis Center, Oak Ridge National Laboratory, U.S. Department of Energy,
Oak Ridge, Tennessee.
http://cdiac.ornl.gov/oceans/co2rprt.html
"""

import numpy as np


def calc_carbonate(values, TP, TSi, T, S, P, params=['TA', 'TC']):
    """Calculate carbonate system parameters given two inputs

    :arg values: List of input values or arrays corresponding to params arg
    :type values: list of :py:class:`numpy.ndarray`

    :arg TP: Total phosphate [umol kg-1]
    :type TP: :py:class:`numpy.ndarray` or scalar

    :arg TSi: Dissolved silica [umol kg-1]
    :type TSi: :py:class:`numpy.ndarray` or scalar

    :arg T: in situ temperature [deg C]
    :type T: :py:class:`numpy.ndarray` or scalar

    :arg S: Practical salinity
    :type S: :py:class:`numpy.ndarray` or scalar

    :arg P: Pressure [dbar]
    :type P: :py:class:`numpy.ndarray` or scalar

    :arg params: List of parameter flags corresponding to values arg
                 (one of 'TC', 'TA', 'pH', 'pCO2', 'OmegaA')
    :type params: list of str

    :returns: A dictionary containing all of the 5 carbonate system parameters
              accepted as input arguments
    """

    global K0, K1, K2

    # Calculate rho
    TempK = T + 273.15

    # Convert from uM to mol/kg
    TP = TP * 1.0e-6
    TSi = TSi * 1.0e-6

    # Set equilibrium constants
    set_constants(S, TempK, P)
    Ca, KCa, KAr = CaSolubility(S, TempK, P)

    # Assign inputs
    for param, val in zip(params, values):
        if param is 'TA':
            TA = val * 1.0e-6
        elif param is 'TC':
            TC = val * 1.0e-6
        elif param is 'pH':
            pH = val
        elif param is 'pCO2':
            pCO2 = val * 1.0e-6
        elif param is 'OmegaA':
            OmegaA = val
            CO3 = OmegaA * KAr / Ca
        else:
            raise ValueError('Unknown CO2 parameter: {}'.format(param))

    # Calculate pH
    if 'TA' in params and 'TC' in params:
        pH = CalculatepHfromTA('TC', TA, TC, TP, TSi)
    elif 'TA' in params and 'pCO2' in params:
        pH = CalculatepHfromTA('pCO2', TA, pCO2, TP, TSi)
    elif 'TA' in params and 'OmegaA' in params:
        pH = CalculatepHfromTA('CO3', TA, CO3, TP, TSi)
    elif 'TC' in params and 'pCO2' in params:
        RR = K0 * pCO2 / TC
        Discr = (K1 * RR) * (K1 * RR) + 4 * (1 - RR) * (K1 * K2 * RR)
        H = 0.5 * (K1 * RR + np.sqrt(Discr)) / (1 - RR)
        pH = np.log(H) / np.log(0.1)
    elif 'TC' in params and 'OmegaA' in params:
        HCO3 = K1 * CO3 / (2 * K2) * (
            np.sqrt(4 * K2 / K1 * (TC / CO3 - 1) + 1) - 1
        )
        H = K2 * HCO3 / CO3
        pH = np.log(H) / np.log(0.1)
    elif 'pCO2' in params and 'OmegaA' in params:
        TC = np.sqrt(K0 * K1 / K2 * pCO2 * CO3) + K0 * pCO2 + CO3
        H = K0 * K1 * pCO2 / (TC - K0 * pCO2 - CO3)
        pH = np.log(H) / np.log(0.1)

    # Fill in remaining params
    H, Beta = CalculateHfrompH(pH)
    NCAlk = CalculateNCAlkfrompH(H, TP, TSi)
    if 'pH' in params and 'pCO2' in params:
        TC = K0 * pCO2 * (1 + K1 / H + K1 * K2 / (H * H))
    elif 'pH' in params and 'OmegaA' in params:
        TC = CO3 * (H * H / (K1 * K2) + H / K2 + 1)
    if 'TA' in params:
        CAlk = TA - NCAlk
        TC = CAlk * Beta / (K1 * (H + 2 * K2))
    else:
        CAlk = TC * K1 * (H + 2 * K2) / Beta
        TA = CAlk + NCAlk
    pCO2 = TC * H * H / Beta / K0
    CO3 = TC * K1 * K2 / Beta
    OmegaA = Ca * CO3 / KAr

    # Unit conversions and dict out
    Calc_values = {
        'TA': TA * 1e6,
        'TC': TC * 1e6,
        'pH': pH,
        'pCO2': pCO2 * 1e6,
        'OmegaA': OmegaA,
    }

    return Calc_values


def set_constants(Sal, TempK, Pdbar):
    """Variable & parameter value declarations, and subroutines related
    to carbonate system calculations in the SOG code

    Constants and alkalinity parametrizations taken from CO2SYS v1.1
    Lewis, E., and D. W. R. Wallace. 1998. Program Developed for
    CO2 System Calculations. ORNL/CDIAC-105. Carbon Dioxide Information
    Analysis Center, Oak Ridge National Laboratory,
    U.S. Department of Energy, Oak Ridge, Tennessee.
    http://cdiac.ornl.gov/oceans/co2rprt.html
    """

    # Declare global constants
    global R_gas, fH, K0, K1, K2, KW, KB, KF, KS, KP1, KP2, KP3, KSi, TB, TS, TF

    # Gas Constant
    R_gas = 83.1451  # ml bar-1 K-1 mol-1, DOEv2

    # Preallocate common operations
    Pbar = Pdbar / 10.0
    TempK100 = TempK / 100.0
    logTempK = np.log(TempK)
    sqrSal = np.sqrt(Sal)

    # Calculate IonS:
    # This is from the DOE handbook, Chapter 5, p. 13/22, eq. 7.2.4:
    IonS = 19.924 * Sal / (1000.0 - 1.005 * Sal)
    sqrIonS = np.sqrt(IonS)

    # Calculate H ion activity coefficient
    fH = 1.2948 - 0.002036 * TempK + (
        0.0004607 - 0.000001475 * TempK
    ) * Sal**2

    # CALCULATE SEAWATER CONSTITUENTS USING EMPIRCAL FITS
    # Calculate total borate:
    # Uppstrom, L., Deep-Sea Research 21:161-162, 1974:
    # this is 0.000416 * Sali / 35 = 0.0000119 * Sali
    # TB = (0.000232d0 / 10.811d0) * (Sal / 1.80655d0) ! in mol/kg-SW
    TB = 0.0004157 * Sal / 35.0    # in mol/kg-SW

    # Calculate total sulfate:
    # Morris, A. W., and Riley, J. P., Deep-Sea Research 13:699-705, 1966:
    # this is .02824 * Sali / 35 = .0008067 * Sali
    TS = (0.14 / 96.062) * (Sal / 1.80655)     # in mol/kg-SW

    # Calculate total fluoride: (in mol/kg-SW)
    # Riley, J. P., Deep-Sea Research 12:219-220, 1965:
    # this is .000068 * Sali / 35 = .00000195 * Sali
    # Approximate [F-] of Fraser River is 3 umol/kg
    TF = np.maximum((0.000067 / 18.998) * (Sal / 1.80655), 3.0e-6)

    # CALCULATE EQUILIBRIUM CONSTANTS (SW scale)
    # Calculate KS:
    # Dickson, A. G., J. Chemical Thermodynamics, 22:113-127, 1990
    # The goodness of fit is .021.
    # It was given in mol/kg-H2O. I convert it to mol/kg-SW.
    # TYPO on p. 121: the constant e9 should be e8.
    # This is from eqs 22 and 23 on p. 123, and Table 4 on p 121:
    lnKS = (
        -4276.1 / TempK + 141.328 - 23.093 * logTempK +
        (-13856.0 / TempK + 324.57 - 47.986 * logTempK) * sqrIonS +
        (35474.0 / TempK - 771.54 + 114.723 * logTempK) * IonS +
        (-2698.0 / TempK) * sqrIonS * IonS + (1776.0 / TempK) * IonS**2
    )
    KS = (
        np.exp(lnKS)              # this is on the free pH scale in mol/kg-H2O
        * (1.0 - 0.001005 * Sal)  # convert to mol/kg-SW
    )

    # Calculate KF:
    # Dickson, A. G. and Riley, J. P., Marine Chemistry 7:89-99, 1979:
    lnKF = 1590.2 / TempK - 12.641 + 1.525 * sqrIonS
    KF = (
        np.exp(lnKF)              # this is on the free pH scale in mol/kg-H2O
        * (1.0 - 0.001005 * Sal)  # convert to mol/kg-SW
    )

    # Calculate pH scale conversion factors ( NOT pressure-corrected)
    SWStoTOT = (1 + TS / KS) / (1 + TS / KS + TF / KF)

    # Calculate K0:
    # Weiss, R. F., Marine Chemistry 2:203-215, 1974.
    lnK0 = (
        -60.2409 + 93.4517 / TempK100 + 23.3585 * np.log(TempK100) +
        Sal * (0.023517 - 0.023656 * TempK100 + 0.0047036 * TempK100**2)
    )
    K0 = np.exp(lnK0)  # this is in mol/kg-SW/atm

    # From Millero, 2010, also for estuarine use.
    # Marine and Freshwater Research, v. 61, p. 139-142.
    # Fits through compilation of real seawater titration results:
    # Mehrbach et al. (1973), Mojica-Prieto & Millero (2002),
    # Millero et al. (2006)
    # Constants for K's on the SWS;
    # This is from page 141
    pK10 = -126.34048 + 6320.813 / TempK + 19.568224 * np.log(TempK)
    # This is from their table 2, page 140.
    A1 = 13.4038 * Sal**0.5 + 0.03206 * Sal - 5.242e-5 * Sal**2
    B1 = -530.659 * Sal**0.5 - 5.8210 * Sal
    C1 = -2.0664 * Sal**0.5
    pK1 = pK10 + A1 + B1 / TempK + C1 * np.log(TempK)
    K1 = 10**(-pK1)
    # This is from page 141
    pK20 = -90.18333 + 5143.692 / TempK + 14.613358 * np.log(TempK)
    # This is from their table 3, page 140.
    A2 = 21.3728 * Sal**0.5 + 0.1218 * Sal - 3.688e-4 * Sal**2
    B2 = -788.289 * Sal**0.5 - 19.189 * Sal
    C2 = -3.374 * Sal**0.5
    pK2 = pK20 + A2 + B2 / TempK + C2 * np.log(TempK)
    K2 = 10**(-pK2)

    # Calculate KW:
    # Millero, Geochemica et Cosmochemica Acta 59:661-677, 1995.
    # his check value of 1.6 umol/kg-SW should be 6.2
    lnKW = (
        148.9802 - 13847.26 / TempK - 23.6521 * logTempK +
        (-5.977 + 118.67 / TempK + 1.0495 * logTempK) * sqrSal -
        0.01615 * Sal
    )
    KW = np.exp(lnKW)    # this is on the SWS pH scale in (mol/kg-SW)^2

    # Calculate KB:
    # Dickson, A. G., Deep-Sea Research 37:755-766, 1990:
    lnKB = (
        (-8966.9 - 2890.53 * sqrSal - 77.942 * Sal +
            1.728 * sqrSal * Sal - 0.0996 * Sal**2) / TempK +
        148.0248 + 137.1942 * sqrSal + 1.62142 * Sal +
        (-24.4344 - 25.085 * sqrSal - 0.2474 * Sal) * logTempK +
        0.053105 * sqrSal * TempK
    )
    KB = (
        np.exp(lnKB)  # this is on the total pH scale in mol/kg-SW
        / SWStoTOT    # convert to SWS pH scale
    )

    # Calculate KP1, KP2, KP3, and KSi:
    # Yao and Millero, Aquatic Geochemistry 1:53-88, 1995
    # KP1, KP2, KP3 are on the SWS pH scale in mol/kg-SW.
    # KSi was given on the SWS pH scale in molal units.
    lnKP1 = (
        -4576.752 / TempK + 115.54 - 18.453 * logTempK +
        (-106.736 / TempK + 0.69171) * sqrSal +
        (-0.65643 / TempK - 0.01844) * Sal
    )
    KP1 = np.exp(lnKP1)

    lnKP2 = (
        -8814.715 / TempK + 172.1033 - 27.927 * logTempK +
        (-160.34 / TempK + 1.3566) * sqrSal +
        (0.37335 / TempK - 0.05778) * Sal
    )
    KP2 = np.exp(lnKP2)

    lnKP3 = (
        -3070.75 / TempK - 18.126 +
        (17.27039 / TempK + 2.81197) * sqrSal +
        (-44.99486 / TempK - 0.09984) * Sal
    )
    KP3 = np.exp(lnKP3)

    lnKSi = (
        -8904.2 / TempK + 117.4 - 19.334 * logTempK +
        (-458.79 / TempK + 3.5913) * sqrIonS +
        (188.74 / TempK - 1.5998) * IonS +
        (-12.1652 / TempK + 0.07871) * IonS**2
    )
    KSi = (
        np.exp(lnKSi)             # this is on the SWS pH scale in mol/kg-H2O
        * (1.0 - 0.001005 * Sal)  # convert to mol/kg-SW
    )

    # Correct constants for pressure
    pressure_corrections(TempK, Pbar)


def pressure_corrections(TempK, Pbar):
    """Calculate pressure corrections for constants defined in set_constants
    """

    # Declare global constants
    global R_gas, fH, K1, K2, KW, KB, KF, KS, KP1, KP2, KP3, KSi, TB, TS, TF

    # Temperature and gas constant
    RT = R_gas * TempK
    TempC = TempK - 273.15

    # Fugacity Factor
    Delta = 57.7 - 0.118 * TempK
    b = (
        -1636.75 + 12.0408 * TempK - 0.0327957 * TempK**2 +
        3.16528 * 1.0e-5 * TempK**3
    )
    FugFac = np.exp((b + 2.0 * Delta) * 1.01325 / RT)

    # Pressure effects on K1 & K2:
    # These are from Millero, 1995.
    # They are the same as Millero, 1979 and Millero, 1992.
    # They are from data of Culberson and Pytkowicz, 1968.
    deltaV = -25.5 + 0.1271 * TempC
    # deltaV = deltaV - 0.151 * (Sal - 34.8)   # Millero, 1979
    Kappa = (-3.08 + 0.0877 * TempC) / 1000.0
    # Kappa = Kappa - 0.578 * (Sal - 34.8) / 1000  # Millero, 1979
    lnK1fac = (-deltaV + 0.5 * Kappa * Pbar) * Pbar / RT
    # The fits given in Millero, 1983 are somewhat different.
    deltaV = -15.82 - 0.0219 * TempC
    # deltaV = deltaV + 0.321 * (Sal - 34.8)  # Millero, 1979
    Kappa = (1.13 - 0.1475 * TempC) / 1000.0
    # Kappa = Kappa - 0.314 * (Sal - 34.8) / 1000  # Millero, 1979
    lnK2fac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT
    # The fit given in Millero, 1983 is different.
    # Not by a lot for deltaV, but by much for Kappa.

    # Pressure effects on KW:
    # This is from Millero, 1983 and his programs CO2ROY(T).BAS.
    deltaV = -20.02 + 0.1119 * TempC - 0.001409 * TempC**2
    # Millero, 1992 and Millero, 1995 have:
    Kappa = (-5.13 + 0.0794 * TempC) / 1000.0  # Millero, 1983
    # Millero, 1995 has this too, but Millero, 1992 is different.
    lnKWfac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT
    # Millero, 1979 does not list values for these.

    # Pressure effects on KB:
    # This is from Millero, 1979.
    # It is from data of Culberson and Pytkowicz, 1968.
    deltaV = -29.48 + 0.1622 * TempC - 0.002608 * TempC**2
    # deltaV = -28.56 + 0.1211 * TempC - 0.000321 * TempC**2  # Millero, 1983
    # deltaV = -29.48 + 0.1622 * TempC + 0.295 * (Sal - 34.8) # Millero, 1992
    # deltaV = -29.48 - 0.1622 * TempC - 0.002608 * TempC**2  # Millero, 1995
    # deltaV = deltaV + 0.295 * (Sal - 34.8)                  # Millero, 1979
    Kappa = -2.84 / 1000.0    # Millero, 1979
    # Millero, 1992 and Millero, 1995 also have this.
    # Kappa = Kappa + 0.354 * (Sal - 34.8) / 1000  # Millero, 1979
    # Kappa = (-3.0 + 0.0427 * TempC) / 1000   # Millero, 1983
    lnKBfac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT

    # Pressure effects on KF & KS:
    # These are from Millero, 1995, which is the same as Millero, 1983.
    # It is assumed that KF and KS are on the free pH scale.
    deltaV = -9.78 - 0.009 * TempC - 0.000942 * TempC**2
    Kappa = (-3.91 + 0.054 * TempC) / 1000.0
    lnKFfac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT
    deltaV = -18.03 + 0.0466 * TempC + 0.000316 * TempC**2
    Kappa = (-4.53 + 0.09 * TempC) / 1000.0
    lnKSfac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT

    # Correct KP1, KP2, & KP3 for pressure:
    # The corrections for KP1, KP2, and KP3 are from Millero, 1995,
    # which are the same as Millero, 1983.
    deltaV = -14.51 + 0.1211 * TempC - 0.000321 * TempC**2
    Kappa = (-2.67 + 0.0427 * TempC) / 1000.0
    lnKP1fac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT
    deltaV = -23.12 + 0.1758 * TempC - 0.002647 * TempC**2
    Kappa = (-5.15 + 0.09 * TempC) / 1000.0
    lnKP2fac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT
    deltaV = -26.57 + 0.202 * TempC - 0.003042 * TempC**2
    Kappa = (-4.08 + 0.0714 * TempC) / 1000.0
    lnKP3fac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT

    # Pressure effects on KSi:
    # The only mention of this is Millero, 1995 where it is stated that the
    # values have been estimated from the values of boric acid. HOWEVER,
    # there is no listing of the values in the table.
    # I used the values for boric acid from above.
    deltaV = -29.48 + 0.1622 * TempC - 0.002608 * TempC**2
    Kappa = -2.84 / 1000.0
    lnKSifac = (-1.0 * deltaV + 0.5 * Kappa * Pbar) * Pbar / RT

    # Correct K's for pressure here:
    K1 = K1 * np.exp(lnK1fac)
    K2 = K2 * np.exp(lnK2fac)
    KW = KW * np.exp(lnKWfac)
    KB = KB * np.exp(lnKBfac)
    KF = KF * np.exp(lnKFfac)
    KS = KS * np.exp(lnKSfac)
    KP1 = KP1 * np.exp(lnKP1fac)
    KP2 = KP2 * np.exp(lnKP2fac)
    KP3 = KP3 * np.exp(lnKP3fac)
    KSi = KSi * np.exp(lnKSifac)


def CalculatepHfromTA(param, TA, val, TP, TSi):
    """ SUB CalculatepHfromTATC, version 04.01, 10-13-96, written by Ernie Lewis.
    Inputs: TA, TC, TP, TSi
    Output: pH
    This calculates pH from TA and TC using K1 and K2 by Newton's method.
    It tries to solve for the pH at which Residual = 0.
    The starting guess is pH = 8.
    Though it is coded for H on the total pH scale, for the pH values
    occuring in seawater (pH > 6) it will be equally valid on any pH scale
    (H terms negligible) as long as the K Constants are on that scale.
    """

    # Declare global constants
    global K0, K1, K2, KW, KB

    # Set iteration parameters
    pHGuess = 8.0         # this is the first guess
    pHTol = 1.0e-4        # tolerance for iterations end
    ln10 = np.log(10.0)
    # creates a vector holding the first guess for all samples
    if hasattr(TA, 'shape'):
        pH = np.ones(TA.shape) * pHGuess
    else:
        pH = pHGuess
    deltapH = pHTol + 1.0

    # Begin iteration to find pH
    while np.any(abs(deltapH) > pHTol):
        H, Beta = CalculateHfrompH(pH)
        NCAlk = CalculateNCAlkfrompH(H, TP, TSi)

        if param is 'TC':
            CAlk = val * K1 * (H + 2 * K2) / Beta
            # find Slope dTA/dpH (not exact, but keeps all important terms)
            Slope = ln10 * (
                val * K1 * H * (H * H + K1 * K2 + 4.0 * H * K2)
                / Beta / Beta + TB * KB * H / (KB + H) / (KB + H) + KW / H + H
            )
        elif param is 'pCO2':
            HCO3 = K0 * K1 * val / H
            CO3 = K0 * K1 * K2 * val / (H * H)
            CAlk = HCO3 + 2 * CO3
            # find Slope dTA/dpH (not exact, but keeps all important terms)
            Slope = ln10 * (
                HCO3 + 4 * CO3 + TB * KB * H / (KB + H) / (KB + H) + KW / H + H
            )
        elif param is 'CO3':
            HCO3 = H * val / K2
            CAlk = HCO3 + 2 * val
            # find Slope dTA/dpH (not exact, but keeps all important terms)
            Slope = ln10 * (
                HCO3 + 4 * CO3 + TB * KB * H / (KB + H) / (KB + H) + KW / H + H
            )
        else:
            raise ValueError('Unknown carbon param: {}'.format(param))

        TA_calc = CAlk + NCAlk
        Residual = TA - TA_calc
        deltapH = Residual / Slope   # this is Newton's method
        # to keep the jump from being too big
        while np.any(abs(deltapH) > 1):
            deltapH = deltapH / 2.0
        pH = pH + deltapH  # Is on the same scale as K1 and K2 were calculated

    return pH


def CalculateNCAlkfrompH(H, TP, TSi):
    """SUB CalculateNCAlkfrompH, adapted from CO2SYS written by Ernie Lewis.
    Inputs: pH, TP, TSi
    Output: NCAlk
    This calculates NCAlk from pH.
    Though it is coded for H on the total pH scale, for the pH values occuring
    in seawater (pH > 6) it will be equally valid on any pH scale (H terms
    negligible) as long as the K Constants are on that scale.
    """

    global K1, K2, KW, KB, KF, KS, KP1, KP2, KP3, KSi, TB, TS, TF

    BAlk = TB * KB / (KB + H)
    OH = KW / H
    PhosTop = KP1 * KP2 * H + 2 * KP1 * KP2 * KP3 - H * H * H
    PhosBot = H * H * H + KP1 * H * H + KP1 * KP2 * H + KP1 * KP2 * KP3
    PAlk = TP * PhosTop / PhosBot
    SiAlk = TSi * KSi / (KSi + H)
    FREEtoTOT = (1 + TS / KS)  # pH scale conversion factor
    Hfree = H / FREEtoTOT  # for H on the total scale
    HSO4 = TS / (1 + KS / Hfree)  # since KS is on the free scale
    HF = TF / (1 + KF / Hfree)  # since KF is on the free scale
    NCAlk = BAlk + OH + PAlk + SiAlk - Hfree - HSO4 - HF

    return NCAlk


def CalculateHfrompH(pH):
    """
    """

    global K1, K2

    H = 10**(-pH)
    Beta = H * H + K1 * H + K1 * K2

    return H, Beta


def CaSolubility(S, TempK, P):
    """Taken from CO2SYS subfunction CaSolubility
    ***********************************************************************
    SUB CaSolubility, version 01.05, 05-23-97, written by Ernie Lewis.
    Inputs: Sal, TempCi, Pdbari, TCi, pHi, K1, K2
    Outputs: OmegaCa, OmegaAr
    This calculates omega, the solubility ratio, for calcite and aragonite.
    This is defined by: Omega = [CO3--]*[Ca++]./Ksp,
          where Ksp is the solubility product (either KCa or KAr).
    ***********************************************************************
    These are from:
    Mucci, Alphonso, The solubility of calcite and aragonite in seawater
          at various salinities, temperatures, and one atmosphere total
          pressure, American Journal of Science 283:781-799, 1983.
    Ingle, S. E., Solubility of calcite in the ocean,
          Marine Chemistry 3:301-319, 1975,
    Millero, Frank, The thermodynamics of the carbonate system in seawater,
          Geochemica et Cosmochemica Acta 43:1651-1661, 1979.
    Ingle et al, The solubility of calcite in seawater at atmospheric
          pressure and 35%o salinity, Marine Chemistry 1:295-307, 1973.
    Berner, R. A., The solubility of calcite and aragonite in seawater in
          atmospheric pressure and 34.5%o salinity, American Journal of
          Science 276:713-730, 1976.
    Takahashi et al, in GEOSECS Pacific Expedition, v. 3, 1982.
    Culberson, C. H. and Pytkowicz, R. M., Effect of pressure on carbonic
          acid, boric acid, and the pHi of seawater, Limnology and
          Oceanography, 13:403-417, 1968.
    ***********************************************************************
    """

    # Declare global constants
    global R_gas, fH, K1, K2, KW, KB, KF, KS, KP1, KP2, KP3, KSi, TB, TS, TF

    # Precalculate quantities
    TempC = TempK - 273.15
    logTempK = np.log(TempK)
    sqrtS = np.sqrt(S)

    # Calculate Ca^2+:
    # Riley, J. P. and Tongudai, M., Chemical Geology 2:263-269, 1967:
    # this is 0.010285 * S / 35
    Ca = 0.02128 / 40.087 * (S / 1.80655)

    # Calcite solubility:
    # Mucci, Alphonso, Amer. J. of Science 283:781-799, 1983.
    KCa = 10.0**(
        -171.9065 - 0.077993 * TempK + 2839.319 / TempK
        + 71.595 * logTempK / np.log(10.0)
        + (-0.77712 + 0.0028426 * TempK + 178.34 / TempK) * sqrtS
        - 0.07711 * S + 0.0041249 * sqrtS * S
    )

    # Aragonite solubility:
    # Mucci, Alphonso, Amer. J. of Science 283:781-799, 1983.
    KAr = 10.0**(
        -171.945 - 0.077993 * TempK + 2903.293 / TempK
        + 71.595 * logTempK / np.log(10.0)
        + (-0.068393 + 0.0017276 * TempK + 88.135 / TempK) * sqrtS
        - 0.10018 * S + 0.0059415 * sqrtS * S
    )

    # Pressure correction for calcite:
    # Ingle, Marine Chemistry 3:301-319, 1975
    # same as in Millero, GCA 43:1651-1661, 1979, but Millero, GCA 1995
    # has typos (-0.5304, -0.3692, and 10^3 for Kappa factor)
    deltaV_KCa = -48.76 + 0.5304 * TempC
    Kappa_KCa = (-11.76 + 0.3692 * TempC) / 1000.0
    KCa = KCa * np.exp(
        (-deltaV_KCa + 0.5 * Kappa_KCa * P) * P / (R_gas * TempK)
    )

    # Pressure correction for aragonite:
    # Millero, Geochemica et Cosmochemica Acta 43:1651-1661, 1979,
    # same as Millero, GCA 1995 except for typos (-0.5304, -0.3692,
    # and 10^3 for Kappa factor)
    deltaV_KAr = deltaV_KCa + 2.8
    Kappa_KAr = Kappa_KCa
    KAr = KAr * np.exp(
        (-deltaV_KAr + 0.5 * Kappa_KAr * P) * P / (R_gas * TempK)
    )

    # Calculate Omegas:
    # H = 10.0**(-pH)
    # CO3 = DIC * K1 * K2 / (K1 * H + H * H + K1 * K2)
    # Omega_C = CO3 * Ca / KCa
    # Omega_A = CO3 * Ca / KAr

    return Ca, KCa, KAr


def FindpHOnAllScales(pH_in, T, S, P, scale='total'):
    """ SUB FindpHOnAllScales, version 01.02, 01-08-97, written by Ernie Lewis.
    Inputs: pH, scale
    Outputs: pH dict containing all scales
    """

    # Declare global constants
    global R_gas, fH, K1, K2, KW, KB, KF, KS, KP1, KP2, KP3, KSi, TB, TS, TF

    TempK = T + 273.15
    set_constants(S, TempK, P)

    # pH scale conversion factors
    FREEtoTOT = (1 + TS / KS)
    SWStoTOT = (1 + TS / KS) / (1 + TS / KS + TF / KF)

    # Determine input pH scale
    if scale is 'total':
        factor = 0
    elif scale is 'seawater':
        factor = -np.log(SWStoTOT) / np.log(0.1)
    elif scale is 'free':
        factor = -np.log(FREEtoTOT) / np.log(0.1)
    elif scale is 'NBS':
        factor = -np.log(SWStoTOT) / np.log(0.1) + np.log(fH) / np.log(0.1)
    else:
        raise ValueError('Unrecongnized pH scale: {}'.format(scale))

    # Calculate pH on all scales
    pH = {}
    pH['total'] = pH_in - factor
    pH['free'] = pH['total'] - np.log(FREEtoTOT) / np.log(0.1)
    pH['seawater'] = pH['total'] - np.log(SWStoTOT) / np.log(0.1)
    pH['NBS'] = (
        pH['total'] - np.log(SWStoTOT) / np.log(0.1) + np.log(fH) / np.log(0.1)
    )

    return pH
