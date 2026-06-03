"""Data seed awal: universe saham IDX (LQ45 + mid-cap likuid).

Diselaraskan dengan frontend/src/lib/watchlist.ts (80 emiten). Ticker disimpan
tanpa sufiks ".JK"; backend menambahkannya saat fetch ke Yahoo Finance.
"""

from __future__ import annotations

# (ticker, name, sector)
IDX_STOCKS: list[tuple[str, str, str]] = [
    # --- Banking & Finance ---
    ("BBCA", "Bank Central Asia", "Banking & Finance"),
    ("BBRI", "Bank Rakyat Indonesia", "Banking & Finance"),
    ("BMRI", "Bank Mandiri", "Banking & Finance"),
    ("BBNI", "Bank Negara Indonesia", "Banking & Finance"),
    ("BRIS", "Bank Syariah Indonesia", "Banking & Finance"),
    ("BBTN", "Bank Tabungan Negara", "Banking & Finance"),
    ("ARTO", "Bank Jago", "Banking & Finance"),
    ("BTPS", "Bank BTPN Syariah", "Banking & Finance"),
    ("AGRO", "Bank Raya Indonesia", "Banking & Finance"),
    # --- Telco, Media & Tech ---
    ("TLKM", "Telkom Indonesia", "Telco, Media & Tech"),
    ("EXCL", "XL Axiata", "Telco, Media & Tech"),
    ("ISAT", "Indosat Ooredoo Hutchison", "Telco, Media & Tech"),
    ("TOWR", "Sarana Menara Nusantara", "Telco, Media & Tech"),
    ("MTEL", "Dayamitra Telekomunikasi", "Telco, Media & Tech"),
    ("TBIG", "Tower Bersama Infrastructure", "Telco, Media & Tech"),
    ("GOTO", "GoTo Gojek Tokopedia", "Telco, Media & Tech"),
    ("BUKA", "Bukalapak.com", "Telco, Media & Tech"),
    ("EMTK", "Elang Mahkota Teknologi", "Telco, Media & Tech"),
    ("MNCN", "Media Nusantara Citra", "Telco, Media & Tech"),
    ("SCMA", "Surya Citra Media", "Telco, Media & Tech"),
    # --- Consumer & Retail ---
    ("UNVR", "Unilever Indonesia", "Consumer & Retail"),
    ("ICBP", "Indofood CBP Sukses Makmur", "Consumer & Retail"),
    ("INDF", "Indofood Sukses Makmur", "Consumer & Retail"),
    ("MYOR", "Mayora Indah", "Consumer & Retail"),
    ("KLBF", "Kalbe Farma", "Consumer & Retail"),
    ("SIDO", "Industri Jamu & Farmasi Sido Muncul", "Consumer & Retail"),
    ("AMRT", "Sumber Alfaria Trijaya", "Consumer & Retail"),
    ("MAPI", "Mitra Adiperkasa", "Consumer & Retail"),
    ("MAPA", "Map Aktif Adiperkasa", "Consumer & Retail"),
    ("ACES", "Aspirasi Hidup Indonesia", "Consumer & Retail"),
    ("ERAA", "Erajaya Swasembada", "Consumer & Retail"),
    ("CPIN", "Charoen Pokphand Indonesia", "Consumer & Retail"),
    ("JPFA", "Japfa Comfeed Indonesia", "Consumer & Retail"),
    ("HMSP", "HM Sampoerna", "Consumer & Retail"),
    ("GGRM", "Gudang Garam", "Consumer & Retail"),
    ("ULTJ", "Ultrajaya Milk Industry", "Consumer & Retail"),
    ("KAEF", "Kimia Farma", "Consumer & Retail"),
    ("HEAL", "Medikaloka Hermina", "Consumer & Retail"),
    ("MIKA", "Mitra Keluarga Karyasehat", "Consumer & Retail"),
    ("RALS", "Ramayana Lestari Sentosa", "Consumer & Retail"),
    # --- Energy ---
    ("ADRO", "Adaro Energy Indonesia", "Energy"),
    ("PGAS", "Perusahaan Gas Negara", "Energy"),
    ("PTBA", "Bukit Asam", "Energy"),
    ("ITMG", "Indo Tambangraya Megah", "Energy"),
    ("MEDC", "Medco Energi Internasional", "Energy"),
    ("AKRA", "AKR Corporindo", "Energy"),
    ("HRUM", "Harum Energy", "Energy"),
    ("INDY", "Indika Energy", "Energy"),
    ("ELSA", "Elnusa", "Energy"),
    # --- Metals & Mining ---
    ("ANTM", "Aneka Tambang", "Metals & Mining"),
    ("MDKA", "Merdeka Copper Gold", "Metals & Mining"),
    ("INCO", "Vale Indonesia", "Metals & Mining"),
    ("TINS", "Timah", "Metals & Mining"),
    ("NCKL", "Trimegah Bangun Persada", "Metals & Mining"),
    ("BRMS", "Bumi Resources Minerals", "Metals & Mining"),
    ("MBMA", "Merdeka Battery Materials", "Metals & Mining"),
    ("PSAB", "J Resources Asia Pasifik", "Metals & Mining"),
    ("HRTA", "Hartadinata Abadi", "Metals & Mining"),
    # --- Property & Construction ---
    ("BSDE", "Bumi Serpong Damai", "Property & Construction"),
    ("CTRA", "Ciputra Development", "Property & Construction"),
    ("PWON", "Pakuwon Jati", "Property & Construction"),
    ("SMRA", "Summarecon Agung", "Property & Construction"),
    ("PTPP", "PP (Persero)", "Property & Construction"),
    ("WIKA", "Wijaya Karya", "Property & Construction"),
    ("ADHI", "Adhi Karya", "Property & Construction"),
    # --- Industrials & Auto ---
    ("ASII", "Astra International", "Industrials & Auto"),
    ("UNTR", "United Tractors", "Industrials & Auto"),
    ("AUTO", "Astra Otoparts", "Industrials & Auto"),
    ("GJTL", "Gajah Tunggal", "Industrials & Auto"),
    # --- Basic Materials ---
    ("SMGR", "Semen Indonesia", "Basic Materials"),
    ("INTP", "Indocement Tunggal Prakarsa", "Basic Materials"),
    ("BRPT", "Barito Pacific", "Basic Materials"),
    ("TPIA", "Chandra Asri Pacific", "Basic Materials"),
    ("TKIM", "Pabrik Kertas Tjiwi Kimia", "Basic Materials"),
    ("INKP", "Indah Kiat Pulp & Paper", "Basic Materials"),
    ("ESSA", "ESSA Industries Indonesia", "Basic Materials"),
    # --- Infrastructure & Agri ---
    ("JSMR", "Jasa Marga", "Infrastructure & Agri"),
    ("AALI", "Astra Agro Lestari", "Infrastructure & Agri"),
    ("LSIP", "PP London Sumatra Indonesia", "Infrastructure & Agri"),
    ("TAPG", "Triputra Agro Persada", "Infrastructure & Agri"),
]
