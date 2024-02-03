# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from enum import Enum, unique
import QuantLib as ql


@unique
class Currency(Enum):
    AFN = 971  # Afghani
    EUR = 978  # Euro
    ALL = 8  # Lek
    DZD = 12  # Algerian Dinar
    USD = 840  # US Dollar
    AOA = 973  # Kwanza
    XCD = 951  # East Caribbean Dollar
    ARS = 32  # Argentine Peso
    AMD = 51  # Armenian Dram
    AWG = 533  # Aruban Florin
    AUD = 36  # Australian Dollar
    AZN = 944  # Azerbaijan Manat
    BSD = 44  # Bahamian Dollar
    BHD = 48  # Bahraini Dinar
    BDT = 50  # Taka
    BBD = 52  # Barbados Dollar
    BYN = 933  # Belarusian Ruble
    BZD = 84  # Belize Dollar
    XOF = 952  # CFA Franc BCEAO
    BMD = 60  # Bermudian Dollar
    INR = 356  # Indian Rupee
    BTN = 64  # Ngultrum
    BOB = 68  # Boliviano
    BOV = 984  # Mvdol
    BAM = 977  # Convertible Mark
    BWP = 72  # Pula
    NOK = 578  # Norwegian Krone
    BRL = 986  # Brazilian Real
    BND = 96  # Brunei Dollar
    BGN = 975  # Bulgarian Lev
    BIF = 108  # Burundi Franc
    CVE = 132  # Cabo Verde Escudo
    KHR = 116  # Riel
    XAF = 950  # CFA Franc BEAC
    CAD = 124  # Canadian Dollar
    KYD = 136  # Cayman Islands Dollar
    CLP = 152  # Chilean Peso
    CLF = 990  # Unidad de Fomento
    CNY = 156  # Yuan Renminbi
    COP = 170  # Colombian Peso
    COU = 970  # Unidad de Valor Real
    KMF = 174  # Comorian Franc
    CDF = 976  # Congolese Franc
    NZD = 554  # New Zealand Dollar
    CRC = 188  # Costa Rican Colon
    CUP = 192  # Cuban Peso
    CUC = 931  # Peso Convertible
    ANG = 532  # Netherlands Antillean Guilder
    CZK = 203  # Czech Koruna
    DKK = 208  # Danish Krone
    DJF = 262  # Djibouti Franc
    DOP = 214  # Dominican Peso
    EGP = 818  # Egyptian Pound
    SVC = 222  # El Salvador Colon
    ERN = 232  # Nakfa
    SZL = 748  # Lilangeni
    ETB = 230  # Ethiopian Birr
    FKP = 238  # Falkland Islands Pound
    FJD = 242  # Fiji Dollar
    XPF = 953  # CFP Franc
    GMD = 270  # Dalasi
    GEL = 981  # Lari
    GHS = 936  # Ghana Cedi
    GIP = 292  # Gibraltar Pound
    GTQ = 320  # Quetzal
    GBP = 826  # Pound Sterling
    GNF = 324  # Guinean Franc
    GYD = 328  # Guyana Dollar
    HTG = 332  # Gourde
    HNL = 340  # Lempira
    HKD = 344  # Hong Kong Dollar
    HUF = 348  # Forint
    ISK = 352  # Iceland Krona
    IDR = 360  # Rupiah
    XDR = 960  # SDR (Special Drawing Right)
    IRR = 364  # Iranian Rial
    IQD = 368  # Iraqi Dinar
    ILS = 376  # New Israeli Sheqel
    JMD = 388  # Jamaican Dollar
    JPY = 392  # Yen
    JOD = 400  # Jordanian Dinar
    KZT = 398  # Tenge
    KES = 404  # Kenyan Shilling
    KPW = 408  # North Korean Won
    KRW = 410  # Won
    KWD = 414  # Kuwaiti Dinar
    KGS = 417  # Som
    LAK = 418  # Lao Kip
    LBP = 422  # Lebanese Pound
    LSL = 426  # Loti
    ZAR = 710  # Rand
    LRD = 430  # Liberian Dollar
    LYD = 434  # Libyan Dinar
    CHF = 756  # Swiss Franc
    MOP = 446  # Pataca
    MKD = 807  # Denar
    MGA = 969  # Malagasy Ariary
    MWK = 454  # Malawi Kwacha
    MYR = 458  # Malaysian Ringgit
    MVR = 462  # Rufiyaa
    MRU = 929  # Ouguiya
    MUR = 480  # Mauritius Rupee
    XUA = 965  # ADB Unit of Account
    MXN = 484  # Mexican Peso
    MXV = 979  # Mexican Unidad de Inversion (UDI)
    MDL = 498  # Moldovan Leu
    MNT = 496  # Tugrik
    MAD = 504  # Moroccan Dirham
    MZN = 943  # Mozambique Metical
    MMK = 104  # Kyat
    NAD = 516  # Namibia Dollar
    NPR = 524  # Nepalese Rupee
    NIO = 558  # Cordoba Oro
    NGN = 566  # Naira
    OMR = 512  # Rial Omani
    PKR = 586  # Pakistan Rupee
    PAB = 590  # Balboa
    PGK = 598  # Kina
    PYG = 600  # Guarani
    PEN = 604  # Peruvian Sol
    PHP = 608  # Philippine Peso
    PLN = 985  # Zloty
    QAR = 634  # Qatari Rial
    RON = 946  # Romanian Leu
    RUB = 643  # Russian Ruble
    RWF = 646  # Rwanda Franc
    SHP = 654  # Saint Helena Pound
    WST = 882  # Tala
    STN = 930  # Dobra
    SAR = 682  # Saudi Riyal
    RSD = 941  # Serbian Dinar
    SCR = 690  # Seychelles Rupee
    SLL = 694  # Leone
    SLE = 925  # Leone
    SGD = 702  # Singapore Dollar
    SBD = 90  # Solomon Islands Dollar
    SOS = 706  # Somali Shilling
    SSP = 728  # South Sudanese Pound
    LKR = 144  # Sri Lanka Rupee
    SDG = 938  # Sudanese Pound
    SRD = 968  # Surinam Dollar
    SEK = 752  # Swedish Krona
    CHE = 947  # WIR Euro
    CHW = 948  # WIR Franc
    SYP = 760  # Syrian Pound
    TWD = 901  # New Taiwan Dollar
    TJS = 972  # Somoni
    TZS = 834  # Tanzanian Shilling
    THB = 764  # Baht
    TOP = 776  # Pa’anga
    TTD = 780  # Trinidad and Tobago Dollar
    TND = 788  # Tunisian Dinar
    TRY = 949  # Turkish Lira
    TMT = 934  # Turkmenistan New Manat
    UGX = 800  # Uganda Shilling
    UAH = 980  # Hryvnia
    AED = 784  # UAE Dirham
    USN = 997  # US Dollar (Next day)
    UYU = 858  # Peso Uruguayo
    UYI = 940  # Uruguay Peso en Unidades Indexadas (UI)
    UYW = 927  # Unidad Previsional
    UZS = 860  # Uzbekistan Sum
    VUV = 548  # Vatu
    VES = 928  # Bolívar Soberano
    VED = 926  # Bolívar Soberano
    VND = 704  # Dong
    YER = 886  # Yemeni Rial
    ZMW = 967  # Zambian Kwacha
    ZWL = 932  # Zimbabwe Dollar

    def to_ql(self) -> ql.Currency:
        """
        Get an equivalent QuantLib object.
        Example usage: Currency.EUR.to_ql()
        """
        return get_ql_currency(self)


# lookup map for QuantLib currency objects
_ql_currencies_map = {}


def _init_ql_currencies_map():
    for ccy in Currency:
        ql_module_ccy_name = ccy.name + "Currency"
        if not hasattr(ql, ql_module_ccy_name):
            # TODO handle currencies that QuantLib does not define
            # print(f"Missing {ccy}")
            continue
        # print(f"Adding  {ccy}")
        ccy_func = getattr(ql, ql_module_ccy_name)
        ql_ccy = ccy_func()
        code = ql_ccy.code()
        _ql_currencies_map[code] = ql_ccy


def get_ql_currency(ccy: Currency):
    """
    Lookup QuantLib currency object given string code like GBP
    """
    if not _ql_currencies_map:
        _init_ql_currencies_map()
    return _ql_currencies_map.get(ccy.name, None)


def get_ql_currency_from_str(currency_code: str):
    """
    Lookup QuantLib currency object given string code like GBP
    """
    if not _ql_currencies_map:
        _init_ql_currencies_map()
    return _ql_currencies_map.get(currency_code, None)
