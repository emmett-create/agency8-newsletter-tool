"""
Agency 8 Newsletter Tool — configuration.

To add a new client later, copy one block and fill in the four values.
Find a client's Archive workspace UUID by running:  python list_workspaces.py
"""

# Path to the Google service-account credentials (reused from the influencer tool)
GOOGLE_CREDENTIALS = "/Users/emmett/agency8-influencer-tool/google-credentials.json"

# How many top-performing posts to include in the newsletter draft
TOP_POSTS = 5

# Archive GraphQL endpoint
ARCHIVE_API_URL = "https://app.archive.com/api/v2"

# Model used to auto-draft the narrative copy (cost is pennies per draft)
DRAFT_MODEL = "claude-sonnet-4-6"


CLIENTS = {
    # key (what you type / pick) : settings
    "snif": {
        "display_name": "Snif",
        "archive_workspace": "8b4a8873-ce7e-4335-8c59-469e09449727",
        # Spreadsheet that holds the Master List (outreach lives here)
        "report_sheet_key": "1-Y5vwy3QlfjZMKbmT7sX7m4HH2Ji4By6ZNkk7t5oiEk",
        "master_list_tab": "Master List",
        "outreach_header": "Outreach Date",   # found by name, not column letter
        # Spreadsheet that holds the gift applications (may be the same or separate)
        "giftapp_sheet_key": "1bSv7ISY0mRoiD8Gjf0o8CHrngIiY6RlLy1ChEzgZ9UI",
        "giftapp_tab_prefix": "Snif Gift Application",  # tabs starting with this count
    },
}
