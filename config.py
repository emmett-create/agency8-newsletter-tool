"""
Agency 8 Newsletter Tool — configuration.

To add a new client later, copy one block and fill in the four values.
Find a client's Archive workspace UUID by running:  python list_workspaces.py
"""

# Path to the Google service-account credentials (reused from the influencer tool)
GOOGLE_CREDENTIALS = "/Users/emmett/agency8-influencer-tool/google-credentials.json"

# How many top-performing posts to include in the newsletter draft
TOP_POSTS = 10   # how many top-UGC candidates to offer in the checklist

# Archive GraphQL endpoint
ARCHIVE_API_URL = "https://app.archive.com/api/v2"

# Model used to auto-draft the narrative copy (cost is pennies per draft)
DRAFT_MODEL = "claude-sonnet-4-6"


# For most clients we only need: display_name, archive_workspace, report_sheet_key.
# Outreach + gift tabs/columns are read automatically from the client's Reporting-tab
# formulas. archive_workspace = None means the client has no Archive (UGC/EMV will be 0).
CLIENTS = {
    "snif": {
        "display_name": "Snif",
        "archive_workspace": "8b4a8873-ce7e-4335-8c59-469e09449727",
        "report_sheet_key": "1-Y5vwy3QlfjZMKbmT7sX7m4HH2Ji4By6ZNkk7t5oiEk",
        # Snif's gifts live in a separate spreadsheet (matched by tab name):
        "giftapp_sheet_key": "1bSv7ISY0mRoiD8Gjf0o8CHrngIiY6RlLy1ChEzgZ9UI",
        "extra_gift_tabs": ["Only Sunshine Bundle"],
        # legacy outreach fallback if the Reporting formula isn't found:
        "master_list_tab": "Master List",
        "outreach_header": "Outreach Date",
    },
    "borntostandout": {"display_name": "BORNTOSTANDOUT",    "archive_workspace": "abf96c32-02b6-450a-85e9-39776d3199d0", "report_sheet_key": "1nsRCoRK9hdbH50rMD9zqp-GGwTpPyEAFWT69_pjVEbg"},
    "brodo":          {"display_name": "Brodo",             "archive_workspace": "2ce9fdc1-9eae-4c1d-b08f-f8345599f943", "report_sheet_key": "13PXK5rMfw2S53AZLU57MhwEfv1TWwQS0LYIE7xZHOx0"},
    "counter":        {"display_name": "Counter",           "archive_workspace": "bc2a64b7-3ba4-4b98-b476-0e6cd4c0cc51", "report_sheet_key": "1gVSv9Nz4Aucnd_8kd8YkW0AsiIEHpjtYgMRp7R3yOqY"},
    "evolvetogether": {"display_name": "EvolveTogether",    "archive_workspace": "c8493a78-3eb0-4bad-9567-70dc2dc76e98", "report_sheet_key": "19EZE0wC_8SdK_ntNbjHz63Zdp4ml9Xf7BYJHtv7Fz9Q"},
    "feals":          {"display_name": "Feals",             "archive_workspace": "47737d8b-8e42-41fe-b898-5dd09c45b1be", "report_sheet_key": "1x7OyNUkQS8lWvz-jRMlCC99fvROX-B7tDeuGG5PiwvM"},
    "harperwilde":    {"display_name": "Harper Wilde",      "archive_workspace": "9294416a-1698-4736-81b9-f8a38d170b8f", "report_sheet_key": "1Yyc85gXz45xoILd_EKprK87d2mpvCGx5wguSpt-Bs-M"},
    "ilia":           {"display_name": "Ilia",              "archive_workspace": "62abe75c-b250-4ad5-98d3-a55ba9e7b8da", "report_sheet_key": "1xkOWiPIWnIyho4rhPJze_OuBFQSZS7XUAqR1XAM0jrg"},
    # Reconciled against Archive's actual current workspace list 2026-09-25 —
    # this one and the 5 below it (lenox, nette, todaytix, emmarelief,
    # momofuku) all had an archive_workspace UUID that no longer exists in
    # Archive at all (not renamed to something recognizable either — just
    # gone from the 37 workspaces the shared token can currently see).
    # Previously this was a hard crash generating that client's newsletter
    # (archive_query raises SystemExit on any Archive API error) — set to
    # None instead, the documented fallback ("no Archive" = UGC/EMV show 0),
    # so it degrades gracefully instead of breaking. Someone needs to find
    # each client's actual current Archive workspace ID (Archive-side
    # question — did the workspace get renamed/recreated, or did the client
    # relationship end?) and put the real UUID back here.
    "kalshi":         {"display_name": "Kalshi",            "archive_workspace": None, "report_sheet_key": "1-Rkb-r9wlLQcCuPPaimDSSNvFJc0U3ZqkQ7pm7BDbb8"},
    "lenox":          {"display_name": "Lenox and Sixteenth","archive_workspace": None, "report_sheet_key": "1mbK7-TgwBZ8jq46MxTw9wnN985h7pGr-ustMV9AiXlM"},
    "madegood":       {"display_name": "MadeGood",          "archive_workspace": "0cec8ea5-c3b3-4bb1-8083-eaab65719f8e", "report_sheet_key": "1HoHwoMgV1iGUBO6M3gD91DbwiK51_5TQKNxYNw7FZrs"},
    "magicmolecule":  {"display_name": "Magic Molecule",    "archive_workspace": "7487544d-2d3b-4f60-bce1-2833db999329", "report_sheet_key": "1-hl6G1UYmovAkQLUY6toCaYabvG6Wd3uEWuVgIyNBfY"},
    "nette":          {"display_name": "Nette",             "archive_workspace": None, "report_sheet_key": "1dq07ZScfGpzQ2FwK292keRRgKXhetyQyzrt22o3Hd3k"},
    "pattern":        {"display_name": "Pattern",           "archive_workspace": "5596db9f-c6d0-48e9-ad46-e64c1aa0bd00", "report_sheet_key": "12QE7GRqXv_LZS7VjaD-jgCgzhMHATrMMVY8sH5ptSvk"},
    "roz":            {"display_name": "Roz",               "archive_workspace": "b27273a9-3153-46d6-8f5a-2cac4f6cf144", "report_sheet_key": "1e2bZ925S7g13oqNxAkE1LMphBoXJRSZ8elPMKPGVh7M"},
    "sys":            {"display_name": "SYS",               "archive_workspace": "c522e827-edc6-4314-8737-919b19829e0b", "report_sheet_key": "1T_PKGEkVaZoazmGotIXqcsI5FcPzKp7J43x87tw7Xck"},
    "timebeam":       {"display_name": "Timebeam",          "archive_workspace": "66d4666f-1218-40d8-9c92-ca8102fa5105", "report_sheet_key": "1kfSRwoUOQSyblpYvdlSiwO_XUX7F2tL9omdcmT9IBzY"},
    "todaytix":       {"display_name": "TodayTix",          "archive_workspace": None, "report_sheet_key": "1en88S03oxxDk9fe37TfIs3Acmcj3j0vetE4NyWP2EHA"},
    "squigs":         {"display_name": "Squigs",            "archive_workspace": "3e1baa2d-a1e3-46bd-a42d-2788d6eef7ef", "report_sheet_key": "1uuKOSei2nHd1KD6tDAyGDKIwvV2guhUdcolmIHP2mbw"},
    "tushy":          {"display_name": "Tushy",             "archive_workspace": "d0de51ce-b5f3-45ed-91cf-df7c04c424f4", "report_sheet_key": "15K-yi3aKwNd8YChBEEgIXAE89_30FR2mILLRcg_fEjE"},
    # Merit's gifts live in a separate "Merit Zapier Orders" spreadsheet ('Gift Application' tab):
    "merit":          {"display_name": "Merit",             "archive_workspace": "b40fdbe0-4b5d-4f74-9cbb-898e62a87f9b", "report_sheet_key": "1rs53MIeQW6er-xSCZeYtWQRSaG1-eBOd5ugJSJp9JT0", "giftapp_sheet_key": "1mh5kmtn7k0QrgNcmnb42AhVT2PcP-RDxpeB9RPd9DSQ"},
    # These 3 work once shared (Viewer) with the service account:
    "emmarelief":     {"display_name": "Emma Relief",       "archive_workspace": None, "report_sheet_key": "1tIs_TonI25q20QEB9perUtIAmgepb4Jd0OY4q3x-EdU"},
    "fur":            {"display_name": "Fur",               "archive_workspace": "1bfb1db8-dbcd-460a-bb81-d44b31b73d92", "report_sheet_key": "1aYKRBpUFy2rZ7vpAmayfA_AnmW9c4tGKECFF-G1Kd6w"},
    "maev":           {"display_name": "Maev",              "archive_workspace": "a676018b-8d07-44b2-a3d4-8afd0008b67b", "report_sheet_key": "1QSsL_AK8vaJsGhbgC1kXDUD0eOFRtAR-HuJJoRRNlQQ"},
    "momofuku":       {"display_name": "Momofuku",          "archive_workspace": None, "archive_token": "wbE5bHi7yvDUmdTdo3b2niSG7yZ6GLeh", "report_sheet_key": "1Kk5ZgKu1RoHrLN0KcSai34RDlI0VmzxtgGKChiDOlv4"},

    # Added 2026-09-25 — found in Archive's current 37 workspaces but not yet
    # here. Google Sheet IDs cross-checked against agency8-creator-add's
    # clients.js (same brand, same spreadsheet already in use elsewhere).
    "drsquatch":      {"display_name": "Dr. Squatch",       "archive_workspace": "0206b3cb-402d-4708-ab50-d54a97d627f8", "report_sheet_key": "1hmz1j7FDgkkmBx7qklTIkeNhZ64bFxIzeLyZ4BJAMu4"},
    "clarev":         {"display_name": "Clare V.",          "archive_workspace": "92c09804-0593-4ea8-adc7-42fd99bcabcc", "report_sheet_key": "12t1s81q3vOy_yFdIM-169dKXo_jL_HRr4rovqIVuBUk"},
    "starshoney":     {"display_name": "Stars + Honey",     "archive_workspace": "b5d1cdfb-9192-4c98-9818-10f1629b5275", "report_sheet_key": "1nZUCDXuNPmy_s2H9KisgJPA9gZ_OQsMtY_5q0rsKDRE"},
    "personalday":    {"display_name": "Personal Day",      "archive_workspace": "f6ab9c8a-d3b7-4db0-beb9-97b32734936a", "report_sheet_key": "1luLrAJtMGe0oCRmc-aqmyvF24Osx5gdDCodNDxP8fRo"},
    "gimmeseaweed":   {"display_name": "Gimme Seaweed",     "archive_workspace": "849893d6-59e1-4cc8-8df8-388c0c031665", "report_sheet_key": "1Gp2wcJSBa5YOZ51nd-FuFg-Dy5otJDJUb3bNQW8ELPw"},
    "ubeauty":        {"display_name": "U Beauty",          "archive_workspace": "ad940c47-7520-4e84-8975-efb708f24424", "report_sheet_key": "1Clh5lceTRC0bFvUD-o8WPOixanCc6nWxM0xX-HqOzv4"},
    "tiltbeauty":     {"display_name": "Tilt Beauty",       "archive_workspace": "0099a42f-cda1-47cf-b22d-49580a985a1f", "report_sheet_key": "1PyowbTWyAZ_k86bGBtexotoExcqWmUQgYJloTSUZBC0"},
    "raazitea":       {"display_name": "Raazi Tea",         "archive_workspace": "1f1d2712-cc3f-41fc-922a-7172a18aed53", "report_sheet_key": "1DcybNwr-F6uJMa0xfo29cMBJPNa7-lkMl8YFMP0Sbg0"},
    "realeactives":   {"display_name": "Reale Actives",     "archive_workspace": "da2f4fae-ccd6-46ef-b016-3bdba01d4792", "report_sheet_key": "1dmOV65MU9SM-Otq1lNgk1koIVsk-3jDQfmLGcVN1Hhc"},
    "tein":           {"display_name": "Tein",              "archive_workspace": "25196eb3-5dcf-47d1-b83f-56a4ae011391", "report_sheet_key": "1Enujzezf-kIKSgF9Xkded96yz5txr49gGk7ooMji8t0"},
    "tac":            {"display_name": "The Absorption Company", "archive_workspace": "77b77ba7-db31-44d2-819d-cc710cb89289", "report_sheet_key": "1xcVQ2SvbyenVLZnuQcJQBzDGD4xWDpM1kwhPWXw2s7w"},
    "magna":          {"display_name": "Magna",             "archive_workspace": "1a9f4270-c1c5-4dde-bcfa-3040589e9184", "report_sheet_key": "1Id9_j-5yVGMBQXlaQvNcIGEA1PRRMw1V_E4eq8RDYIc", "master_list_tab": "Organic Gifting Master List"},
    # Stardust's spreadsheet has 4 different master-list tabs (Working/
    # Horoscope/Sorority/Tarot Mailer) — defaults to the main "Working" one.
    "stardust":       {"display_name": "Stardust",          "archive_workspace": "d7413c10-4ac9-4a69-b7a6-0e0babaad8a1", "report_sheet_key": "1Qz6ynzsQX-hf_0s5qxoq_jsztri1uhA25V-qO-c202k", "master_list_tab": "Master List (working)"},
    # Sheet IDs from Emmett 2026-09-25 — both verified readable, plain
    # "Master List" tab, no override needed (same shape as every other client).
    "moonjuice":      {"display_name": "Moon Juice",        "archive_workspace": "dd891362-725f-4b08-b77b-d5a5b9801e4c", "report_sheet_key": "1UK--bNXSyWdtq-jlWAw8IikinOGof-stQ9N17RI-I40"},
    "fenty":          {"display_name": "Fenty",             "archive_workspace": "fc5899da-04ea-4807-83f4-0687123d4549", "report_sheet_key": "1ttnrS6HKJr_iD6HNKSWi-HJUKuVD2554rXi9R1W0zos"},
}

# Found in Archive's current workspace list (2026-09-25) but with NO known
# Google Sheet — clients.js doesn't have it either, and report_sheet_key
# is required (newsletter.py crashes without one). Not added until a real
# sheet ID is found:
#   Biossance    952bbf02-0d54-4704-b72a-f1c6e09fceb1
# "Agency Eight" (c51ac2eb-5bd2-49bd-b8ff-0840041b04c4) is the agency's own
# internal workspace, not a client — deliberately excluded.
